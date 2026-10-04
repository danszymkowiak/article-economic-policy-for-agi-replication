"""Recommendation robustness (TASK-21): read every cell from the raw store, evaluate the prereg s6
recommendation clauses, the three-stage sequence, score consistency and the blinding contrast per
cell and per single run, render the report. Descriptive (prereg s6)."""

from __future__ import annotations

import csv
import io
import math
import statistics
from collections.abc import Mapping, Sequence
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
from llm_panel.domain.analysis_rank import CellArray, build_cell_array
from llm_panel.domain.analysis_recommend import (
    CLAUSE_TEXT,
    CLAUSES,
    DURABILITY_COMPOSITES,
    MATERIALITY_M,
    OWNERSHIP,
    RECOMMEND_CRITERIA,
    STAGES,
    CellRecommendations,
    RunResult,
    SplitNoise,
    analyse_cell,
    noise_floor,
)
from llm_panel.ports import ResultStore

BLINDED_CELL = "Q1"  # description-only: policy names removed (prereg s5)


@dataclass(frozen=True)
class RecommendationReport:
    counts: dict[str, CellCounts]
    cells: dict[str, CellArray]
    cell_order: list[str]
    results: dict[str, CellRecommendations]  # B included: B's single runs against its own mean
    noise: dict[int, SplitNoise]  # B's k-split reference, k = the other cells' repeat counts
    has_approvals: bool


def run_recommendations(
    store: ResultStore, net_approval: Mapping[str, float] | None = None
) -> RecommendationReport:
    by_cell = cell_observations(store)
    policies = tuple(sorted({o.policy_id for obs, _ in by_cell.values() for o in obs}))
    counts = {cell: c for cell, (_, c) in by_cell.items()}
    arrays = {
        cell: build_cell_array(cell, obs, policy_ids=policies, criteria=RECOMMEND_CRITERIA)
        for cell, (obs, _) in by_cell.items()
        if obs
    }
    order = report_order(arrays)
    if BASELINE_CELL not in arrays:
        return RecommendationReport(counts, arrays, order, {}, {}, bool(net_approval))
    b = arrays[BASELINE_CELL]
    results = {c: analyse_cell(b, arrays[c], net_approval) for c in order}
    ks = [len(arrays[c].repeats) for c in order if c != BASELINE_CELL]
    return RecommendationReport(
        counts, arrays, order, results, noise_floor(b, ks), bool(net_approval)
    )


