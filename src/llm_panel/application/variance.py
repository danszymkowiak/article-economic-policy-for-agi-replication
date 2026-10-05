"""Variance decomposition (TASK-20): read every cell from the raw store, decompose within cells,
set each varied factor against B's repeat noise, render the report. Descriptive (prereg s6)."""

from __future__ import annotations

import csv
import io
import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from llm_panel.application.baseline_comparison import (
    BASELINE_CELL,
    COUNT_HEADER,
    COUNT_NOTE,
    NO_PERSONA_NOTE,
    CellCounts,
    cell_observations,
    is_study_store,
)
from llm_panel.application.rank_stability import report_order
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA
from llm_panel.domain.analysis_rank import CellArray, build_cell_array
from llm_panel.domain.analysis_variance import (
    CellDecomposition,
    CriterionAgreement,
    FactorShift,
    PersonaCell,
    criterion_agreement,
    decompose_cell,
    factor_shift,
    persona_cells,
)

# The one factor each cell changes from B (prereg s5).
FACTORS = {
    "B'": "drift (B repeated at the end)",
    "Q1": "policy identifier (name removed)",
    "Q2a": "description wording", "Q2b": "description wording", "Q2c": "description wording",
    "Q3a": "instruction wording", "Q3b": "instruction wording", "Q3c": "instruction wording",
    "Q4": "evidence packet (none)",
    "R-T0": "temperature", "R-T1": "temperature",
    "D1": "scoring mode (joint)",
    "D2": "persona (none)",
    "D2b": "persona source (synthetic panel)",
    "D3": "model",
}  # fmt: skip


@dataclass(frozen=True)
class VarianceReport:
    counts: dict[str, CellCounts]
    cells: dict[str, CellArray]
    cell_order: list[str]
    decompositions: dict[str, CellDecomposition]
    persona_cells: dict[str, list[PersonaCell]]  # cells with personas
    agreement: dict[str, list[CriterionAgreement]]
    shifts: list[FactorShift]  # empty when the store holds no cell B ratings


def rated_criteria(observed: set[str]) -> tuple[str, ...]:
    first = [c for c in TABLE4_CRITERIA if c in observed]
    return (*first, *sorted(observed - set(first)))


def run_variance(store) -> VarianceReport:
    by_cell = cell_observations(store)
    policies = tuple(sorted({o.policy_id for obs, _ in by_cell.values() for o in obs}))
    criteria = rated_criteria({o.criterion_id for obs, _ in by_cell.values() for o in obs})
    counts = {cell: c for cell, (_, c) in by_cell.items()}
    arrays = {
        cell: build_cell_array(cell, obs, policy_ids=policies, criteria=criteria)
        for cell, (obs, _) in by_cell.items()
        if obs
    }
    order = report_order(arrays)
    with_personas = [c for c in order if arrays[c].has_personas]
    shifts = []
    if BASELINE_CELL in arrays:
        b = arrays[BASELINE_CELL]
        shifts = [factor_shift(b, arrays[c]) for c in order if c != BASELINE_CELL]
    return VarianceReport(
        counts=counts, cells=arrays, cell_order=order,
        decompositions={c: decompose_cell(arrays[c]) for c in order},
        persona_cells={c: persona_cells(arrays[c]) for c in with_personas},
        agreement={c: criterion_agreement(arrays[c]) for c in with_personas},
        shifts=shifts,
    )  # fmt: skip


