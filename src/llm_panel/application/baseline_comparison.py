"""Baseline B versus the paper's published scores (TASK-18): read cell B from the raw store,
compare per composite, render the report. Descriptive; supporting only (prereg s6)."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from dataclasses import dataclass, field
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
from llm_panel.domain.results import (
    STATUS_DEFERRED,
    STATUS_DUPLICATE,
    STATUS_FAILED,
    STATUS_INVALID,
    STATUS_OK,
)
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import ResultStore

BASELINE_CELL = "B"
ESSAY_COMPOSITES = ("welfare_resilience", "agency_voice", "scenario_durability")
DIMENSIONS = ("welfare_resilience", "agency_voice", "feasibility", "scenario_durability")


@dataclass(frozen=True)
class CellCounts:
    ok_jobs: int
    not_ok_jobs: int  # failed, awaiting retry, or stored ok but no longer parsing
    failed_jobs: int = 0  # of those, terminally failed
    deferred_jobs: int = 0  # retry withheld (e.g. spend ceiling), not ok and not failed
    duplicate_rows: int = 0  # usage-only rows: the job already finished via another batch

    def cells(self) -> str:
        """The count columns of a report table row, matching COUNT_HEADER."""
        return (f"{self.ok_jobs} | {self.not_ok_jobs} (failed {self.failed_jobs}) "
                f"| {self.deferred_jobs} | {self.duplicate_rows}")  # fmt: skip


COUNT_HEADER = "ok jobs | not ok | deferred | duplicate rows"
COUNT_NOTE = (
    "Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = "
    "terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = "
    "usage-only rows for jobs already finished (not outcomes)."
)
NO_PERSONA_NOTE = (
    "- A cell without personas (D2) makes one call per policy and repeat, so a failed call drops "
    "only that repeat x policy: its means average the surviving repeats per policy, and its "
    "single runs, repeat-noise SE and variance components use only the repeats with no failed "
    "call (TASK-37, prereg s13)."
)


@dataclass(frozen=True)
class BaselineComparison:
    panel: PanelMeans
    counts: CellCounts
    ours: dict[str, dict[str, float]]  # composite -> policy -> score
    published: dict[str, dict[str, float]]
    agreements: list[Agreement]
    provenance: tuple[str, ...]
    policy_order: tuple[str, ...]
    r8_check: list[Agreement] = field(default_factory=list)  # Table 4 means vs essay composites
    essay_agreements: list[Agreement] = field(default_factory=list)  # ours vs essay composites


def cell_observations(store: ResultStore) -> dict[str, tuple[list[Observation], CellCounts]]:
    """Ratings of every one-at-a-time cell from ok rows, each job counted once. Persona x policy
    jobs and joint (D1, persona x criterion) jobs both count; fractional-design rows (no cell id)
    do not."""
    ok: dict[str, set[str]] = defaultdict(set)
    attempted: dict[str, set[str]] = defaultdict(set)
    failed: dict[str, set[str]] = defaultdict(set)
    deferred: dict[str, set[str]] = defaultdict(set)
    duplicates: dict[str, int] = defaultdict(int)
    observations: dict[str, list[Observation]] = defaultdict(list)
    for row in store.iter_rows():
        cell_id = (row.request or {}).get("cell_id")
        if not cell_id:
            continue
        if row.status in (STATUS_OK, STATUS_INVALID, STATUS_FAILED):
            attempted[cell_id].add(row.job_id)
        if row.status == STATUS_FAILED:
            failed[cell_id].add(row.job_id)
        elif row.status == STATUS_DEFERRED:
            deferred[cell_id].add(row.job_id)
        elif row.status == STATUS_DUPLICATE:
            duplicates[cell_id] += 1
        if row.status != STATUS_OK or row.job_id in ok[cell_id]:
            continue
        job = RenderedJob.from_dict(row.request)
        try:
            ratings = parse_ratings(job, (row.response or {}).get("text") or "")
        except InvalidResponse:
            continue
        ok[cell_id].add(row.job_id)
        observations[cell_id] += [
            Observation(job.repeat, r.persona_id, r.policy_id, r.criterion_id, r.score)
            for r in ratings
        ]
    return {
        cell: (
            observations[cell],
            CellCounts(
                len(ok[cell]),
                len(attempted[cell] - ok[cell]),
                len(failed[cell] - ok[cell]),
                len(deferred[cell] - ok[cell] - failed[cell]),
                duplicates[cell],
            ),
        )
        for cell in attempted | deferred.keys() | duplicates.keys()
    }


def baseline_observations(
    store: ResultStore, cell_id: str = BASELINE_CELL
) -> tuple[list[Observation], CellCounts]:
    """Ratings of one cell from ok rows; each job counted once."""
    return cell_observations(store).get(cell_id, ([], CellCounts(0, 0)))


def run_baseline_comparison(
    store: ResultStore,
    published: PublishedTable,
    cell_id: str = BASELINE_CELL,
    essay: PublishedTable | None = None,
) -> BaselineComparison:
    observations, counts = baseline_observations(store, cell_id)
    panel = repeat_mean_panel(observations)
    ours = composite_scores(panel.scores)
    theirs = composite_scores(published.scores)
    r8_check: list[Agreement] = []
    essay_agreements: list[Agreement] = []
    if essay is not None:
        shared = tuple(c for c in ESSAY_COMPOSITES if c in essay.scores)
        r8_check = compare(theirs, essay.scores, shared)
        essay_agreements = compare(ours, essay.scores, shared)
    return BaselineComparison(
        panel=panel, counts=counts, ours=ours, published=theirs,
        agreements=compare(ours, theirs, tuple(COMPOSITES)),
        provenance=published.provenance, policy_order=published.policy_order,
        r8_check=r8_check, essay_agreements=essay_agreements,
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
        f"- Store: `{store_path}`; cell B ok jobs {c.ok_jobs}, not ok {c.not_ok_jobs} "
        f"(failed {c.failed_jobs}), deferred {c.deferred_jobs}, duplicate rows {c.duplicate_rows}.",
        f"- Repeats {p.n_repeats}; persona x policy pairs complete in every repeat {p.n_pairs} "
        f"(dropped {p.dropped_pairs}). Scores are repeat means of the unweighted panel mean.",
        f"- {COUNT_NOTE}",
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
    if result.essay_agreements:
        lines += _essay_section(result)
    return "\n".join(lines) + "\n"


def _essay_section(result: BaselineComparison) -> list[str]:
    lines = [
        "",
        "## Essay composite tables (reconstruction R8)",
        "",
        "The essay prints a composite per policy for Welfare, Agency and Durability. First check "
        "(R8): the unweighted mean of the published Table 4 columns against the essay's composite. "
        "Second: our baseline B against the same essay composites.",
        "",
        "| Composite | Policies | R8: max abs. diff | R8: Spearman | B vs essay: Spearman "
        "| B vs essay: Kendall tau-b | B vs essay: mean abs. diff |",
        "|---|---|---|---|---|---|---|",
    ]
    for r8, ours in zip(result.r8_check, result.essay_agreements, strict=True):
        worst = max((abs(d) for d in r8.differences.values()), default=math.nan)
        lines.append(
            f"| {r8.composite} | {ours.n_policies} | {_num(worst, 2)} | {_num(r8.spearman)} "
            f"| {_num(ours.spearman)} | {_num(ours.kendall_tau_b)} "
            f"| {_num(ours.mean_abs_diff, 1)} |"
        )
    lines += [
        "",
        "- Feasibility is not compared: the essay's composite averages six columns, including "
        "Popular Support (survey data) and Admin. Capacity and Speed as two columns, which our "
        "panel does not rate separately; it is transcribed for reference only.",
        "- R8 differences below 0.1 are rounding of the printed one-decimal values.",
    ]
    return lines


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
