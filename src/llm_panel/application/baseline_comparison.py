"""Baseline B versus the paper's published scores (TASK-18): read cell B from the raw store,
compare per composite, render the report. Descriptive; supporting only (prereg s6)."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from pathlib import PurePath

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    Agreement,
    Observation,
    PanelMeans,
    PublishedTable,
    compare,
    composite_scores,
    repeat_mean_panel,
)
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import STATUS_FAILED, STATUS_INVALID, STATUS_OK
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import ResultStore

BASELINE_CELL = "B"
DIMENSIONS = ("welfare_resilience", "agency_voice", "feasibility", "scenario_durability")


@dataclass(frozen=True)
class CellCounts:
    ok_jobs: int
    not_ok_jobs: int  # failed, awaiting retry, or stored ok but no longer parsing


@dataclass(frozen=True)
class BaselineComparison:
    panel: PanelMeans
    counts: CellCounts
    ours: dict[str, dict[str, float]]  # composite -> policy -> score
    published: dict[str, dict[str, float]]
    agreements: list[Agreement]
    provenance: tuple[str, ...]
    policy_order: tuple[str, ...]


def baseline_observations(
    store: ResultStore, cell_id: str = BASELINE_CELL
) -> tuple[list[Observation], CellCounts]:
    """Ratings of one persona x policy cell from ok rows; each job counted once."""
    ok: set[str] = set()
    attempted: set[str] = set()
    observations: list[Observation] = []
    for row in store.iter_rows():
        if (row.request or {}).get("cell_id") != cell_id:
            continue
        if row.status in (STATUS_OK, STATUS_INVALID, STATUS_FAILED):
            attempted.add(row.job_id)
        if row.status != STATUS_OK or row.job_id in ok:
            continue
        job = RenderedJob.from_dict(row.request)
        if not job.criterion_ids:
            continue  # not a persona x policy job
        try:
            ratings = parse_ratings(job, (row.response or {}).get("text") or "")
        except InvalidResponse:
            continue
        ok.add(row.job_id)
        observations += [
            Observation(job.repeat, r.persona_id, r.policy_id, r.criterion_id, r.score)
            for r in ratings
        ]
    return observations, CellCounts(len(ok), len(attempted - ok))


def run_baseline_comparison(
    store: ResultStore, published: PublishedTable, cell_id: str = BASELINE_CELL
) -> BaselineComparison:
    observations, counts = baseline_observations(store, cell_id)
    panel = repeat_mean_panel(observations)
    ours = composite_scores(panel.scores)
    theirs = composite_scores(published.scores)
    return BaselineComparison(
        panel=panel, counts=counts, ours=ours, published=theirs,
        agreements=compare(ours, theirs, tuple(COMPOSITES)),
        provenance=published.provenance, policy_order=published.policy_order,
    )  # fmt: skip


def is_study_store(store_path: str) -> bool:
    """True only for the study's raw store (results/raw); pilot and smoketest stores are not."""
    parent = PurePath(store_path).parent
    return parent.name == "raw" and parent.parent.name == "results"


def _num(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None or math.isnan(value) else f"{value:.{digits}f}"


def render_markdown(result: BaselineComparison, store_path: str) -> str:
    lines = ["# Baseline B versus the paper's published scores", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    p, c = result.panel, result.counts
    lines += [
        f"- Store: `{store_path}`; cell B ok jobs {c.ok_jobs}, not ok {c.not_ok_jobs}.",
        f"- Repeats {p.n_repeats}; persona x policy pairs complete in every repeat {p.n_pairs} "
        f"(dropped {p.dropped_pairs}). Scores are repeat means of the unweighted panel mean.",
        "- Published source:",
        *[f"  {line}" for line in result.provenance],
        "",
        "## Agreement (rank correlation, not exact match)",
        "",
        "| Composite | Policies | Spearman | Kendall tau-b | Mean abs. difference |",
        "|---|---|---|---|---|",
    ]
    for a in result.agreements:
        lines.append(
            f"| {a.composite} | {a.n_policies} | {_num(a.spearman)} | {_num(a.kendall_tau_b)} "
            f"| {_num(a.mean_abs_diff, 1)} |"
        )
    lines += [
        "",
        "## How to read this",
        "",
        "- Agreement is reported as rank correlation, not exact match: the paper makes its "
        "recommendations by rank order, and our setup is a reconstruction, so equal scores are "
        "not expected. The mean absolute difference (score points) is descriptive only.",
        "- Any gap between our baseline and the published numbers may come from our "
        "reconstruction as well as from instability of the panel scores. Prompts, evidence "
        "packets, personas, model and aggregation are our stand-ins (prereg/reconstruction.md); "
        "this comparison cannot tell the two sources apart.",
        "- Agreement does not validate our procedure either: Table 4 has many round values "
        "(65.0 three times, 50.0, 27.0, 30.0, 78.0, 68.0) that a mean of 51 continuous scores "
        "would rarely produce, so the paper's aggregation is uncertain.",
        "- Instability of the scores, where present, shows they lack the claimed precision, not "
        "that the recommendations are wrong.",
        "- Composites are unweighted means of Table 4 columns. Feasibility is Economic "
        "Feasibility and Implementation Readiness only, the two columns in Table 4's Feasibility "
        "block (our reading; Table 1 also names Political, Popular and Administrative criteria, "
        "which the paper never publishes per policy). Scenario Durability is the mean of the "
        "three scenarios.",
        "- Implementation Readiness carries an unexplained dagger in the paper (the essay calls "
        "it author-coded); its comparison is lower-confidence.",
        "- Not compared: Political Support and Administrative Capacity & Speed (rated by us, not "
        "in Table 4) and Public Net Approval (survey data, not a panel rating).",
        "",
        "## Dimension composites per policy (ours / published)",
        "",
        "| Policy | " + " | ".join(DIMENSIONS) + " |",
        "|---|" + "---|" * len(DIMENSIONS),
    ]
    for policy in result.policy_order:
        cells = [
            f"{_num(result.ours[d].get(policy), 1)} / {_num(result.published[d].get(policy), 1)}"
            for d in DIMENSIONS
        ]
        lines.append(f"| {policy} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _csv(header: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def _cell(value: float | None) -> str:
    return "" if value is None or math.isnan(value) else f"{value:.4f}"


def render_agreement_csv(result: BaselineComparison) -> str:
    return _csv(
        ["composite", "n_policies", "spearman", "kendall_tau_b", "mean_abs_diff"],
        [
            [
                a.composite,
                a.n_policies,
                _cell(a.spearman),
                _cell(a.kendall_tau_b),
                _cell(a.mean_abs_diff),
            ]
            for a in result.agreements
        ],
    )


def render_policy_csv(result: BaselineComparison) -> str:
    rows = []
    for composite in COMPOSITES:
        ours, theirs = result.ours.get(composite, {}), result.published.get(composite, {})
        for policy in result.policy_order:
            mine, pub = ours.get(policy), theirs.get(policy)
            diff = mine - pub if mine is not None and pub is not None else None
            rows.append([composite, policy, _cell(mine), _cell(pub), _cell(diff)])
    return _csv(["composite", "policy_id", "ours", "published", "difference"], rows)
