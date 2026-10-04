"""ADVERSARIAL ARM CLI (bootstrap): `python -m adversarial plan|submit|collect|report`.

Cron-friendly like llm-panel: rerun `collect` then `submit --confirm` until the search stops;
each submit sends the candidates the search needs next, as far as the budget allows. Exit 0 on
success, 2 on a guarded refusal.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import yaml

from adversarial.arm import ArmSettings, arm_state, plan_submission
from adversarial.catalogue import CATALOGUE_VERSION
from adversarial.report import render_csv, render_markdown
from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.adapters.lock import LockHeld, exclusive_lock
from llm_panel.application.baseline_comparison import is_study_store
from llm_panel.application.collect import collect
from llm_panel.application.spend import SpendCeilingError
from llm_panel.application.submit import (
    ClientFactory,
    ConfirmationRequired,
    ModelIdDrift,
    ProviderNotApproved,
    submit,
)
from llm_panel.bootstrap.cli import REFUSED, _now, default_client_factory
from llm_panel.bootstrap.config import Config, ExternalSpendError, external_spend, load_config
from llm_panel.bootstrap.env import load_dotenv
from llm_panel.bootstrap.inputs_loader import load_study_materials
from llm_panel.domain.oat_design import Factors, ModelRef
from llm_panel.domain.pricing import MissingPriceError
from llm_panel.ports import ProviderConfigError

DEFAULT_CONFIG = "adversarial/config.adversarial.yaml"


def load_arm_config(path: Path | str) -> tuple[Config, ArmSettings]:
    """The arm's config: a normal llm-panel config (store, ledger, ceiling, prices) plus an
    `adversarial` block. Refuses another catalogue version and any store outside the config's
    own directory (so never results/raw)."""
    path = Path(path)
    config = load_config(path)
    home = path.parent.resolve()
    for name, p in (("raw_store", config.raw_store), ("ledger", config.ledger)):
        if is_study_store(str(p.resolve())) or not p.resolve().is_relative_to(home):
            raise ValueError(
                f"{name} {p} must lie under {home}; the adversarial arm never writes results/raw"
            )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = data.get("adversarial") or {}
    if block.get("catalogue_version") != CATALOGUE_VERSION:
        raise ValueError(
            f"config names catalogue {block.get('catalogue_version')!r}; this code has "
            f"{CATALOGUE_VERSION!r}"
        )
    base = block.get("baseline") or {}
    model = base.get("model") or {}
    temperature = base.get("temperature")
    settings = ArmSettings(
        baseline=Factors(
            model=ModelRef(model.get("provider", ""), model.get("snapshot", "")),
            temperature=None if temperature is None else float(temperature),
            persona_source=base["persona_source"],
            evidence=base["evidence"],
        ),
        search_personas=int(block["search_personas"]),
        panel_seed=int(block["panel_seed"]),
        seed=int(block["seed"]),
        noise_seed=int(block["noise_seed"]),
        primary_composite=str(block["primary_composite"]),
        max_depth=int(block["max_depth"]),
        max_candidates=int(block["max_candidates"]),
    )
    return config, settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m adversarial", description="ADVERSARIAL ARM")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="search state and what submit would send; read-only")
    s = sub.add_parser("submit", help="submit the candidates the search needs next (spends money)")
    s.add_argument("--confirm", action="store_true", help="required to submit")
    sub.add_parser("collect", help="fetch finished batches, validate, store, retry once")
    r = sub.add_parser("report", help="write report.md and candidates.csv")
    r.add_argument("--out", default="adversarial", help="report directory")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    client_factory: ClientFactory | None = None,
    now: Callable[[], str] = _now,
) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.config)
    for d in (path.parent, path.parent.parent):  # the arm's folder, then the project root
        load_dotenv(d / ".env", os.environ)
    try:
        config, settings = load_arm_config(path)
        store, ledger = JsonlResultStore(config.raw_store), JsonlBatchLedger(config.ledger)
        factory = client_factory or default_client_factory(
            path.parent, est_output_tokens_per_policy=config.spend.est_output_tokens_per_policy
        )
        lock = (
            exclusive_lock(config.ledger.with_suffix(".lock"))
            if args.command in ("submit", "collect")
            else contextlib.nullcontext()
        )
        with lock:
            return _run(args, path, config, settings, store, ledger, factory, now)
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


def _run(args, path, config, settings, store, ledger, factory, now) -> int:
    external = external_spend(config)
    if args.command == "collect":
        r = collect(store, ledger, factory, config.spend, now, external)
        print(
            f"ADVERSARIAL ARM: collected {r.batches_collected} batch(es), {r.batches_pending} "
            f"still pending; ok={r.ok} invalid={r.invalid} failed={r.failed} retried={r.retried} "
            f"deferred={r.deferred}"
        )
        return 0
    if args.command == "submit" and not args.confirm:
        raise ConfirmationRequired("submit needs --confirm")
    materials = load_study_materials(config)
    state = arm_state(materials, settings, store)
    sub = plan_submission(state, store, ledger, config.spend, external)
    if args.command == "report":
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        label = str(config.raw_store)
        md = render_markdown(sub, settings, label, config.spend.max_spend_usd)
        (out / "report.md").write_text(md, encoding="utf-8")
        (out / "candidates.csv").write_text(render_csv(state), encoding="utf-8")
        print(f"ADVERSARIAL ARM: wrote report.md and candidates.csv to {out} ({sub.status})")
        return 0
    if args.command == "plan":
        _print_plan(sub)
        return 0
    if not sub.plan.jobs:
        print(f"ADVERSARIAL ARM: nothing to submit ({sub.status})")
        return 0
    batch_ids = submit(
        sub.plan, ledger, factory, config.spend, config.approved_providers, now, confirm=True
    )
    print(
        f"ADVERSARIAL ARM: submitted {len(sub.plan.jobs)} jobs for {len(sub.keys)} candidate(s) "
        f"in {len(batch_ids)} batch(es): {batch_ids}"
    )
    return 0


def _print_plan(sub) -> None:
    st = sub.state
    print(f"ADVERSARIAL ARM (not pooled with the main analysis); status: {sub.status}")
    if st.target:
        print(f"target policy: {st.target}; candidates tried: {len(st.search.tried)}")
    print(f"needed now: {', '.join(st.needed) or 'none'}")
    print(
        f"to submit: {', '.join(sub.keys) or 'none'}; in flight: {', '.join(sub.waiting) or 'none'}"
    )
    if sub.unaffordable:
        print(f"over budget: {', '.join(sub.unaffordable)}")
    print(f"jobs to submit: {len(sub.plan.jobs)}; estimated ${sub.plan.estimated_cost:.4f}")
    s = sub.spend
    print(f"spend: actual ${s.actual:.4f} + outstanding ${s.outstanding:.4f} of ceiling "
          f"${s.ceiling:.2f}; other ledgers ${s.external:.4f}")  # fmt: skip
