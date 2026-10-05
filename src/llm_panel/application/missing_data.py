"""Missing-data sensitivity (TASK-37; prereg s7): read every cell and its failed calls from the raw
store, recompute the primary materiality count and the recommendation clauses under survivor-only
means and with failures imputed at 0 and at 100, render the report. Descriptive."""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from dataclasses import dataclass

from llm_panel.application.baseline_comparison import (
    BASELINE_CELL,
    COUNT_HEADER,
    COUNT_NOTE,
    CellCounts,
    cell_observations,
    is_study_store,
)
from llm_panel.application.rank_stability import report_order
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA
from llm_panel.domain.analysis_materiality import materiality
from llm_panel.domain.analysis_missing import (
    VARIANTS,
    Failure,
    variant_comparison,
    variant_observations,
)
from llm_panel.domain.analysis_rank import build_cell_array
from llm_panel.domain.analysis_recommend import (
    CLAUSE_TEXT,
    CLAUSES,
    MATERIALITY_M,
    RECOMMEND_CRITERIA,
    analyse_cell,
)
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import STATUS_FAILED, STATUS_INVALID, STATUS_OK
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import ResultStore

FLAG_RATE = 0.10  # prereg s7: a cell above 10% failures is flagged
COMMON_COMPLETE = "common_complete"
VIEWS = (COMMON_COMPLETE, *VARIANTS)
VIEW_TEXT = {
    COMMON_COMPLETE: "common-complete (primary)",
    "survivor": "survivor-only",
    "impute_0": "failures imputed at 0",
    "impute_100": "failures imputed at 100",
}


@dataclass(frozen=True)
class ViewRow:
    cell_id: str
    view: str
    n_units: int  # Table 4 policy x criterion means on both sides
    beyond: int  # |cell - B| > M
    max_abs_shift: float
    clauses: dict[str, bool | None]  # on the cell's own repeat mean


@dataclass(frozen=True)
class MissingDataReport:
    counts: dict[str, CellCounts]
    cell_order: list[str]
    failure_rate: dict[str, float]  # not ok jobs / attempted jobs
    flagged: list[str]
    rows: list[ViewRow]  # empty when there is no cell B


def cell_failures(store: ResultStore) -> dict[str, list[Failure]]:
    """Per cell, the ratings each attempted call that never gave a valid reply would have given
    (the "not ok" jobs of the other reports)."""
    requests: dict[str, dict[str, RenderedJob]] = defaultdict(dict)
    ok: dict[str, set[str]] = defaultdict(set)
    for row in store.iter_rows():
        cell_id = (row.request or {}).get("cell_id")
        if not cell_id or row.status not in (STATUS_OK, STATUS_INVALID, STATUS_FAILED):
            continue
        job = RenderedJob.from_dict(row.request)
        requests[cell_id][row.job_id] = job
        if row.status != STATUS_OK:
            continue
        try:
            parse_ratings(job, (row.response or {}).get("text") or "")
        except InvalidResponse:
            continue
        ok[cell_id].add(row.job_id)
    return {
        cell: [
            Failure(job.repeat, job.persona_id, job.policy_ids,
                    job.criterion_ids or (job.criterion_id,))
            for job_id, job in jobs.items() if job_id not in ok[cell]
        ]
        for cell, jobs in requests.items()
    }  # fmt: skip


def run_missing_data(store: ResultStore) -> MissingDataReport:
    by_cell = cell_observations(store)
    failures = cell_failures(store)
    counts = {cell: c for cell, (_, c) in by_cell.items()}
    policies = tuple(sorted({o.policy_id for obs, _ in by_cell.values() for o in obs}))
    order = report_order({c for c, (obs, _) in by_cell.items() if obs})
    rate = {}
    for cell, c in counts.items():
        attempted = c.ok_jobs + c.not_ok_jobs
        rate[cell] = c.not_ok_jobs / attempted if attempted else math.nan
    flagged = [c for c in order if rate.get(c, 0.0) > FLAG_RATE]
    rows: list[ViewRow] = []
    if BASELINE_CELL in order:

        def arrays(criteria, variant=None):
            return {
                cell: build_cell_array(
                    cell,
                    by_cell[cell][0] if variant is None else
                    variant_observations(by_cell[cell][0], failures.get(cell, []), variant),
                    policy_ids=policies, criteria=criteria, common_complete=variant is None,
                )
                for cell in order
            }  # fmt: skip

        primary, recommend = arrays(TABLE4_CRITERIA), arrays(RECOMMEND_CRITERIA)
        views = {v: arrays(RECOMMEND_CRITERIA, v) for v in VARIANTS}
        for cell in order:
            mat = materiality(primary[BASELINE_CELL], primary[cell])
            shifts = [abs(u.shift) for u in mat.units]
            clauses = analyse_cell(recommend[BASELINE_CELL], recommend[cell]).mean.clauses
            rows.append(ViewRow(
                cell, COMMON_COMPLETE, mat.n_units, mat.counts[MATERIALITY_M],
                max(shifts) if shifts else math.nan, {k: clauses[k].holds for k in CLAUSES},
            ))  # fmt: skip
            for v in VARIANTS:
                res = variant_comparison(views[v][BASELINE_CELL], views[v][cell])
                rows.append(ViewRow(cell, v, res.n_units, res.beyond, res.max_abs_shift,
                                    res.clauses))  # fmt: skip
    return MissingDataReport(counts, order, rate, flagged, rows)


