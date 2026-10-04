"""Cron-friendly CLI: plan, submit, collect, status, check, analyze.

Exit 0 on success, 2 on a guarded refusal."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.adapters.lock import LockHeld, exclusive_lock
from llm_panel.application.baseline_comparison import (
    render_agreement_csv,
    render_markdown,
    render_policy_csv,
    run_baseline_comparison,
)
from llm_panel.application.build_jobs import build_study_jobs
from llm_panel.application.collect import collect
from llm_panel.application.rank_stability import (
    render_aggregation_csv,
    render_noise_csv,
    render_shifts_csv,
    render_tau_csv,
    run_rank_stability,
)
from llm_panel.application.rank_stability import (
    render_markdown as render_rank_markdown,
)
from llm_panel.application.smoketest import ratings_from_store
from llm_panel.application.spend import SpendCeilingError
from llm_panel.application.status import get_status
from llm_panel.application.submit import (
    ClientFactory,
    ConfirmationRequired,
    ModelIdDrift,
    ProviderNotApproved,
    make_plan,
    plan_from_build,
    submit,
)
from llm_panel.bootstrap.config import ExternalSpendError, external_spend, load_config
from llm_panel.bootstrap.design_loader import is_oat_design, load_design, load_oat_design
from llm_panel.bootstrap.env import load_dotenv
from llm_panel.bootstrap.inputs_loader import load_inputs, load_study_materials
from llm_panel.bootstrap.persona_files import read_records, write_panel
from llm_panel.bootstrap.providers import (
    ProviderBuilder,
    ProviderContext,
    default_registry,
    make_client_factory,
)
from llm_panel.bootstrap.published_loader import load_published
from llm_panel.bootstrap.smoketest_loader import load_expectations
from llm_panel.domain.analysis_rank import DEFAULT_RESAMPLES
from llm_panel.domain.design import to_run_specs
from llm_panel.domain.oat_design import expand_cells, paired_persona_ids, run_order
from llm_panel.domain.personas import (
    build_igm_panel,
    build_named_panel,
    build_synthetic_panel,
)
from llm_panel.domain.pricing import HARD_CEILING_USD, MissingPriceError, estimate_job_cost
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


def _positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
    return value


MAX_JOBS_HELP = (
    "only the first N jobs still to submit, in run order (finished and in-flight jobs are "
    "skipped first, so rerunning takes the next N); cost and the ceiling check use only these"
)


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
    plan.add_argument("--max-jobs", type=_positive_int, metavar="N", help=MAX_JOBS_HELP)

    sub_submit = sub.add_parser("submit", help="submit jobs as batches (spends money)")
    sub_submit.add_argument("--design", required=True)
    sub_submit.add_argument("--provider")
    sub_submit.add_argument("--confirm", action="store_true", help="required to submit")
    sub_submit.add_argument("--max-jobs", type=_positive_int, metavar="N", help=MAX_JOBS_HELP)

    sub.add_parser("collect", help="fetch finished batches, validate, store, retry once")
    sub.add_parser("status", help="show spend versus ceiling and row counts")
    build = sub.add_parser("build-personas", help="build a persona source file with provenance")
    kinds = build.add_subparsers(dest="kind", required=True)
    synth = kinds.add_parser("synthetic", help="our stand-in panel for the unpublished survey")
    synth.add_argument("--n", type=int, default=51)
    synth.add_argument("--seed", type=int, required=True)
    synth.add_argument("--source", default="reconstructed")
    igm = kinds.add_parser("igm", help="personas from anonymous expert-panel records (CSV)")
    igm.add_argument("--records", required=True)
    igm.add_argument("--source", required=True, help="e.g. igm_us or igm_europe")
    igm.add_argument("--origin", required=True)
    igm.add_argument("--retrieved", required=True)
    named = kinds.add_parser("named", help="the paper's named economists (Table 7 roster CSV)")
    named.add_argument("--roster", required=True)
    named.add_argument("--source", default="named")
    named.add_argument("--retrieved", required=True)
    for p in (synth, igm, named):
        p.add_argument("--out", required=True, help="inputs directory")
    check = sub.add_parser("check", help="check smoketest expectations against the store")
    check.add_argument("--expectations", required=True)
    analyze = sub.add_parser("analyze", help="descriptive analyses read from the raw store")
    analyses = analyze.add_subparsers(dest="analysis", required=True)
    baseline = analyses.add_parser("baseline", help="baseline B versus the published Table 4")
    baseline.add_argument(
        "--published",
        default="analysis/published/paper_table4.csv",
        help="transcribed published scores (relative to the config's folder)",
    )
    baseline.add_argument("--out", default="analysis/baseline", help="report directory")
    ranks = analyses.add_parser("ranks", help="rank stability of every cell versus B")
    ranks.add_argument("--out", default="analysis/ranks", help="report directory")
    ranks.add_argument(
        "--resamples",
        type=int,
        default=DEFAULT_RESAMPLES,
        help="persona bootstrap resamples (placeholder default; prereg s12 item 6 open)",
    )
    ranks.add_argument("--seed", type=int, default=0, help="persona bootstrap seed")
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


def _build_personas(args) -> int:
    try:
        if args.kind == "synthetic":
            panel = build_synthetic_panel(args.n, args.seed, args.source)
        elif args.kind == "named":
            records, digest = read_records(args.roster)
            panel = build_named_panel(
                records, source=args.source, retrieved=args.retrieved, input_sha256=digest
            )
        else:
            records, digest = read_records(args.records)
            panel = build_igm_panel(
                records, source=args.source, origin=args.origin, retrieved=args.retrieved,
                input_sha256=digest,
            )  # fmt: skip
    except ValueError as exc:  # e.g. identifying fields, no records, bad roster
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    try:
        path = write_panel(args.out, panel)
    except FileExistsError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    print(f"wrote {len(panel.personas)} personas ({args.source}) to {path}")
    return 0


def _store_label(raw_store: Path, config_dir: Path) -> str:
    try:
        return str(raw_store.resolve().relative_to(config_dir.resolve()))
    except ValueError:
        return str(raw_store)


def _analyze_baseline(args, config_dir: Path, raw_store: Path, store) -> int:
    published = load_published(config_dir / args.published)
    result = run_baseline_comparison(store, published)
    out = config_dir / args.out
    out.mkdir(parents=True, exist_ok=True)
    label = _store_label(raw_store, config_dir)
    (out / "baseline_comparison.md").write_text(render_markdown(result, label), encoding="utf-8")
    (out / "baseline_agreement.csv").write_text(render_agreement_csv(result), encoding="utf-8")
    (out / "baseline_policy_scores.csv").write_text(render_policy_csv(result), encoding="utf-8")
    print(f"wrote baseline_comparison.md and two CSVs to {out} "
          f"({result.counts.ok_jobs} cell B jobs from {label})")  # fmt: skip
    return 0


def _analyze_ranks(args, config_dir: Path, raw_store: Path, store) -> int:
    report = run_rank_stability(store, resamples=args.resamples, seed=args.seed)
    out = config_dir / args.out
    out.mkdir(parents=True, exist_ok=True)
    label = _store_label(raw_store, config_dir)
    files = {
        "rank_stability.md": render_rank_markdown(report, label),
        "rank_tau.csv": render_tau_csv(report),
        "rank_shifts.csv": render_shifts_csv(report),
        "rank_repeat_noise.csv": render_noise_csv(report),
        "rank_aggregation_agreement.csv": render_aggregation_csv(report),
    }
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    print(f"wrote rank_stability.md and four CSVs to {out} "
          f"({len(report.cell_order)} cells from {label})")  # fmt: skip
    return 0


def _run(args, config, store, ledger, factory, settings, now) -> int:
    if args.command == "build-personas":
        return _build_personas(args)
    if args.command == "analyze":  # read-only; needs no ledger or spend state
        analyze = _analyze_ranks if args.analysis == "ranks" else _analyze_baseline
        return analyze(args, Path(args.config).parent, config.raw_store, store)
    external = external_spend(config)
    if args.command in ("plan", "submit"):
        if is_oat_design(args.design):
            plan = _oat_plan(args, config, store, ledger, settings, external)
        else:
            specs = to_run_specs(load_design(args.design))
            inputs = load_inputs(config.inputs_dir)
            plan = make_plan(
                specs, inputs, store, ledger, settings, args.provider, external, args.max_jobs
            )
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


def _oat_plan(args, config, store, ledger, settings, external):
    """One-at-a-time design (prereg s5): cells -> jobs in the recorded run order."""
    design = load_oat_design(args.design)
    cells = expand_cells(design)
    materials = load_study_materials(config)
    paired_persona_ids(cells, materials.panels, design.n_personas)
    build = build_study_jobs(
        cells, run_order(cells, design.order_seed), materials, store,
        cost=lambda job: estimate_job_cost(job, settings),
    )  # fmt: skip
    return plan_from_build(build, store, ledger, settings, args.provider, external, args.max_jobs)


def _print_plan(plan, ceiling: float) -> None:
    b = plan.build
    if b.per_cell:
        print(f"design: one_at_a_time ({len(b.per_cell)} cells)")
        for cid, s in b.per_cell.items():
            print(
                f"  {cid}: {s.count.calls} calls ({s.count.calls // s.repeats} per repeat x "
                f"{s.repeats}), {s.count.ratings} ratings, estimated ${s.estimated_cost:.4f}"
            )
    print(f"configurations: {len(b.per_spec)}")
    print(f"calls (all configs, before dedupe): {sum(c.calls for c in b.per_spec)}")
    print(f"ratings (all configs, before dedupe): {sum(c.ratings for c in b.per_spec)}")
    print(
        f"distinct jobs: {b.total}; already finished: {b.skipped}; duplicates across configs: "
        f"{b.duplicates}; in flight: {plan.in_flight}"
    )
    print(f"jobs to submit: {len(plan.jobs)}")
    if plan.max_jobs is not None:
        print(
            f"selected by --max-jobs {plan.max_jobs}: first {len(plan.jobs)} of {plan.eligible} "
            "jobs in run order"
        )
        if b.per_cell:
            print(f"  cells: {_tally(j.cell_id for j in plan.jobs)}")
        print(f"  personas: {_tally(j.persona_id for j in plan.jobs)}")
        print(f"  policies: {_tally(p for j in plan.jobs for p in j.policy_ids)}")
    for provider, cost in sorted(plan.cost_by_provider.items()):
        n = sum(1 for j in plan.jobs if j.provider == provider)
        print(f"  {provider}: {n} jobs, estimated ${cost:.4f}")
    print(f"estimated total: ${plan.estimated_cost:.4f}")
    print(
        f"spend so far: ${plan.spend.actual:.4f} actual + "
        f"${plan.spend.outstanding:.4f} outstanding; ceiling ${ceiling:.2f}"
    )


def _tally(values) -> str:
    counts = Counter(values)
    return f"{len(counts)} distinct ({', '.join(f'{k} x{n}' for k, n in counts.items())})"


if __name__ == "__main__":
    raise SystemExit(main())
