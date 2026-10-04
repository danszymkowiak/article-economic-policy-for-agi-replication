"""Rank stability between cells (TASK-19): read every cell from the raw store, compare each with
B, render the report. Descriptive; rank metrics are secondary to flips (prereg s6)."""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Sequence
from dataclasses import dataclass

from llm_panel.application.baseline_comparison import (
    BASELINE_CELL,
    CellCounts,
    cell_observations,
    is_study_store,
)
from llm_panel.domain.analysis_baseline import COMPOSITES
from llm_panel.domain.analysis_rank import (
    AGGREGATIONS,
    DEFAULT_RESAMPLES,
    PREREG_COMPOSITES,
    TOP_K,
    CellArray,
    CellComparison,
    RankStability,
    build_cell_array,
    rank_stability,
)
from llm_panel.domain.oat_design import PRIORITY_ORDER, UNIT_CELLS
from llm_panel.ports import ResultStore

PRIMARY_AGGREGATION = "mean"  # prereg s4; median and trimmed mean are exploratory
# Report order: B, then the design's units in priority order, then anything unexpected.
_KNOWN_ORDER = [c for unit in PRIORITY_ORDER for c in UNIT_CELLS[unit]]


@dataclass(frozen=True)
class RankStabilityReport:
    result: RankStability | None  # None when the store holds no cell B ratings
    counts: dict[str, CellCounts]
    cells: dict[str, CellArray]
    cell_order: list[str]  # B first, then the compared cells


def report_order(cell_ids) -> list[str]:
    known = [c for c in _KNOWN_ORDER if c in cell_ids]
    return known + sorted(set(cell_ids) - set(known))


def run_rank_stability(
    store: ResultStore, *, resamples: int = DEFAULT_RESAMPLES, seed: int = 0
) -> RankStabilityReport:
    by_cell = cell_observations(store)
    policies = tuple(sorted({o.policy_id for obs, _ in by_cell.values() for o in obs}))
    counts = {cell: c for cell, (_, c) in by_cell.items()}
    arrays = {
        cell: build_cell_array(cell, obs, policy_ids=policies)
        for cell, (obs, _) in by_cell.items()
        if obs
    }
    order = report_order(arrays)
    if BASELINE_CELL not in arrays:
        return RankStabilityReport(None, counts, arrays, order)
    others = [arrays[c] for c in order if c != BASELINE_CELL]
    result = rank_stability(arrays[BASELINE_CELL], others, resamples=resamples, seed=seed)
    return RankStabilityReport(result, counts, arrays, order)


