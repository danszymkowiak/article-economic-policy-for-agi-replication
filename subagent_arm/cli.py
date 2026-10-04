"""CLAUDE SUBAGENT ARM CLI (bootstrap): `python -m subagent_arm prepare|next|discard|ingest|status`.

The Claude Code session launches the agents: `next` prints the prompts to give them, the session
reports tool-use discards with `discard`, and `ingest` folds the answer files into the arm's own
store. Exit 0 on success, 2 on a guarded refusal.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import yaml

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.baseline_comparison import is_study_store
from llm_panel.bootstrap.cli import REFUSED, _now
from llm_panel.bootstrap.config import Config, load_config
from llm_panel.bootstrap.design_loader import load_oat_design
from llm_panel.bootstrap.inputs_loader import load_study_materials
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.oat_design import Factors
from subagent_arm.arm import Workspace, agent_prompt, build_jobs, ingest, pending, write_tasks

DEFAULT_CONFIG = "subagent_arm/config.subagent.yaml"
HEADER = "CLAUDE SUBAGENT ARM — not pooled with the main analysis"


def load_arm(path: Path | str) -> tuple[Config, Factors, int, tuple[str, ...] | None, Workspace]:
    path = Path(path)
    config = load_config(path)
    home = path.parent.resolve()
    if is_study_store(
        str(config.raw_store.resolve())
    ) or not config.raw_store.resolve().is_relative_to(home):
        raise ValueError(f"raw_store {config.raw_store} must lie under {home}, never results/raw")
    block = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("subagent_arm") or {}
    k_c = int(block.get("k_c", 3))
    if k_c < 1:
        raise ValueError("k_c must be >= 1")
    repeat_policies = tuple(block["repeat_policies"]) if block.get("repeat_policies") else None
    baseline = load_oat_design(home / block["design"]).baseline
    return config, baseline, k_c, repeat_policies, Workspace(home / block.get("work_dir", "work"))


def _jobs(
    config: Config, baseline: Factors, k_c: int, repeat_policies: tuple[str, ...] | None
) -> list[RenderedJob]:
    return build_jobs(load_study_materials(config), baseline, k_c, repeat_policies)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="subagent_arm", description=HEADER)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="write one task file per job")
    nxt = sub.add_parser("next", help="print the next agent prompts as JSON lines")
    nxt.add_argument("--limit", type=int, default=25)
    disc = sub.add_parser(
        "discard", help="mark runs that used tools beyond one Read, one Write and the hand-back"
    )
    disc.add_argument("pairs", nargs="+", help="JOB_ID:ATTEMPT")
    sub.add_parser("ingest", help="fold answer files into the arm's store")
    sub.add_parser("status", help="counts by state")
    args = parser.parse_args(argv)

    try:
        config, baseline, k_c, repeat_policies, ws = load_arm(args.config)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return REFUSED
    store = JsonlResultStore(config.raw_store)

    if args.command == "discard":
        for pair in args.pairs:
            job_id, _, attempt = pair.partition(":")
            ws.discard(job_id, int(attempt))
        print(f"recorded {len(args.pairs)} discards")
        return 0
    jobs = _jobs(config, baseline, k_c, repeat_policies)
    if args.command == "prepare":
        write_tasks(ws, jobs)
        print(f"{HEADER}\nwrote {len(jobs)} task files under {ws.root / 'tasks'} (k_c={k_c})")
    elif args.command == "next":
        write_tasks(ws, jobs)
        for job, attempt in pending(store, jobs)[: args.limit]:
            print(json.dumps({"job_id": job.job_id, "attempt": attempt,
                              "prompt": agent_prompt(ws, job, attempt)}))  # fmt: skip
    elif args.command == "ingest":
        r = ingest(store, ws, jobs, now=_now)
        print(f"ok {r.ok}, invalid (retry pending) {r.invalid}, failed {r.failed}, "
              f"waiting for an answer {r.waiting}")  # fmt: skip
    else:
        counts = Counter(row.status for row in store.iter_rows())
        todo = pending(store, jobs)
        print(f"{HEADER}\njobs {len(jobs)} (k_c={k_c}); rows by status {dict(counts)}; "
              f"still to run {len(todo)}")  # fmt: skip
    return 0
