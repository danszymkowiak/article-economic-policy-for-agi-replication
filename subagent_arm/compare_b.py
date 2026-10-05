"""Claude arm versus the main arm's baseline B (TASK-35; prereg s9a comparisons 1 and 2). Separate,
labeled arm, never pooled. Descriptive only, no inference language.

Pure functions over parsed ratings (`Observation`: repeat, persona, policy, criterion, score).
Claude's repeat 0 is pass 1 (every policy); its later repeats are the UBC-only passes. Both models
are compared on the persona x policy x criterion keys present in every B repeat and in Claude's
pass 1, so panel means cover the same raters.

- Between models: policy x criterion panel means of Claude's pass 1 against B's repeat mean, units
  with |shift| > M = 5 (Table 4 criteria; the two added criteria separately). Reference: each B
  repeat against the mean of the other B repeats (what one run of the same model does), since
  Claude's pass 1 is one run.
- UBC: B's repeat mean and SD across its repeats beside Claude's per-pass means and SD.
- Clauses (a)-(d) for B's repeat mean and Claude's pass 1; (a) and (b) per Claude pass with that
  pass's UBC means and pass 1's means for the other policies (prereg s9a). Kendall tau-b per
  composite, Claude pass 1 against B.
- Distribution of single ratings per criterion: B's first repeat against Claude's pass 1.
"""

# ruff: noqa: E501  (long report-text string literals, as report.py)
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    Observation,
    composite_scores,
    kendall_tau_b,
)
from llm_panel.domain.analysis_recommend import MATERIALITY_M, ClauseResult, evaluate_clauses

UBC = "ubc"
Key = tuple[str, str, str]  # persona, policy, criterion
Means = dict[tuple[str, str], float]  # (policy, criterion) -> panel mean


