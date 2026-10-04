"""Materiality shifts (TASK-28; prereg s6 primary metric 2): read every cell from the raw store,
count the policy x criterion panel means each cell moves more than M from B, render the report."""

from __future__ import annotations

import csv
import io
import math
import statistics
from dataclasses import dataclass, replace

from llm_panel.application.baseline_comparison import (
    BASELINE_CELL,
    COUNT_HEADER,
    COUNT_NOTE,
    CellCounts,
    cell_observations,
    is_study_store,
)
from llm_panel.application.rank_stability import report_order
from llm_panel.application.variance import FACTORS, rated_criteria
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA
from llm_panel.domain.analysis_materiality import (
    MARGINS,
    MATERIALITY_M,
    SENSITIVITY_M,
    Materiality,
    materiality,
)
from llm_panel.domain.analysis_rank import CellArray, build_cell_array
from llm_panel.ports import ResultStore


@dataclass(frozen=True)
class MaterialityReport:
    counts: dict[str, CellCounts]
    cells: dict[str, CellArray]
    cell_order: list[str]
    results: list[Materiality]  # primary: the Table 4 criteria; every cell but B
    extra_results: list[Materiality]  # descriptive: the added criteria only (prereg s10)


def run_materiality(store: ResultStore) -> MaterialityReport:
    by_cell = cell_observations(store)
    policies = tuple(sorted({o.policy_id for obs, _ in by_cell.values() for o in obs}))
    criteria = rated_criteria({o.criterion_id for obs, _ in by_cell.values() for o in obs})
    arrays = {
        cell: build_cell_array(cell, obs, policy_ids=policies, criteria=criteria)
        for cell, (obs, _) in by_cell.items()
        if obs
    }
    order = report_order(arrays)
    results, extra_results = [], []
    if BASELINE_CELL in arrays:
        primary = {c: _restrict(a, keep_table4=True) for c, a in arrays.items()}
        extras = {c: _restrict(a, keep_table4=False) for c, a in arrays.items()}
        results = [materiality(primary[BASELINE_CELL], primary[c])
                   for c in order if c != BASELINE_CELL]  # fmt: skip
        if extras[BASELINE_CELL].criteria:
            extra_results = [materiality(extras[BASELINE_CELL], extras[c])
                             for c in order if c != BASELINE_CELL]  # fmt: skip
    counts = {cell: c for cell, (_, c) in by_cell.items()}
    return MaterialityReport(counts, arrays, order, results, extra_results)


def _restrict(a: CellArray, *, keep_table4: bool) -> CellArray:
    keep = [i for i, c in enumerate(a.criteria) if (c in TABLE4_CRITERIA) == keep_table4]
    return replace(a, criteria=tuple(a.criteria[i] for i in keep), scores=a.scores[:, keep])


def _num(value: float, digits: int = 2) -> str:
    return "n/a" if math.isnan(value) else f"{value:.{digits}f}"


def _band(values: tuple[int, ...]) -> str:
    if not values:
        return "n/a"
    return f"{min(values)} / {statistics.median(values):g} / {max(values)} (n={len(values)})"