def _num(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None or math.isnan(value) else f"{value + 0.0:.{digits}f}"


def _yes(value: bool | None) -> str:
    return "n/a" if value is None else ("yes" if value else "no")


def _spread(values: Sequence[float], digits: int = 1) -> str:
    ok = [v for v in values if not math.isnan(v)]
    if not ok:
        return "n/a"
    return (f"{_num(min(ok), digits)} / {_num(statistics.median(ok), digits)} / "
            f"{_num(max(ok), digits)} (n={len(ok)})")  # fmt: skip


def _range(values: Sequence[float], digits: int = 1) -> str:
    ok = [v for v in values if not math.isnan(v)]
    return f"{_num(min(ok), digits)} to {_num(max(ok), digits)}" if ok else "n/a"


def _count(runs: Sequence[RunResult], pred) -> str:
    defined = [pred(r) for r in runs]
    defined = [v for v in defined if v is not None]
    return f"{sum(defined)}/{len(defined)}" if defined else "n/a"


def _clause_cell(res: CellRecommendations, clause: str) -> str:
    m = res.mean.clauses[clause]
    flip = res.mean_flipped(clause)
    runs = len(res.runs)
    flip_txt = "" if res.cell_id == BASELINE_CELL else f", {'FLIP' if flip else 'same'}"
    return (f"{_yes(m.holds)} ({_num(m.margin)}{flip_txt}); runs flipped "
            f"{res.flip_count(clause)}/{runs}")  # fmt: skip


def _leaders(res: RunResult, composite: str) -> str:
    return ", ".join(res.consistency.leaders[composite]) or "n/a"


HOW_TO_READ = [
    "- Descriptive and unthresholded (prereg s6). Every cell is reported, with ranges across all "
    "cells, not only the largest change; the CSV files hold every run.",
    "- Instability of the scores, where present, shows they lack the claimed precision, not that "
    "the recommendations are wrong. A clause that flips says the scores cannot carry that rank "
    "claim at their stated precision; it does not say the policy advice is mistaken.",
    "- The clauses are the paper's own claims with cut-offs from Table 4, which passes all four, "
    "so B is not a test of the paper.",
    "- Flips are counted against B's repeat mean on the persona x policy x criterion set the two "
    "cells share (prereg s7). B's own row is the noise floor: its single runs against its mean. "
    "The k-split reference compares a k-repeat mean of B with the rest; it is descriptive, "
    "not a test (the splits overlap).",
    "- The score-consistency checks (leaders, UBS, NIT's political support, ALMP) are not in "
    "prereg s6 and are exploratory. 'Low' political support means a rank below the median "
    "policy (our reading; the paper gives no cut-off). Political Support is our rating; the "
    "paper does not publish it per policy.",
    "- Tier changes (prereg s6 item 1b) are not computed here: the paper defines no tiers or "
    "tier cut-offs for the Table 4 composites, so a tier change cannot be defined without "
    "inventing one. This is an open prereg item.",
    "- Block D cells change the design, not a small detail, and are read separately from blocks "
    "R and Q (prereg s5).",
]


def render_markdown(report: RecommendationReport, store_path: str) -> str:
    lines = ["# Recommendation robustness", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    lines += [f"- Store: `{store_path}`.", ""]
    if BASELINE_CELL not in report.results:
        lines += ["No cell B data in the store, so no clause can be compared with B.", ""]
        return "\n".join(lines)
    results = report.results
    others = [c for c in report.cell_order if c != BASELINE_CELL]
    lines += [
        "## Data",
        "",
        f"| Cell | {COUNT_HEADER} | repeats | pairing with B |",
        "|---|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        cnt, res = report.counts[cell], results[cell]
        pairing = "(reference)" if cell == BASELINE_CELL else res.pairing
        lines.append(f"| {cell} | {cnt.cells()} | {res.n_repeats} | {pairing} |")
    lines += ["", f"_{COUNT_NOTE}_"]
    lines += [
        "",
        "## Clauses (prereg s6)",
        "",
        *[
            f"- ({c}) {CLAUSE_TEXT[c]}" if c != "sequence" else f"- {CLAUSE_TEXT[c]}"
            for c in CLAUSES
        ],  # fmt: skip
        "",
        "Margin: the policy's score minus the k-th best score among the other policies (rank-1 "
        "clauses: the gap to the runner-up), so a clause holds exactly when its margin is "
        "positive; a tie at the cut-off does not hold. (d) and the sequence take the smallest "
        "margin of their parts. Published Table 4 margins: (a) 15.5, (b) 40.0, (c) 3.9 (NIT 69.8 "
        "minus UI 65.9 at rank 4; prereg s6 writes 3.8, the gap to UBC at rank 3), (d) 5.9.",
        "",
        "The paper's Mild recommendation also names employer-led retraining, but ALMP scores 42.5 "
        "on Mild in Table 4, so it is excluded from the clauses (prereg s6); its Mild rank is "
        "reported under score consistency.",
        "",
        "## Three-stage sequence per configuration",
        "",
        "Repeat mean: holds (margin, versus B's repeat mean); single runs: how many hold, how many "
        "flip against B, and the range of their margins.",
        "",
        "| Cell | repeat mean | flipped vs B | runs holding | runs flipped | single-run margins |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        m = res.mean.clauses["sequence"]
        flipped = "(reference)" if cell == BASELINE_CELL else _yes(res.mean_flipped("sequence"))
        lines.append(
            f"| {cell} | {_yes(m.holds)} ({_num(m.margin)}) | {flipped} "
            f"| {_count(res.runs, lambda r: r.clauses['sequence'].holds)} "
            f"| {res.flip_count('sequence')}/{len(res.runs)} "
            f"| {_range([r.clauses['sequence'].margin for r in res.runs])} |"
        )
    seq_margins = [results[c].mean.clauses["sequence"].margin for c in others]
    holding = [results[c].mean.clauses["sequence"].holds for c in others]
    lines += [
        "",
        f"- Across all cells other than B: the sequence holds in the repeat mean of "
        f"{sum(h is True for h in holding)} of {len(others)} cells; repeat-mean margin min / "
        f"median / max {_spread(seq_margins)}; single runs flipped "
        f"{sum(results[c].flip_count('sequence') for c in others)} of "
        f"{sum(len(results[c].runs) for c in others)}.",
        f"- Noise floor, B's single runs against B's repeat mean: "
        f"{results[BASELINE_CELL].flip_count('sequence')} of "
        f"{len(results[BASELINE_CELL].runs)} flipped.",
        "",
        "## Clause flips",
        "",
        "Each entry: repeat mean holds (margin, FLIP or same against B); single runs flipped.",
        "",
        "| Cell | (a) | (b) | (c) | (d) |",
        "|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        lines.append(f"| {cell} | " + " | ".join(_clause_cell(res, c) for c in "abcd") + " |")
    lines += ["", "Repeat-mean margin across all cells other than B, min / median / max:", ""]
    for c in CLAUSES:
        margins = [results[x].mean.clauses[c].margin for x in others]
        lines.append(f"- ({c}): {_spread(margins)}" if c != "sequence" else
                     f"- sequence: {_spread(margins)}")  # fmt: skip
    lines += [
        "",
        "Repeat-noise reference: share of splits of B's repeats where a k-repeat mean and the "
        "mean of the remaining repeats disagree on the clause (descriptive, not a test).",
        "",
        "| k | splits | (a) | (b) | (c) | (d) | sequence |",
        "|---|---|---|---|---|---|---|",
    ]
    for k, n in report.noise.items():
        lines.append(
            f"| {k} | {n.n_splits} | "
            + " | ".join(_num(n.flip_fraction[c], 2) for c in CLAUSES)
            + " |"
        )
    if not report.noise:
        lines.append("| n/a | 0 | | | | | |")
    lines += [
        "",
        "## Do the recommendations follow from the scores?",
        "",
        "Repeat mean per cell. Leaders: the top-scoring policy on each durability composite. "
        "Stage follows: the stage's sole leader is the policy the paper recommends there "
        "(Mild: UI or EITC; Moderate: NIT; Full: UBC). Outside the sequence: leaders that are not "
        "UI, EITC, NIT or UBC. In published Table 4 the Mild leader is NIT and the Moderate and "
        "Scenario Durability leader is UBS, so the paper's own scores do not single out its "
        "Mild and Moderate picks either; UBS leads on durability yet is absent from the sequence.",
        "",
        "| Cell | leaders mild / moderate / full / scenario | stage follows (mild, moderate, "
        "full) | outside the sequence | UBS ranks (mild, moderate, full, scenario) | UBS leads "
        "(runs) |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        c = res.mean.consistency
        outside = sorted({p for ps in c.leaders_outside_sequence.values() for p in ps})
        lines.append(
            f"| {cell} | {' / '.join(_leaders(res.mean, d) for d in DURABILITY_COMPOSITES)} "
            f"| {', '.join(_yes(c.stage_follows[s]) for s in STAGES)} "
            f"| {', '.join(outside) or 'none'} "
            f"| {', '.join(_num(c.ubs_ranks[d]) for d in DURABILITY_COMPOSITES)} "
            f"| {_yes(c.ubs_leads)} ({_count(res.runs, lambda r: r.consistency.ubs_leads)}) |"
        )
    lines += [
        "",
        "NIT is recommended for Moderate (clause c) although the paper reports low public support "
        "for it (net approval +17.1). Political support below, as rated by the panel (rank 1 = "
        "highest).",
        "",
        "| Cell | NIT political support (rank of n) | low | clause (c) | recommended despite low "
        "support (runs) | ALMP Mild rank |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        c = res.mean.consistency
        lines.append(
            f"| {cell} | {_num(c.nit_political_score)} ({_num(c.nit_political_rank)} of "
            f"{c.n_political}) | {_yes(c.nit_low_political)} "
            f"| {_yes(res.mean.clauses['c'].holds)} | {_yes(c.nit_despite_low_political)} "
            f"({_count(res.runs, lambda r: r.consistency.nit_despite_low_political)}) "
            f"| {_num(c.almp_mild_rank)} |"
        )
    lines += _blinding_section(report)
    lines += [
        "",
        "## Correlations with Full Transformation durability",
        "",
        "The paper reports r(public net approval, Full Transformation) = -0.57 (recomputed -0.569 "
        "from Table 4) and r(Readiness, Full Transformation) = -0.51. Net approval is the paper's "
        "fixed survey input"
        + ("." if report.has_approvals else "; not supplied to this run, so n/a.")
        + "",
        "",
        "| Cell | r(approval, Full) mean (single runs) | r(Readiness, Full) mean (single runs) |",
        "|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        lines.append(
            f"| {cell} | {_num(res.mean.r_approval, 2)} "
            f"({_range([r.r_approval for r in res.runs], 2)}) "
            f"| {_num(res.mean.r_readiness, 2)} "
            f"({_range([r.r_readiness for r in res.runs], 2)}) |"
        )
    lines += ["", "## How to read this", "", *HOW_TO_READ, ""]
    return "\n".join(lines)


def _ownership(res: RunResult, policy: str) -> float:
    return res.scores.get(OWNERSHIP, {}).get(policy, math.nan)


def _material(shift: float) -> str:
    if math.isnan(shift):
        return "n/a"
    return "beyond M" if abs(shift) > MATERIALITY_M else "within M"


def _blinding_section(report: RecommendationReport) -> list[str]:
    results = report.results
    b = results[BASELINE_CELL]
    lines = [
        "",
        "## Blinding policy names: UBC versus Sovereign AI Fund on Ownership of Gains",
        "",
        f"Gap = UBC minus Sovereign AI Fund / Dividend (SAWF) on Ownership of Gains (published "
        f"94.9 - 54.9 = 40.0). Q1 removes the policy names (description only). Shifts of a "
        f"single policy are set against the materiality margin M = {_num(MATERIALITY_M)} points "
        f"(prereg s6).",
        "",
    ]
    q1 = results.get(BLINDED_CELL)
    if q1 is None:
        lines += [f"Cell {BLINDED_CELL} is not in the store (not run), so blinding cannot be "
                  "assessed.", ""]  # fmt: skip
    else:
        ref = q1.reference
        change = q1.mean.gap - ref.gap
        ubc = _ownership(q1.mean, "ubc") - _ownership(ref, "ubc")
        sawf = _ownership(q1.mean, "sawf") - _ownership(ref, "sawf")
        split = report.noise.get(q1.n_repeats)
        band = _range(split.gap_differences) if split else "n/a"
        lines += [
            f"- B: gap {_num(ref.gap)} (repeat mean on the shared set); single runs "
            f"{_range([r.gap for r in b.runs])}.",
            f"- Q1: gap {_num(q1.mean.gap)}; single runs {_range([r.gap for r in q1.runs])}.",
            f"- Change in the gap: {_num(change)} points. UBC moves {_num(ubc)} "
            f"({_material(ubc)}), SAWF {_num(sawf)} ({_material(sawf)}).",
            f"- Repeat-noise reference for the change (k = {q1.n_repeats}-repeat mean of B minus "
            f"the rest, over every split): {band}.",
            f"- Clause (b) in Q1: {_yes(q1.mean.clauses['b'].holds)} (margin "
            f"{_num(q1.mean.clauses['b'].margin)}); "
            f"{'FLIP' if q1.mean_flipped('b') else 'same'} against B; single runs flipped "
            f"{q1.flip_count('b')}/{len(q1.runs)}.",
            "",
        ]
    lines += [
        "The same gap in every cell (whole range):",
        "",
        "| Cell | gap mean | change vs B | single-run gaps | UBC | SAWF |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        res = results[cell]
        change = "(reference)" if cell == BASELINE_CELL else _num(res.mean.gap - res.reference.gap)
        lines.append(
            f"| {cell} | {_num(res.mean.gap)} | {change} | {_range([r.gap for r in res.runs])} "
            f"| {_num(_ownership(res.mean, 'ubc'))} | {_num(_ownership(res.mean, 'sawf'))} |"
        )
    changes = [results[c].mean.gap - results[c].reference.gap
               for c in report.cell_order if c != BASELINE_CELL]  # fmt: skip
    lines += ["", f"- Gap change across all cells other than B, min / median / max: "
              f"{_spread(changes)}."]  # fmt: skip
    return lines


def _csv(header: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def _cell(value: float) -> str:
    return "" if math.isnan(value) else f"{value:.4f}"


def _flag(value: bool | None) -> str:
    return "" if value is None else str(value)


def _runs(res: CellRecommendations) -> list[tuple[str, RunResult]]:
    return [("reference", res.reference), ("mean", res.mean),
            *((str(i), r) for i, r in enumerate(res.runs))]  # fmt: skip


def render_clauses_csv(report: RecommendationReport) -> str:
    rows = []
    for cell in report.cell_order:
        res = report.results.get(cell)
        if res is None:
            continue
        for c in CLAUSES:
            ref = res.reference.clauses[c].holds
            for run, r in _runs(res):
                holds = r.clauses[c].holds
                flipped = None if run == "reference" or ref is None or holds is None else (
                    holds != ref)  # fmt: skip
                rows.append([cell, run, c, _flag(holds), _cell(r.clauses[c].margin),
                             _flag(ref), _flag(flipped)])  # fmt: skip
    header = ["cell_id", "run", "clause", "holds", "margin", "b_holds", "flipped"]
    return _csv(header, rows)


def render_consistency_csv(report: RecommendationReport) -> str:
    rows = []
    for cell in report.cell_order:
        res = report.results.get(cell)
        if res is None:
            continue
        for run, r in _runs(res):
            c = r.consistency
            rows.append([
                cell, run, *(";".join(c.leaders[d]) for d in DURABILITY_COMPOSITES),
                *(_flag(c.stage_follows[s]) for s in STAGES),
                *(_cell(c.ubs_ranks[d]) for d in DURABILITY_COMPOSITES), _flag(c.ubs_leads),
                _cell(c.nit_political_score), _cell(c.nit_political_rank), c.n_political,
                _flag(c.nit_low_political), _flag(c.nit_despite_low_political),
                _cell(c.almp_mild_rank), _cell(r.r_approval), _cell(r.r_readiness),
            ])  # fmt: skip
    header = ["cell_id", "run", *(f"leaders_{d}" for d in DURABILITY_COMPOSITES),
              *(f"stage_follows_{s}" for s in STAGES), *(f"ubs_rank_{d}" for d in
              DURABILITY_COMPOSITES), "ubs_leads", "nit_political_score", "nit_political_rank",
              "n_political", "nit_low_political", "nit_despite_low_political", "almp_mild_rank",
              "r_approval_full", "r_readiness_full"]  # fmt: skip
    return _csv(header, rows)


def render_blinding_csv(report: RecommendationReport) -> str:
    rows = []
    for cell in report.cell_order:
        res = report.results.get(cell)
        if res is None:
            continue
        for run, r in _runs(res):
            change = math.nan if run == "reference" else r.gap - res.reference.gap
            rows.append([cell, run, _cell(r.gap), _cell(_ownership(r, "ubc")),
                         _cell(_ownership(r, "sawf")), _cell(res.reference.gap),
                         _cell(change)])  # fmt: skip
    header = ["cell_id", "run", "gap", "ubc_ownership", "sawf_ownership", "b_gap", "change_vs_b"]
    return _csv(header, rows)


def render_noise_csv(report: RecommendationReport) -> str:
    rows = []
    for k, n in report.noise.items():
        lo = _cell(min(n.gap_differences)) if n.gap_differences else ""
        hi = _cell(max(n.gap_differences)) if n.gap_differences else ""
        for c in CLAUSES:
            rows.append([k, n.n_splits, c, _cell(n.flip_fraction[c]), lo, hi])
    header = ["k", "n_splits", "clause", "flip_fraction", "gap_change_min", "gap_change_max"]
    return _csv(header, rows)