def panel_means(obs: Iterable[Observation], keys: set[Key] | None = None) -> Means:
    """Per repeat, the mean over personas; then the mean over the repeats present."""
    per: dict[tuple[str, str], dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for o in obs:
        if keys is None or (o.persona_id, o.policy_id, o.criterion_id) in keys:
            per[(o.policy_id, o.criterion_id)][o.repeat].append(o.score)
    return {
        k: statistics.fmean(statistics.fmean(v) for v in reps.values()) for k, reps in per.items()
    }


def _repeat_means(obs: Iterable[Observation], keys: set[Key]) -> dict[int, Means]:
    by: dict[int, list[Observation]] = defaultdict(list)
    for o in obs:
        by[o.repeat].append(o)
    return {r: panel_means(v, keys) for r, v in sorted(by.items())}


def shared_keys(b: Iterable[Observation], claude: Iterable[Observation]) -> set[Key]:
    """Keys present in every B repeat and in Claude's pass 1."""
    b = list(b)
    repeats = {o.repeat for o in b}
    seen: dict[Key, set[int]] = defaultdict(set)
    for o in b:
        seen[(o.persona_id, o.policy_id, o.criterion_id)].add(o.repeat)
    claude = list(claude)
    first = min(o.repeat for o in claude)
    c_keys = {(o.persona_id, o.policy_id, o.criterion_id) for o in claude if o.repeat == first}
    return {k for k, r in seen.items() if r == repeats} & c_keys


@dataclass(frozen=True)
class Unit:
    policy: str
    criterion: str
    shift: float


def units_beyond(ref: Mapping, other: Mapping, m: float = MATERIALITY_M) -> list[Unit]:
    out = [Unit(p, c, other[(p, c)] - ref[(p, c)]) for (p, c) in sorted(set(ref) & set(other))]
    return sorted((u for u in out if abs(u.shift) > m), key=lambda u: -abs(u.shift))


def _table4(units: list[Unit]) -> list[Unit]:
    return [u for u in units if u.criterion in TABLE4_CRITERIA]


def b_single_run_counts(b: Iterable[Observation], keys: set[Key]) -> list[int]:
    """Per B repeat: Table 4 units whose single-run panel mean differs from the mean of the other
    repeats by more than M."""
    runs = _repeat_means(b, keys)
    out = []
    for r, single in runs.items():
        rest = [v for q, v in runs.items() if q != r]
        others = {k: statistics.fmean(x[k] for x in rest) for k in single}
        out.append(len(_table4(units_beyond(others, single))))
    return out


def _scores(means: Means) -> dict[str, dict[str, float]]:
    by: dict[str, dict[str, float]] = defaultdict(dict)
    for (p, c), v in means.items():
        by[c][p] = v
    return composite_scores(by)


@dataclass(frozen=True)
class UbcRow:
    criterion: str
    b_mean: float
    b_sd: float  # SD of B's single-repeat panel means
    claude_passes: tuple[float, ...]
    claude_mean: float
    claude_sd: float  # NaN with one pass


@dataclass(frozen=True)
class DistRow:
    criterion: str
    b_mean: float
    b_sd: float
    b_share_mult5: float
    claude_mean: float
    claude_sd: float
    claude_share_mult5: float


@dataclass(frozen=True)
class ModelComparison:
    n_keys: int
    n_personas: int
    beyond_m_table4: list[tuple[str, str, float]]
    beyond_m_added: list[tuple[str, str, float]]
    n_table4_units: int
    b_single_runs: list[int]  # reference: per B repeat, Table 4 units beyond M against the rest
    ubc_rows: list[UbcRow]
    clauses_b: dict[str, ClauseResult]
    clauses_claude: dict[str, ClauseResult]
    clauses_per_pass: list[dict[str, ClauseResult]]  # (a), (b) with each pass's UBC
    taus: dict[str, float]
    distribution: list[DistRow]


def _sd(xs: list[float]) -> float:
    return statistics.stdev(xs) if len(xs) > 1 else math.nan


def _dist(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    mult5 = sum(1 for v in values if v % 5 == 0) / len(values)
    return statistics.fmean(values), _sd(values), mult5


def compare_models(b: list[Observation], claude: list[Observation]) -> ModelComparison:
    keys = shared_keys(b, claude)
    b_mean = panel_means(b, keys)
    passes = sorted({o.repeat for o in claude})
    first = passes[0]
    c_runs = {
        r: panel_means([o for o in claude if o.repeat == r], keys if r == first else None)
        for r in passes
    }
    c1 = c_runs[first]
    units = units_beyond(b_mean, c1)
    b_runs = _repeat_means(b, keys)

    ubc_rows = []
    for c in sorted({c for p, c in b_mean if p == UBC}, key=_criterion_order):
        b_vals = [run[(UBC, c)] for run in b_runs.values() if (UBC, c) in run]
        c_vals = [c_runs[r][(UBC, c)] for r in passes if (UBC, c) in c_runs[r]]
        ubc_rows.append(UbcRow(c, b_mean[(UBC, c)], _sd(b_vals), tuple(c_vals),
                               statistics.fmean(c_vals), _sd(c_vals)))  # fmt: skip

    per_pass = []
    for r in passes:
        mixed = dict(c1)
        mixed.update({k: v for k, v in c_runs[r].items() if k[0] == UBC})
        res = evaluate_clauses(_scores(mixed))
        per_pass.append({k: res[k] for k in ("a", "b")})

    sb, sc = _scores(b_mean), _scores(c1)
    taus = {}
    for comp in COMPOSITES:
        pols = sorted(set(sb.get(comp, {})) & set(sc.get(comp, {})))
        tau = kendall_tau_b([sb[comp][p] for p in pols], [sc[comp][p] for p in pols])
        taus[comp] = math.nan if tau is None else tau

    b_first = min(o.repeat for o in b)
    dist = []
    for c in sorted({o.criterion_id for o in b}, key=_criterion_order):
        bm = _dist([o.score for o in b if o.repeat == b_first and o.criterion_id == c])
        cm = _dist([o.score for o in claude if o.repeat == first and o.criterion_id == c])
        dist.append(DistRow(c, *bm, *cm))

    return ModelComparison(
        n_keys=len(keys),
        n_personas=len({k[0] for k in keys}),
        beyond_m_table4=[(u.policy, u.criterion, u.shift) for u in _table4(units)],
        beyond_m_added=[
            (u.policy, u.criterion, u.shift) for u in units if u.criterion not in TABLE4_CRITERIA
        ],  # fmt: skip
        n_table4_units=sum(1 for _, c in b_mean if c in TABLE4_CRITERIA),
        b_single_runs=b_single_run_counts(b, keys),
        ubc_rows=ubc_rows,
        clauses_b=evaluate_clauses(sb),
        clauses_claude=evaluate_clauses(sc),
        clauses_per_pass=per_pass,
        taus=taus,
        distribution=dist,
    )


def _criterion_order(c: str) -> tuple[int, str]:
    return (TABLE4_CRITERIA.index(c) if c in TABLE4_CRITERIA else len(TABLE4_CRITERIA), c)


# --- rendering (pure) and the thin shell -------------------------------------------------------

HEADER = "# Claude subagent arm versus the main arm's B (separate arm, not pooled)"


def _n(x: float, d: int = 1) -> str:
    return "n/a" if x is None or math.isnan(x) else f"{x:.{d}f}"


def _clause(res: ClauseResult) -> str:
    return "n/a" if res.holds is None else f"{'holds' if res.holds else 'fails'} ({res.margin:.1f})"


def render_markdown(res: ModelComparison) -> str:
    from llm_panel.domain.analysis_recommend import CLAUSE_TEXT, CLAUSES

    single = res.b_single_runs
    out = [
        HEADER,
        "",
        "**Separate, labeled arm (prereg s9a).** Claude Haiku 4.5 as Claude Code subagents against "
        "glm-5.3-flash's baseline B on the same rendered prompts. A difference is a difference "
        "between two model-and-harness bundles (model, agentic wrapper, line reply format, "
        "uncontrolled sampling), not a clean model effect: it shows that scores depend on which "
        "model is used, not that either is right. Descriptive only. Instability of scores shows "
        "they lack the claimed precision, not that the recommendations are wrong.",
        "",
        f"- Compared on {res.n_keys} persona x policy x criterion keys ({res.n_personas} personas) "
        "present in every B repeat and in Claude's pass 1. B: repeat mean of its 5 repeats; "
        "Claude: pass 1 (one run) unless stated.",
        "",
        "## Between models: panel means shifted by more than M = 5",
        "",
        f"- Table 4 units (policy x criterion, {res.n_table4_units}): **{len(res.beyond_m_table4)}** "
        "beyond M = 5 between Claude pass 1 and B.",
        f"- Reference, what one run of the same model does: each B repeat against the mean of the "
        f"other four, units beyond M = 5: {', '.join(str(x) for x in single)} "
        f"(min {min(single)}, max {max(single)}).",
        f"- Added criteria (Political Support, Administrative Capacity and Speed; descriptive, not "
        f"in the count): {len(res.beyond_m_added)} beyond M.",
        "",
        "Largest Table 4 shifts (Claude - B):",
        "",
        "; ".join(f"{p} x {c} {s:+.1f}" for p, c, s in res.beyond_m_table4[:20]) or "none",
        "",
        "## UBC: between-model shift beside each model's repeat noise",
        "",
        "| criterion | B mean | B SD (5 runs) | Claude passes | Claude mean | Claude SD (3 passes) "
        "| shift (Claude mean - B) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in res.ubc_rows:
        passes = " / ".join(_n(x) for x in r.claude_passes)
        out.append(f"| {r.criterion} | {_n(r.b_mean)} | {_n(r.b_sd, 2)} | {passes} | "
                   f"{_n(r.claude_mean)} | {_n(r.claude_sd, 2)} | {r.claude_mean - r.b_mean:+.1f} |")  # fmt: skip
    out += [
        "",
        "## Recommendation clauses",
        "",
        "Holds or fails with its margin (prereg s6). Claude per pass: (a) and (b) with that pass's "
        "UBC means and pass 1's means for the other policies.",
        "",
        "| clause | B (repeat mean) | Claude pass 1 | "
        + " | ".join(f"Claude UBC pass {i + 1}" for i in range(len(res.clauses_per_pass)))
        + " |",
        "|---|---|---|" + "---|" * len(res.clauses_per_pass),
    ]
    for cl in CLAUSES:
        per = [(_clause(p[cl]) if cl in p else "") for p in res.clauses_per_pass]
        out.append(f"| ({cl}) {CLAUSE_TEXT[cl]} | {_clause(res.clauses_b[cl])} | "
                   f"{_clause(res.clauses_claude[cl])} | " + " | ".join(per) + " |")  # fmt: skip
    out += ["", "## Ranks: Kendall tau-b, Claude pass 1 against B", "",
            "| composite | tau-b |", "|---|---|"]  # fmt: skip
    out += [f"| {c} | {_n(t, 2)} |" for c, t in res.taus.items()]
    out += [
        "",
        "B's own repeat-noise taus are in `analysis/ranks/rank_stability.md` (pairwise minimum "
        "0.88 to 0.96 by composite).",
        "",
        "## Distribution of single ratings (B repeat 1 against Claude pass 1)",
        "",
        "| criterion | B mean | B SD | B % mult. of 5 | Claude mean | Claude SD | Claude % mult. of 5 |",
        "|---|---|---|---|---|---|---|",
    ]
    for d in res.distribution:
        out.append(f"| {d.criterion} | {_n(d.b_mean)} | {_n(d.b_sd)} | {d.b_share_mult5:.0%} | "
                   f"{_n(d.claude_mean)} | {_n(d.claude_sd)} | {d.claude_share_mult5:.0%} |")  # fmt: skip
    return "\n".join(out) + "\n"


def main() -> int:  # pragma: no cover - thin shell
    from pathlib import Path

    from llm_panel.adapters.jsonl import JsonlResultStore
    from llm_panel.application.baseline_comparison import BASELINE_CELL, cell_observations

    root = Path(__file__).resolve().parent.parent
    b, _ = cell_observations(JsonlResultStore(root / "results/raw/rows.jsonl"))[BASELINE_CELL]
    c, _ = cell_observations(JsonlResultStore(root / "subagent_arm/results/rows.jsonl"))[
        BASELINE_CELL
    ]
    out = root / "subagent_arm/reports/claude_vs_b.md"
    out.write_text(render_markdown(compare_models(b, c)), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