def _num(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None or math.isnan(value) else f"{value:.{digits}f}"


def _range(values: Sequence[float]) -> str:
    ok = [v for v in values if not math.isnan(v)]
    return f"{min(ok):.2f} to {max(ok):.2f}" if ok else "n/a"


def _below_band(c: CellComparison) -> bool:
    return not math.isnan(c.band_min) and not math.isnan(c.tau) and c.tau < c.band_min


def _max_shift(c: CellComparison) -> float:
    return max((abs(rc - rb) for rb, rc in c.rank_shifts.values()), default=math.nan)


def render_markdown(report: RankStabilityReport, store_path: str) -> str:
    lines = ["# Rank stability between cells", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    lines += [f"- Store: `{store_path}`.", ""]
    res = report.result
    if res is None:
        lines += ["No cell B data in the store, so no cell can be compared with B.", ""]
        return "\n".join(lines)
    comps = res.comparisons
    pairing = {c.cell_id: c.pairing for c in comps}
    lines += [
        "## Data",
        "",
        "| Cell | ok jobs | not ok | repeats | personas | pairing with B |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        arr, cnt = report.cells[cell], report.counts[cell]
        lines.append(
            f"| {cell} | {cnt.ok_jobs} | {cnt.not_ok_jobs} | {len(arr.repeats)} "
            f"| {len(arr.persona_ids) if arr.has_personas else 0} "
            f"| {'(reference)' if cell == BASELINE_CELL else pairing.get(cell, '')} |"
        )
    placeholder = (
        " This count is a **placeholder**: prereg s12 item 6 (persona bootstrap resample count) "
        "is still open." if res.resamples == DEFAULT_RESAMPLES else
        " Prereg s12 item 6 (persona bootstrap resample count) is still open."
    )  # fmt: skip
    lines += [
        "",
        f"- Persona bootstrap: {res.resamples} resamples, seed {res.seed}; 95% percentile "
        f"intervals.{placeholder}",
        f"- B repeats: {res.b_repeats}. Primary aggregation: unweighted mean over personas "
        "(prereg s4).",
        "",
        "## Repeat-noise reference: Kendall tau among B's repeats (mean aggregation)",
        "",
        "Pairwise: tau between two single B repeats. Split k: tau between the mean of k B repeats "
        "and the mean of the remaining ones, over every split (prereg s3; a descriptive band, not "
        "a test: the splits overlap).",
        "",
        "| Composite | Kind | n | min | median | max |",
        "|---|---|---|---|---|---|",
    ]
    for n in res.noise:
        if n.aggregation == PRIMARY_AGGREGATION and n.composite in PREREG_COMPOSITES:
            lines.append(
                f"| {n.composite} | {n.kind} | {n.n} | {_num(n.minimum)} | {_num(n.median)} "
                f"| {_num(n.maximum)} |"
            )
    mean = {
        (c.cell_id, c.composite): c for c in comps if c.aggregation == PRIMARY_AGGREGATION
    }  # fmt: skip
    cells = report.cell_order[1:]
    lines += [
        "",
        "## Kendall tau versus B (mean aggregation, prereg composites)",
        "",
        "Each entry: tau-b [persona-bootstrap 95% interval].",
        "",
        "| Cell | " + " | ".join(PREREG_COMPOSITES) + " |",
        "|---|" + "---|" * len(PREREG_COMPOSITES),
    ]
    for cell in cells:
        entries = [
            f"{_num(c.tau)} [{_num(c.ci_low)}, {_num(c.ci_high)}]"
            for c in (mean[(cell, name)] for name in PREREG_COMPOSITES)
        ]
        lines.append(f"| {cell} | " + " | ".join(entries) + " |")
    lines += [
        "",
        "## Against repeat noise and single runs (mean aggregation, prereg composites)",
        "",
        "Below band: composites whose tau is under the minimum of B's split band for the cell's "
        "repeat count (n/a when the cell has as many repeats as B or more). Single-run range: "
        "each repeat of the cell against B's repeat mean, over the prereg composites.",
        "",
        f"| Cell | repeats | below band | single-run tau range | top-{TOP_K} changes "
        f"| bottom-{TOP_K} changes | max abs. rank shift |",
        "|---|---|---|---|---|---|---|",
    ]
    for cell in cells:
        rows = [mean[(cell, name)] for name in PREREG_COMPOSITES]
        has_band = any(not math.isnan(c.band_min) for c in rows)
        below = [c.composite for c in rows if _below_band(c)]
        top = [f"{c.composite} (+{','.join(c.top_entered)} -{','.join(c.top_left)})"
               for c in rows if c.top_entered or c.top_left]  # fmt: skip
        bottom = [f"{c.composite} (+{','.join(c.bottom_entered)} -{','.join(c.bottom_left)})"
                  for c in rows if c.bottom_entered or c.bottom_left]  # fmt: skip
        values = [v for c in rows for v in (c.single_run_min, c.single_run_max)]
        lines.append(
            f"| {cell} | {rows[0].n_repeats} "
            f"| {(', '.join(below) or 'none') if has_band else 'n/a'} | {_range(values)} "
            f"| {'; '.join(top) or 'none'} | {'; '.join(bottom) or 'none'} "
            f"| {_num(max(_max_shift(c) for c in rows), 1)} |"
        )
    lines += [
        "",
        "## Aggregation over personas (exploratory)",
        "",
        "Not in prereg s6, so exploratory. Range of tau versus B over all "
        f"{len(COMPOSITES)} composites, under each aggregation applied to both sides; then the "
        "lowest tau between two aggregations of the same cell's scores.",
        "",
        "| Cell | " + " | ".join(f"vs B, {a}" for a in AGGREGATIONS) + " |",
        "|---|" + "---|" * len(AGGREGATIONS),
    ]
    for cell in cells:
        entries = [
            _range([c.tau for c in comps if c.cell_id == cell and c.aggregation == a])
            for a in AGGREGATIONS
        ]
        lines.append(f"| {cell} | " + " | ".join(entries) + " |")
    pairs = sorted({(a.aggregation_a, a.aggregation_b) for a in res.aggregation_agreement},
                   key=lambda p: (AGGREGATIONS.index(p[0]), AGGREGATIONS.index(p[1])))  # fmt: skip
    lines += [
        "",
        "| Cell | " + " | ".join(f"min tau {a} vs {z}" for a, z in pairs) + " |",
        "|---|" + "---|" * len(pairs),
    ]
    for cell in report.cell_order:
        entries = []
        for a, z in pairs:
            taus = [
                g.tau for g in res.aggregation_agreement
                if g.cell_id == cell and (g.aggregation_a, g.aggregation_b) == (a, z)
                and not math.isnan(g.tau)
            ]  # fmt: skip
            entries.append(_num(min(taus)) if taus else "n/a")
        lines.append(f"| {cell} | " + " | ".join(entries) + " |")
    lines += [
        "",
        "## How to read this",
        "",
        "- Rank metrics are reported for every cell because the paper makes its recommendations "
        "by rank order, but they are secondary to the flip counts and materiality shifts "
        "(prereg s6). Tau moves only when near-ties swap, and the published scores have many.",
        "- Instability of the scores, where present, shows they lack the claimed precision, not "
        "that the recommendations are wrong.",
        "- The persona bootstrap asks whether other personas would agree. It is secondary, a "
        "generalisation caveat only, and is not mixed into the comparison with repeat noise "
        "(prereg s3). Paired cells share B's persona draw; D2b (another panel) gets its own "
        "draw; D2 (no persona) is not resampled.",
        "- Ties count by Kendall tau-b's correction; ranks are average ranks (rank 1 = highest "
        f"score). A policy is in the top {TOP_K} when its average rank is at most {TOP_K}, so a "
        "tie across the boundary is in neither set.",
        "- Block D cells change the design, not a small detail, and are read separately from "
        "blocks R and Q (prereg s5).",
        "- Every composite and every cell is reported (CSV files hold all composites, "
        "aggregations and per-policy rank shifts). Political Support and Administrative "
        "Capacity & Speed are not in any composite.",
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


def _comparisons(report: RankStabilityReport) -> list[CellComparison]:
    return report.result.comparisons if report.result else []


def render_tau_csv(report: RankStabilityReport) -> str:
    header = [
        "cell_id", "aggregation", "composite", "prereg", "pairing", "n_repeats", "n_policies",
        "tau", "ci_low", "ci_high", "n_boot_undefined", "single_run_min", "single_run_max",
        "band_min", "band_max", "below_band", f"top{TOP_K}_entered", f"top{TOP_K}_left",
        f"bottom{TOP_K}_entered", f"bottom{TOP_K}_left", "max_abs_rank_shift",
    ]  # fmt: skip
    rows = [
        [
            c.cell_id,
            c.aggregation,
            c.composite,
            c.composite in PREREG_COMPOSITES,
            c.pairing,
            c.n_repeats,
            c.n_policies,
            _cell(c.tau),
            _cell(c.ci_low),
            _cell(c.ci_high),
            c.n_boot_undefined,
            _cell(c.single_run_min),
            _cell(c.single_run_max),
            _cell(c.band_min),
            _cell(c.band_max),
            _below_band(c),
            " ".join(c.top_entered),
            " ".join(c.top_left),
            " ".join(c.bottom_entered),
            " ".join(c.bottom_left),
            _cell(_max_shift(c)),
        ]
        for c in _comparisons(report)
    ]
    return _csv(header, rows)


def render_shifts_csv(report: RankStabilityReport) -> str:
    rows = [
        [c.cell_id, c.aggregation, c.composite, policy, rb, rc, rc - rb]
        for c in _comparisons(report)
        for policy, (rb, rc) in sorted(c.rank_shifts.items())
    ]
    header = ["cell_id", "aggregation", "composite", "policy_id", "rank_b", "rank_cell", "shift"]
    return _csv(header, rows)


def render_noise_csv(report: RankStabilityReport) -> str:
    noise = report.result.noise if report.result else []
    return _csv(
        ["aggregation", "composite", "kind", "n", "min", "median", "max"],
        [
            [
                n.aggregation,
                n.composite,
                n.kind,
                n.n,
                _cell(n.minimum),
                _cell(n.median),
                _cell(n.maximum),
            ]
            for n in noise
        ],
    )


def render_aggregation_csv(report: RankStabilityReport) -> str:
    agree = report.result.aggregation_agreement if report.result else []
    return _csv(
        ["cell_id", "composite", "aggregation_a", "aggregation_b", "tau"],
        [[a.cell_id, a.composite, a.aggregation_a, a.aggregation_b, _cell(a.tau)] for a in agree],
    )
