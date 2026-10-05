"""EXPLORATORY reversed-scale probe CLI (bootstrap):
`python -m scale_probe plan|submit|collect|report`.

Cron-friendly like the adversarial arm: `submit --confirm`, then `collect` until nothing is
pending, then `report`. Exit 0 on success, 2 on a guarded refusal. Refuses to run when the
template does not match its manifest hash.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from adversarial.arm import ArmSettings
from adversarial.cli import load_arm_config
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
from llm_panel.bootstrap.prompt_files import manifest_mismatches
from llm_panel.domain.pricing import MissingPriceError
from llm_panel.domain.study_prompt import check_template
from llm_panel.ports import ProviderConfigError
from scale_probe.probe import plan_probe, probe_state
from scale_probe.report import render_markdown

DEFAULT_CONFIG = "scale_probe/config.scale_probe.yaml"


class ManifestMismatch(RuntimeError):
    """The probe's template differs from the hash recorded in its manifest."""


@dataclass(frozen=True)
class ProbeSettings:
    arm: ArmSettings
    adversarial_store: Path
    template: str


def load_probe_config(path: Path | str) -> tuple[Config, ProbeSettings]:
    path = Path(path)
    config = load_config(path)
    home = path.parent.resolve()
    for name, p in (("raw_store", config.raw_store), ("ledger", config.ledger)):
        if is_study_store(str(p.resolve())) or not p.resolve().is_relative_to(home):
            raise ValueError(
                f"{name} {p} must lie under {home}; the probe never writes results/raw"
            )
    block = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("scale_probe") or {}
    adv_config, arm = load_arm_config(path.parent / block["adversarial_config"])
    if adv_config.raw_store.resolve() == config.raw_store.resolve():
        raise ValueError("the probe needs a store of its own")
    manifest = path.parent / block["manifest"]
    bad = manifest_mismatches(manifest, path.parent.parent)
    if bad:
        raise ManifestMismatch(f"template differs from its manifest {manifest}: {bad}")
    template = (path.parent / block["template"]).read_text(encoding="utf-8")
    check_template("persona_policy", template)
    return config, ProbeSettings(arm, adv_config.raw_store, template)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m scale_probe", description="EXPLORATORY probe")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="status and what submit would send; read-only")
    s = sub.add_parser("submit", help="submit the probe's remaining jobs (spends money)")
    s.add_argument("--confirm", action="store_true", help="required to submit")
    sub.add_parser("collect", help="fetch finished batches, validate, store, retry once")
    r = sub.add_parser("report", help="write report.md")
    r.add_argument("--out", default="scale_probe", help="report directory")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    client_factory: ClientFactory | None = None,
    now: Callable[[], str] = _now,
) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.config)
    for d in (path.parent, path.parent.parent):
        load_dotenv(d / ".env", os.environ)
    try:
        config, probe = load_probe_config(path)
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
            return _run(args, config, probe, store, ledger, factory, now)
    except (
        ConfirmationRequired,
        SpendCeilingError,
        ProviderNotApproved,
        ModelIdDrift,
        MissingPriceError,
        ExternalSpendError,
        LockHeld,
        ProviderConfigError,
        ManifestMismatch,
    ) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED


def _run(args, config, probe, store, ledger, factory, now) -> int:
    external = external_spend(config)
    if args.command == "collect":
        r = collect(store, ledger, factory, config.spend, now, external)
        print(
            f"SCALE PROBE: collected {r.batches_collected} batch(es), {r.batches_pending} still "
            f"pending; ok={r.ok} invalid={r.invalid} failed={r.failed} retried={r.retried} "
            f"deferred={r.deferred}"
        )
        return 0
    if args.command == "submit" and not args.confirm:
        raise ConfirmationRequired("submit needs --confirm")
    materials = load_study_materials(config)
    adv_store = JsonlResultStore(probe.adversarial_store)
    state = probe_state(materials, probe.arm, probe.template, store, adv_store)
    plan = plan_probe(state, store, ledger, config.spend, external)
    if args.command == "report":
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        md = render_markdown(
            state, str(config.raw_store), str(probe.adversarial_store), config.spend.max_spend_usd
        )
        (out / "report.md").write_text(md, encoding="utf-8")
        print(f"SCALE PROBE: wrote report.md to {out} ({state.status})")
        return 0
    if args.command == "plan":
        print(f"SCALE PROBE (exploratory, not pooled); status: {state.status}")
        print(f"jobs to submit: {len(plan.jobs)} of {len(state.jobs)}; in flight {plan.in_flight}; "
              f"estimated ${plan.estimated_cost:.4f}; other ledgers ${external:.4f}")  # fmt: skip
        return 0
    if not plan.jobs:
        print(f"SCALE PROBE: nothing to submit ({state.status})")
        return 0
    batch_ids = submit(
        plan, ledger, factory, config.spend, config.approved_providers, now, confirm=True
    )
    print(
        f"SCALE PROBE: submitted {len(plan.jobs)} jobs in {len(batch_ids)} batch(es): {batch_ids}"
    )
    return 0