def render_markdown(report: MaterialityReport, store_path: str) -> str:
    m, (m_lo, m_hi) = MATERIALITY_M, SENSITIVITY_M
    lines = ["# Materiality shifts", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    lines += [f"- Store: `{store_path}`.", ""]
    if BASELINE_CELL not in report.cells:
        lines += ["No cell B data in the store, so no cell can be compared with B.", ""]
        return "\n".join(lines)
    lines += [
        "## Data",
        "",
        f"| Cell | {COUNT_HEADER} | repeats |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        cnt = report.counts[cell]
        lines.append(f"| {cell} | {cnt.cells()} "
                     f"| {len(report.cells[cell].repeats)} |")  # fmt: skip
    lines += ["", f"_{COUNT_NOTE}_"]
    lines += [
        "",
        f"## Policy x criterion means shifted by more than M = {m:g} points (primary)",
        "",
        f"Primary metric 2 of prereg s6: per cell, the number of policy x criterion panel means "
        f"whose |shift from B| exceeds M = {m:g} points, set in advance. Shift = cell repeat mean "
        "- B repeat mean, unweighted panel means on the common-complete set. Noise SE: the "
        "repeat-noise standard error of one unit's shift; M / SE gives the margin as a "
        "repeat-noise multiple. B split band: the same count for every split of B's repeats into "
        "the cell's repeat count and the rest, min / median / max (what repeats alone do; "
        "descriptive, not a test; n/a when the cell has as many repeats as B or more). "
        f"M = {m_lo:g} and M = {m_hi:g} are a descriptive sensitivity and are not used to pick M.",
        "",
        f"| Cell | factor | pairing | repeats | units | beyond M = {m:g} | B split band "
        f"(M = {m:g}) | noise SE | M / SE | beyond {m_lo:g} | beyond {m_hi:g} | noise |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in report.results:
        lines.append(
            f"| {r.cell_id} | {FACTORS.get(r.cell_id, '?')} | {r.pairing} | {r.k_cell} "
            f"| {r.n_units} | **{r.counts[m]}** | {_band(r.band[m])} | {_num(r.noise_se)} "
            f"| {_num(r.m_noise_multiple, 1)} | {r.counts[m_lo]} | {r.counts[m_hi]} "
            f"| {r.noise_source} |"
        )
    lines += ["", f"## Units beyond M = {m:g}, per cell", ""]
    for r in report.results:
        beyond = sorted((u for u in r.units if u.beyond(m)), key=lambda u: -abs(u.shift))
        if not beyond:
            lines.append(f"- {r.cell_id}: none.")
            continue
        parts = [f"{u.policy_id} x {u.criterion} {u.shift:+.1f} ({_num(u.noise_multiple, 1)} SE)"
                 for u in beyond]  # fmt: skip
        lines.append(f"- {r.cell_id}: " + "; ".join(parts) + ".")
    if report.extra_results:
        lines += [
            "",
            f"## Added criteria (descriptive, not in the primary count), M = {m:g}",
            "",
            "Political Support and Administrative Capacity and Speed are not Table 4 columns "
            "(prereg s10, 2026-10-04): counted here separately and never added to the primary "
            "count above.",
            "",
            f"| Cell | units | beyond M = {m:g} | beyond {m_lo:g} | beyond {m_hi:g} |",
            "|---|---|---|---|---|",
        ]
        for r in report.extra_results:
            lines.append(f"| {r.cell_id} | {r.n_units} | {r.counts[m]} | {r.counts[m_lo]} "
                         f"| {r.counts[m_hi]} |")  # fmt: skip
    lines += [
        "",
        "## How to read this",
        "",
        "- Every cell and every policy x criterion is reported; the CSV files hold all shifts. "
        "Holm correction applies to the primary set only if inference language is used "
        "(prereg s6).",
        "- Instability of the scores, where present, shows they lack the claimed precision, not "
        "that the recommendations are wrong.",
        "- Noise column: 'own' when the cell has two or more repeats; 'B' when a one-repeat cell "
        "borrows B's noise (assumes equal noise).",
        "- D2 (no persona) and D2b (another panel) are not paired with B's personas; their shifts "
        "mix the factor with who rates. Block D cells are read separately from blocks R and Q "
        "(prereg s5).",
        "",
    ]
    return "\n".join(lines)


def _csv(header: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def _cell(value: float) -> str:
    return "" if math.isnan(value) else f"{value:.4f}"


def render_counts_csv(report: MaterialityReport) -> str:
    rows = []
    for r in (*report.results, *report.extra_results):
        for m in MARGINS:
            band = r.band[m]
            rows.append([
                "table4" if r in report.results else "added", r.cell_id,
                FACTORS.get(r.cell_id, ""), r.pairing, r.k_b, r.k_cell, f"{m:g}",
                m == MATERIALITY_M and r in report.results, r.counts[m], r.n_units,
                _cell(r.noise_se),
                _cell(m / r.noise_se if r.noise_se > 0 else math.nan), r.noise_source,
                min(band) if band else "", statistics.median(band) if band else "",
                max(band) if band else "", len(band),
            ])  # fmt: skip
    header = ["criteria_set", "cell_id", "factor", "pairing", "k_b", "k_cell", "m", "primary",
              "count", "n_units", "noise_se", "m_noise_multiple", "noise_source", "band_min",
              "band_median", "band_max", "n_splits"]  # fmt: skip
    return _csv(header, rows)


def render_units_csv(report: MaterialityReport) -> str:
    rows = [
        ["table4" if r in report.results else "added", r.cell_id, u.policy_id, u.criterion,
         _cell(u.b_mean), _cell(u.cell_mean),
         _cell(u.shift), _cell(u.noise_multiple), *(u.beyond(m) for m in MARGINS)]
        for r in (*report.results, *report.extra_results)
        for u in r.units
    ]  # fmt: skip
    header = ["criteria_set", "cell_id", "policy_id", "criterion", "b_mean", "cell_mean", "shift",
              "noise_multiple", *(f"beyond_{m:g}" for m in MARGINS)]  # fmt: skip
    return _csv(header, rows)
