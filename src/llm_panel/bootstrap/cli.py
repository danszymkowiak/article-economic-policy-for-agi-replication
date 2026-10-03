"""Cron-friendly CLI: plan, submit, collect, status. Exit 0 on success, 2 on a guarded refusal."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.adapters.lock import LockHeld, exclusive_lock
from llm_panel.application.collect import collect
from llm_panel.application.smoketest import ratings_from_store
from llm_panel.application.spend import SpendCeilingError
from llm_panel.application.status import get_status
from llm_panel.application.submit import (
    ClientFactory,
    ConfirmationRequired,
    ModelIdDrift,
    ProviderNotApproved,
    make_plan,
    submit,
)
from llm_panel.bootstrap.config import ExternalSpendError, external_spend, load_config
from llm_panel.bootstrap.design_loader import load_design
from llm_panel.bootstrap.env import load_dotenv
from llm_panel.bootstrap.inputs_loader import load_inputs
from llm_panel.bootstrap.providers import (
    ProviderBuilder,
    ProviderContext,
    default_registry,
    make_client_factory,
)
from llm_panel.bootstrap.smoketest_loader import load_expectations
from llm_panel.domain.design import to_run_specs
from llm_panel.domain.pricing import HARD_CEILING_USD, MissingPriceError
from llm_panel.domain.smoketest import evaluate
from llm_panel.ports import ProviderConfigError

CHECK_FAILED = 1
REFUSED = 2


def _now() -> str:
    return datetime.now(UTC).isoformat()


def default_client_factory(
    config_dir: Path,
    *,
    est_output_tokens_per_policy: int = 100,
    environ=None,
    transports: Mapping[str, Callable] | None = None,
    registry: Mapping[str, ProviderBuilder] | None = None,
) -> ClientFactory:
    context = ProviderContext(
        config_dir=config_dir,
        environ=os.environ if environ is None else environ,
        est_output_tokens_per_policy=est_output_tokens_per_policy,
        transports=transports or {},
    )
    return make_client_factory(context, registry or default_registry())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-panel")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="count jobs and estimate cost; never submits")
    plan.add_argument("--design", required=True)
    plan.add_argument(
        "--dry-run", action="store_true", help="accepted for clarity; plan is read-only"
    )
    plan.add_argument("--provider")

    sub_submit = sub.add_parser("submit", help="submit jobs as batches (spends money)")
    sub_submit.add_argument("--design", required=True)
    sub_submit.add_argument("--provider")
    sub_submit.add_argument("--confirm", action="store_true", help="required to submit")

    sub.add_parser("collect", help="fetch finished batches, validate, store, retry once")
    sub.add_parser("status", help="show spend versus ceiling and row counts")
    check = sub.add_parser("check", help="check smoketest expectations against the store")
    check.add_argument("--expectations", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    client_factory: ClientFactory | None = None,
    now: Callable[[], str] = _now,
) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    load_dotenv(config_path.parent / ".env", os.environ)
    config = load_config(config_path)
    store = JsonlResultStore(config.raw_store)
    ledger = JsonlBatchLedger(config.ledger)
    settings = config.spend
    factory = client_factory or default_client_factory(
        config_path.parent, est_output_tokens_per_policy=settings.est_output_tokens_per_policy
    )

    # submit and collect hold an exclusive lock so overlapping cron runs cannot double-spend
    lock = (
        exclusive_lock(config.ledger.with_suffix(".lock"))
        if args.command in ("submit", "collect")
        else contextlib.nullcontext()
    )
    try:
        with lock:
            return _run(args, config, store, ledger, factory, settings, now)
    except (
        ConfirmationRequired,
        SpendCeilingError,
        ProviderNotApproved,
        ModelIdDrift,
        MissingPriceError,
        ExternalSpendError,
        LockHeld,
        ProviderConfigError,
    ) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED


def _run(args, config, store, ledger, factory, settings, now) -> int:
    external = external_spend(config)
    if args.command in ("plan", "submit"):
        specs = to_run_specs(load_design(args.design))
        inputs = load_inputs(config.inputs_dir)
        plan = make_plan(specs, inputs, store, ledger, settings, args.provider, external)
        if args.command == "plan":
            _print_plan(plan, settings.max_spend_usd)
            return 0
        batch_ids = submit(
            plan,
            ledger,
            factory,
            settings,
            config.approved_providers,
            now,
            confirm=args.confirm,
        )
        print(f"submitted {len(plan.jobs)} jobs in {len(batch_ids)} batch(es): {batch_ids}")
        return 0
    if args.command == "collect":
        r = collect(store, ledger, factory, settings, now, external)
        print(
            f"collected {r.batches_collected} batch(es), {r.batches_pending} still pending; "
            f"ok={r.ok} invalid={r.invalid} failed={r.failed} retried={r.retried} "
            f"deferred={r.deferred}"
        )
        return 0
    if args.command == "check":
        ratings, ok, total = ratings_from_store(store)
        checks = evaluate(load_expectations(args.expectations), ratings, ok, total)
        for c in checks:
            print(f"{'PASS' if c.passed else 'FAIL'}  {c.description}: {c.detail}")
        return 0 if all(c.passed for c in checks) else CHECK_FAILED
    s = get_status(store, ledger, settings, external)
    print(
        f"spend: actual ${s.spend.actual:.4f} + outstanding ${s.spend.outstanding:.4f} "
        f"of ceiling ${s.spend.ceiling:.2f}"
    )
    if config.counts_spend_from:
        print(f"other ledgers ${external:.4f} (count toward the global ${HARD_CEILING_USD:g} cap)")
    print(f"rows: {s.rows_by_status or 'none'}; pending: {s.pending_batches} batch(es), "
          f"{s.pending_jobs} job(s)")  # fmt: skip
    m = s.model_ids
    if m.has_issues:
        print(f"WARNING: model id drift: {m.describe()}")
    else:
        print(f"model ids: ok ({m.checked} rows reported one, {m.unreported} unreported)")
    if s.unreconciled_intents:
        print(f"WARNING: {s.unreconciled_intents} submission(s) have no recorded batch id "
              "(crash mid-submit?); counted as outstanding until reconciled")  # fmt: skip
    return 0


def _print_plan(plan, ceiling: float) -> None:
    b = plan.build
    print(f"configurations: {len(b.per_spec)}")
    print(f"calls (all configs, before dedupe): {sum(c.calls for c in b.per_spec)}")
    print(f"ratings (all configs, before dedupe): {sum(c.ratings for c in b.per_spec)}")
    print(
        f"distinct jobs: {b.total}; already finished: {b.skipped}; duplicates across configs: "
        f"{b.duplicates}; in flight: {plan.in_flight}"
    )
    print(f"jobs to submit: {len(plan.jobs)}")
    for provider, cost in sorted(plan.cost_by_provider.items()):
        n = sum(1 for j in plan.jobs if j.provider == provider)
        print(f"  {provider}: {n} jobs, estimated ${cost:.4f}")
    print(f"estimated total: ${plan.estimated_cost:.4f}")
    print(
        f"spend so far: ${plan.spend.actual:.4f} actual + "
        f"${plan.spend.outstanding:.4f} outstanding; ceiling ${ceiling:.2f}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
