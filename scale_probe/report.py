"""EXPLORATORY reversed-scale probe (TASK-38): markdown report. Pure rendering."""

from __future__ import annotations

import math

from llm_panel.domain.analysis_baseline import COMPOSITES
from llm_panel.domain.analysis_recommend import CLAUSE_TEXT, CLAUSES
from scale_probe.analysis import CALL_CLASSES, Agreement, Comparison
from scale_probe.probe import ProbeState

HEADER = "# EXPLORATORY: reversed-scale probe — not pooled with the main analysis"
REVERSED, RERUN, KEPT = (
    "reversed, converted (100 - x)",
    "baseline rerun (noise)",
    ("reversed, without unconverted calls"),
)


def _num(x: float, digits: int = 2) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def _agree(a: Agreement) -> str:
    return f"{a.n} | {_num(a.r)} | {_num(a.mean_signed, 1)} | {_num(a.mean_abs, 1)}"


def _rows(state: ProbeState) -> list[tuple[str, Comparison]]:
    r = state.result
    rows = [(REVERSED, r.reversed), (RERUN, r.rerun)]
    if r.converted_only is not None:
        rows.append((KEPT, r.converted_only))
    return rows


def render_markdown(
    state: ProbeState, store_label: str, adversarial_label: str, ceiling: float
) -> str:
    out = [
        HEADER,
        "",
        "Exploratory, post-freeze (prereg s13, TASK-38). Not part of the preregistered analysis, "
        "not pooled with it or with the adversarial arm. B's persona x policy prompt with one "
        "sentence changed so that 0 is best and 100 is worst; raw scores are converted with "
        "100 - x before comparison. Search panel, seed, model and every other setting are the "
        "adversarial arm's baseline run, which is the comparison; the arm's rerun at another seed "
        "is the repeat-noise reference. Instability of scores shows they lack the claimed "
        "precision, not that the recommendations are wrong.",
        "",
        f"- Probe store: `{store_label}` (ceiling {ceiling:.2f} USD); comparison runs read from "
        f"`{adversarial_label}` (read-only).",
        f"- Status: {state.status}. Search panel: {state.panel_size} personas; probe jobs "
        f"{len(state.jobs)}, ratings {len(state.probe.ratings)}, failed {state.probe.failed}; "
        f"baseline failed {state.baseline.failed}, rerun failed {state.rerun.failed}.",
        "",
    ]
    if state.result is None:
        out.append(
            "Results pending: the probe or the adversarial baseline and rerun are not complete."
        )
        return "\n".join(out) + "\n"
    r = state.result
    out += [
        f"target policy: {r.target} (top on Full Transformation in the adversarial baseline run)",
        "",
        "## Did the model follow the reversed scale?",
        "",
        "Each reversed call against the same persona x policy baseline call: unconverted when its "
        "raw mean is nearer the baseline mean than 100 minus it; undecidable when the baseline "
        "mean is within 5 of 50.",
        "",
        "| call class | calls |",
        "|---|---|",
        *[f"| {c} | {r.calls[c]} |" for c in CALL_CLASSES],
        "",
        f"Raw (unconverted) reversed ratings against the baseline: n {r.raw.n}, r {_num(r.raw.r)} "
        "(a faithful mirror gives r near -1).",
        "",
        "## Agreement with the baseline run",
        "",
        "Signed difference = run minus baseline. Panel means are policy x criterion means over the "
        "search panel, all 13 criteria.",
        "",
        "| run | level | n | r | mean signed diff | mean abs diff |",
        "|---|---|---|---|---|---|",
    ]
    for label, c in _rows(state):
        out.append(f"| {label} | single ratings | {_agree(c.rating)} |")
        out.append(f"| {label} | panel means | {_agree(c.panel)} |")
    out += [
        "",
        "## Ranks, materiality and clauses",
        "",
        "Beyond M: Table 4 policy x criterion panel means with |shift from the baseline| > 5. "
        "Target rank on Full Transformation in the run (1 = highest).",
        "",
        "| run | target rank | beyond M = 5 | min tau | median tau |",
        "|---|---|---|---|---|",
    ]
    for label, c in _rows(state):
        taus = sorted(t for t in c.taus.values() if not math.isnan(t))
        mid = taus[len(taus) // 2] if taus else math.nan
        out.append(
            f"| {label} | {r.target} rank {_num(c.target_rank, 1)} | {len(c.beyond_m)} | "
            f"{_num(taus[0] if taus else math.nan)} | {_num(mid)} |"
        )
    out += ["", "Kendall tau-b against the baseline run, per composite:", "",
            "| composite | " + " | ".join(label for label, _ in _rows(state)) + " |",
            "|---|" + "---|" * len(_rows(state))]  # fmt: skip
    for comp in COMPOSITES:
        out.append(f"| {comp} | " + " | ".join(_num(c.taus[comp]) for _, c in _rows(state)) + " |")
    out += ["", "Clauses in each run (holds, margin); on a 5-persona panel, descriptive only:", "",
            "| clause | " + " | ".join(label for label, _ in _rows(state)) + " |",
            "|---|" + "---|" * len(_rows(state))]  # fmt: skip
    for cl in CLAUSES:
        cells = []
        for _, c in _rows(state):
            res = c.clauses[cl]
            cells.append(
                "n/a" if res.holds is None else f"{'yes' if res.holds else 'no'} ({res.margin:.1f})"
            )
        out.append(f"| ({cl}) {CLAUSE_TEXT[cl]} | " + " | ".join(cells) + " |")
    out += ["", "## Units beyond M = 5", ""]
    for label, c in _rows(state):
        units = "; ".join(f"{u.policy} x {u.criterion} {u.shift:+.1f}" for u in c.beyond_m)
        out.append(f"- {label}: {units or 'none'}.")
    out += [
        "",
        "## How to read this",
        "",
        "- One run of 5 personas per condition: a probe of the response scale, not an estimate of "
        "the panel's stability. Compare every row with the rerun row, which changes only the seed.",
        "- A shift after conversion mixes three things the probe cannot separate: calls that "
        "ignored the reversal, an asymmetric response to a reversed scale (e.g. avoiding 0), and "
        "ordinary run-to-run noise.",
        "- The probe's prompts use the adversarial arm's settings, including its max_tokens cap "
        "(600 per rating), which differ from study cell B's (400).",
    ]
    return "\n".join(out) + "\n"