def _num(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None or math.isnan(value) else f"{value:.{digits}f}"


def _pct(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{100 * value:.1f}%"


def _spread(values: Sequence[float], fmt=_num) -> str:
    ok = [v for v in values if not math.isnan(v)]
    if not ok:
        return "n/a"
    return f"{fmt(min(ok))} / {fmt(statistics.median(ok))} / {fmt(max(ok))} (n={len(ok)})"


def _term(key: tuple[str, ...], residual: tuple[str, ...]) -> str:
    name = " x ".join(key)
    return f"{name} (with residual)" if key == residual else name


IDENTIFIABILITY = [
    "- **Identifiable within a cell** (fully crossed persona x policy x criterion x repeat): every "
    "main effect and interaction of those four factors, except that the top interaction is "
    "confounded with residual error. With one repeat, repeat noise is not separable at all: the "
    "persona x policy x criterion term then holds it, and the report flags this.",
    "- **Identifiable per varied factor**: the cell's level shift and its policy x criterion "
    "specific shift against B, each beyond the repeat noise measured in B (and in the cell when it "
    "has two or more repeats). This is a contrast between two configurations, not a variance over "
    "a population of prompts, models or evidence packets: each factor has one alternative level "
    "(Q2 and Q3 three paraphrases), so a factor variance component is not identifiable.",
    "- **Not identifiable**: any interaction between varied factors (e.g. model x evidence, "
    "wording x temperature): the design is one-at-a-time, never factorial, so no two factors are "
    "changed together. The shift of a cell is the whole effect of its one change under B's other "
    "settings; it may differ under other settings. Persona x factor interactions are estimable in "
    "principle for paired cells but are not estimated here (shifts are at panel-mean level).",
    "- D2 (no persona) and D2b (another panel) are not paired with B's personas; their shifts "
    "compare panel means of different raters and mix the factor with who rates.",
]


def render_markdown(report: VarianceReport, store_path: str) -> str:
    lines = ["# Variance decomposition", ""]
    if not is_study_store(store_path):
        lines += [
            f"**NON-INFERENCE DATA.** The store `{store_path}` is not `results/raw` (pilot or "
            "smoketest). These numbers exercise the analysis code only and never enter inference.",
            "",
        ]
    lines += [f"- Store: `{store_path}`.", ""]
    if BASELINE_CELL not in report.cells:
        lines += ["No cell B data in the store, so nothing can be decomposed against B.", ""]
        return "\n".join(lines)
    lines += [
        "## Data",
        "",
        f"| Cell | {COUNT_HEADER} | repeats | personas used | personas dropped | criteria |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        d, cnt = report.decompositions[cell], report.counts[cell]
        lines.append(
            f"| {cell} | {cnt.cells()} | {d.n_repeats} | {d.n_personas} "
            f"| {d.n_personas_dropped} | {d.n_criteria} |"
        )
    lines += ["", f"_{COUNT_NOTE}_"]
    lines += [
        "",
        "Personas enter the within-cell decomposition only when complete in every rated policy x "
        "criterion and repeat (a balanced design); the per policy x criterion and per criterion "
        "analyses use every persona complete there.",
        "",
        "## What the design can and cannot identify",
        "",
        *IDENTIFIABILITY,
        "",
    ]
    b = report.decompositions[BASELINE_CELL]
    lines += ["## Within-cell decomposition, baseline B", ""]
    if b.components is None:
        lines += ["Too few complete levels to decompose B.", ""]
    else:
        comp = b.components
        lines += [
            "Method-of-moments components of a balanced crossed random-effects ANOVA. Negative "
            "raw estimates are shown and count as 0 in shares.",
            "",
            "| Term | df | mean square | component | share |",
            "|---|---|---|---|---|",
        ]
        for key, est in comp.estimates.items():
            lines.append(
                f"| {_term(key, comp.residual_key)} | {comp.dfs[key]} "
                f"| {_num(comp.mean_squares[key])} | {_num(est)} | {_pct(comp.share([key]))} |"
            )
    noise_note = (
        " B has one repeat, so repeat noise is not separable: it sits in the top interaction "
        "term (the persona terms when personas are identified)."
        if b.noise_confounded else ""
    )  # fmt: skip
    pcs = report.persona_cells.get(BASELINE_CELL, [])
    lines += [
        "",
        "## How much variance persona explains",
        "",
        f"- In B, all persona terms without repeat (persona, persona x policy, persona x "
        f"criterion, persona x policy x criterion) take **{_pct(b.persona_share)}** of the "
        f"variance of a single rating; the persona main effect alone {_pct(b.persona_main_share)}"
        f". Repeat noise (every term with repeat) takes {_pct(b.repeat_share)}; the policy and "
        f"criterion structure {_pct(b.structure_share)}.{noise_note}",
        "- Per policy x criterion (persona x repeat decomposition), persona share "
        "sigma2_P / (sigma2_P + sigma2_run + sigma2_residual), min / median / max over cells: "
        f"{_spread([c.persona_share for c in pcs], _pct)}.",
        "",
        "| Cell | persona main | all persona terms | repeat noise | policy/criterion | "
        "per policy x criterion persona share (min / median / max) |",
        "|---|---|---|---|---|---|",
    ]
    for cell in report.cell_order:
        d = report.decompositions[cell]
        per = [c.persona_share for c in report.persona_cells.get(cell, [])]
        flag = " (noise confounded)" if d.noise_confounded else ""
        lines.append(
            f"| {cell} | {_pct(d.persona_main_share)} | {_pct(d.persona_share)}{flag} "
            f"| {_pct(d.repeat_share)} | {_pct(d.structure_share)} | {_spread(per, _pct)} |"
        )
    agreement = report.agreement.get(BASELINE_CELL, [])
    lines += [
        "",
        "## Effective number of independent raters",
        "",
        "Design-effect formula: **n_eff = n / (1 + (n - 1) icc)**, n = personas rated. Two "
        "readings of icc, both from the decompositions above; the run-shared one is primary and "
        "the agreement one secondary (prereg s6, s10):",
        "",
        "- *Run-shared, PRIMARY* (per policy x criterion cell; persona x repeat decomposition): "
        "icc_run = sigma2_run / (sigma2_P + sigma2_run + sigma2_residual), the correlation of two "
        "personas' ratings within one run. Its complement is the persona share plus the "
        "persona-specific noise share. It needs two or more repeats.",
        "- *Agreement, secondary* (per criterion; persona x policy x repeat decomposition): "
        "icc_agree = (sigma2_policy + sigma2_policy x run) / (that + sigma2_persona x policy + "
        "sigma2_residual), the correlation of two personas' single-run ratings across policies. "
        "Its complement is the persona x policy (persona-specific view) share plus noise; near 1 "
        "means the panel behaves as one model (prereg H4).",
        "",
        f"- B, run-shared n_eff over policy x criterion cells, min / median / max: "
        f"{_spread([c.n_eff_run for c in pcs], lambda v: _num(v, 1))}; icc_run "
        f"{_spread([c.icc_run for c in pcs])}.",
        "",
        "| Criterion (B) | personas | policies | icc_agree | persona x policy share | n_eff |",
        "|---|---|---|---|---|---|",
    ]
    for a in agreement:
        flag = " (noise confounded)" if a.noise_confounded else ""
        lines.append(
            f"| {a.criterion} | {a.n_personas} | {a.n_policies} | {_num(a.icc_agree)} "
            f"| {_pct(a.persona_policy_share)}{flag} | {_num(a.n_eff_agree, 1)} |"
        )
    lines += [
        "",
        f"- Agreement n_eff over criteria, min / median / max: "
        f"{_spread([a.n_eff_agree for a in agreement], lambda v: _num(v, 1))}.",
        "",
        "## Varied factors against repeat noise (one-at-a-time, versus B)",
        "",
        "Units are policy x criterion panel means. Level shift: mean of cell - B, with its "
        "repeat-noise SE. Shift SD: SD of the unit-specific shift beyond repeat noise (0 when the "
        "estimate is negative). Ratio: that variance over B's single-run panel-mean noise "
        "variance (raw, may be negative); band: the same ratio over every split of B's repeats "
        "into the cell's repeat count and the rest (descriptive, not a test; n/a when the cell "
        "has as many repeats as B or more).",
        "",
        "| Cell | factor | pairing | units | repeats | level shift (SE) | shift SD | ratio to "
        "noise | B split band | noise |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for f in report.shifts:
        band = f"{_num(min(f.band))} to {_num(max(f.band))}" if f.band else "n/a"
        lines.append(
            f"| {f.cell_id} | {FACTORS.get(f.cell_id, '?')} | {f.pairing} | {f.n_units} "
            f"| {f.k_cell} | {_num(f.level_shift)} ({_num(f.level_se)}) | {_num(f.shift_sd)} "
            f"| {_num(f.ratio_to_noise)} | {band} | {f.noise_source} |"
        )
    lines += [
        "",
        "## How to read this",
        "",
        NO_PERSONA_NOTE,
        "- Descriptive and unthresholded (prereg s6: variance decomposition is a secondary "
        "descriptive). Every cell and every policy x criterion is reported; the CSV files hold "
        "the full tables.",
        "- Instability of the scores, where present, shows they lack the claimed precision, not "
        "that the recommendations are wrong.",
        "- Policy and criterion are fixed in the design; their components are the variance of "
        "their effects (divisor n - 1), read descriptively. The 51 personas are the fixed "
        "inference target (prereg s3); the persona share describes how much they differ, not a "
        "sample of economists.",
        "- Noise column: 'own' when the cell has two or more repeats; 'B' when a one-repeat cell "
        "borrows B's noise (assumes equal noise).",
        "- Block D cells change the design, not a small detail, and are read separately from "
        "blocks R and Q (prereg s5).",
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


def render_components_csv(report: VarianceReport) -> str:
    rows = []
    for cell in report.cell_order:
        comp = report.decompositions[cell].components
        if comp is None:
            continue
        for key, est in comp.estimates.items():
            rows.append([cell, " x ".join(key), key == comp.residual_key, comp.dfs[key],
                         _cell(comp.mean_squares[key]), _cell(est),
                         _cell(comp.share([key]))])  # fmt: skip
    header = ["cell_id", "term", "with_residual", "df", "mean_square", "estimate", "share"]
    return _csv(header, rows)


def render_persona_cells_csv(report: VarianceReport) -> str:
    rows = [
        [cell, c.policy_id, c.criterion, c.n_personas, c.n_repeats, _cell(c.var_persona),
         _cell(c.var_run), _cell(c.var_residual), _cell(c.persona_share), _cell(c.icc_run),
         _cell(c.n_eff_run)]
        for cell, cells in report.persona_cells.items()
        for c in cells
    ]  # fmt: skip
    header = ["cell_id", "policy_id", "criterion", "n_personas", "n_repeats", "var_persona",
              "var_run", "var_residual", "persona_share", "icc_run", "n_eff_run"]  # fmt: skip
    return _csv(header, rows)


def render_agreement_csv(report: VarianceReport) -> str:
    rows = [
        [cell, a.criterion, a.n_personas, a.n_policies, a.n_repeats, _cell(a.icc_agree),
         _cell(a.persona_policy_share), _cell(a.n_eff_agree), a.noise_confounded]
        for cell, items in report.agreement.items()
        for a in items
    ]  # fmt: skip
    header = ["cell_id", "criterion", "n_personas", "n_policies", "n_repeats", "icc_agree",
              "persona_policy_share", "n_eff_agree", "noise_confounded"]  # fmt: skip
    return _csv(header, rows)


def render_shifts_csv(report: VarianceReport) -> str:
    rows = [
        [f.cell_id, FACTORS.get(f.cell_id, ""), f.pairing, f.n_units, f.k_b, f.k_cell,
         _cell(f.level_shift), _cell(f.level_se), _cell(f.shift_var), _cell(f.shift_sd),
         _cell(f.noise_var_b), _cell(f.noise_var_cell), f.noise_source, _cell(f.ratio_to_noise),
         _cell(f.share_vs_noise), _cell(min(f.band)) if f.band else "",
         _cell(max(f.band)) if f.band else "", len(f.band)]
        for f in report.shifts
    ]  # fmt: skip
    header = ["cell_id", "factor", "pairing", "n_units", "k_b", "k_cell", "level_shift",
              "level_se", "shift_var", "shift_sd", "noise_var_b", "noise_var_cell",
              "noise_source", "ratio_to_noise", "share_vs_noise", "band_min", "band_max",
              "n_band_splits"]  # fmt: skip
    return _csv(header, rows)