def _num(value: float, digits: int = 1) -> str:
    return "n/a" if math.isnan(value) else f"{value:.{digits}f}"


def _holds(value: bool | None) -> str:
    return "n/a" if value is None else ("holds" if value else "fails")


def render_markdown(report: MissingDataReport, store_path: str) -> str:
    m = MATERIALITY_M
    lines = ["# Missing-data sensitivity", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    lines += [
        f"- Store: `{store_path}`.",
        "",
        "## Failures",
        "",
        f"A cell with failures above {FLAG_RATE:.0%} of its attempted calls is flagged (prereg s7) "
        "and still analysed on the common-complete set.",
        "",
        f"| Cell | {COUNT_HEADER} | failure rate | flag |",
        "|---|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        flag = f"**above {FLAG_RATE:.0%}**" if cell in report.flagged else ""
        lines.append(f"| {cell} | {report.counts[cell].cells()} "
                     f"| {report.failure_rate[cell]:.1%} | {flag} |")  # fmt: skip
    lines += ["", f"_{COUNT_NOTE}_", ""]
    if not report.rows:
        lines += ["No cell B data in the store, so no cell can be compared with B.", ""]
        return "\n".join(lines)
    lines += [
        "## Views",
        "",
        "- Common-complete (primary): the materiality count and the clauses exactly as in the "
        "materiality and recommendations reports.",
        "- Survivor-only (secondary): every valid rating, no common-complete filter and no pairing "
        "with B; a unit's mean is the panel mean per repeat over the personas present, then the "
        "mean over the repeats present.",
        "- Worst-case bound: every failed call's ratings imputed at 0, and separately imputed at "
        "100, then averaged as survivor-only (B under the same imputation).",
        f"- Beyond M: Table 4 policy x criterion means whose |shift from B| exceeds M = {m:g}. "
        "Clauses: on the cell's own repeat mean (B's row gives B's own result).",
        "",
        f"| Cell | view | units | beyond M = {m:g} | max abs shift "
        + "".join(f"| ({c}) " if c != "sequence" else "| sequence " for c in CLAUSES)
        + "|",
        "|---|---|---|---|---|" + "---|" * len(CLAUSES),
    ]
    for r in report.rows:
        lines.append(
            f"| {r.cell_id} | {VIEW_TEXT[r.view]} | {r.n_units} | {r.beyond} "
            f"| {_num(r.max_abs_shift)} | "
            + " | ".join(_holds(r.clauses[c]) for c in CLAUSES)
            + " |"
        )
    lines += ["", "Clauses:", ""]
    lines += [f"- ({c}) {CLAUSE_TEXT[c]}" if c != "sequence" else f"- {CLAUSE_TEXT[c]}"
              for c in CLAUSES]  # fmt: skip
    lines += [
        "",
        "## How to read this",
        "",
        "- The imputations are bounds, not estimates: a failed call is unlikely to have given 0 "
        "or 100 on every criterion, and imputing every failure at one extreme is not the most "
        "adverse case for a count or a clause. Where a result is the same under every view, it "
        "survives these two imputations.",
        "- B's failures are imputed too, so a cell with no failures of its own can still move "
        "under imputation; survivor-only drops the pairing with B, so a partial cell (Q3c) can "
        "differ from its common-complete count.",
        "- In a cell without personas (D2) a failed call drops only that repeat x policy "
        "(TASK-37, prereg s13), so its common-complete and survivor-only means coincide.",
        "- Instability of the scores, where present, shows they lack the claimed precision, not "
        "that the recommendations are wrong.",
        "",
    ]
    return "\n".join(lines)


def render_csv(report: MissingDataReport) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["cell_id", "view", "n_units", "beyond_m", "max_abs_shift",
                *(f"clause_{c}" for c in CLAUSES), "failure_rate", "flagged"])  # fmt: skip
    for r in report.rows:
        w.writerow([
            r.cell_id, r.view, r.n_units, r.beyond,
            "" if math.isnan(r.max_abs_shift) else f"{r.max_abs_shift:.4f}",
            *("" if r.clauses[c] is None else r.clauses[c] for c in CLAUSES),
            f"{report.failure_rate[r.cell_id]:.4f}", r.cell_id in report.flagged,
        ])  # fmt: skip
    return buf.getvalue()
