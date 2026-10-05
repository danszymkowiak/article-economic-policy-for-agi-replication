"""EXPLORATORY reversed-scale probe (TASK-38; prereg s13): the analysis. Pure, descriptive.

Ratings are keyed (persona, policy, criterion). The reversed run asked for 0 = best and 100 = worst,
so its raw scores are converted with 100 - x before any comparison. Every quantity is computed for
the converted reversed run against the baseline run and, as the repeat-noise reference, for the
baseline rerun (another seed, nothing else changed) against the same baseline:

- agreement of single ratings and of policy x criterion panel means: Pearson r, mean signed
  difference (other - baseline) and mean absolute difference, paired on the keys both runs share;
- Table 4 policy x criterion panel means whose |shift| exceeds M = 5 (prereg s6);
- Kendall tau-b per composite, the target's rank on Full Transformation, clauses (a)-(d).

Each reversed call is classified by its mean against the matching baseline call's mean m_b:
"unconverted" when the raw mean is nearer m_b (the model kept 100 = best) than 100 - m_b,
"converted" otherwise, and "undecidable" when |m_b - 50| < 5 (the two readings lie within 10
points). Comparisons are repeated without the unconverted calls (secondary).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    kendall_tau_b,
    pearson,
)
from llm_panel.domain.analysis_rank import descending_ranks
from llm_panel.domain.analysis_recommend import (
    FULL,
    MATERIALITY_M,
    ClauseResult,
    evaluate_clauses,
)

Key = tuple[str, str, str]  # persona, policy, criterion
Ratings = Mapping[Key, float]

CONVERTED, UNCONVERTED, UNDECIDABLE = "converted", "unconverted", "undecidable"
CALL_CLASSES = (CONVERTED, UNCONVERTED, UNDECIDABLE)
UNDECIDABLE_BAND = 5.0  # |baseline call mean - 50| below this: the two readings are too close


def convert(score: float) -> float:
    """A reversed-scale score (0 = best) on the study's scale (100 = best)."""
    return 100.0 - score


def classify_call(raw: Sequence[float], base: Sequence[float]) -> str:
    """One reversed call's raw scores against the same persona x policy baseline call."""
    m_r, m_b = sum(raw) / len(raw), sum(base) / len(base)
    if abs(m_b - 50.0) < UNDECIDABLE_BAND:
        return UNDECIDABLE
    return UNCONVERTED if abs(m_r - m_b) < abs(m_r - convert(m_b)) else CONVERTED


@dataclass(frozen=True)
class Agreement:
    n: int
    r: float  # NaN when undefined
    mean_signed: float  # other - reference
    mean_abs: float


def agreement(ref: Mapping, other: Mapping) -> Agreement:
    keys = sorted(set(ref) & set(other))
    if not keys:
        return Agreement(0, math.nan, math.nan, math.nan)
    x, y = [ref[k] for k in keys], [other[k] for k in keys]
    r = pearson(x, y) if len(keys) > 1 else None
    diffs = [b - a for a, b in zip(x, y, strict=True)]
    return Agreement(
        len(keys),
        math.nan if r is None else r,
        sum(diffs) / len(diffs),
        sum(abs(d) for d in diffs) / len(diffs),
    )


def _panel_means(ratings: Ratings) -> dict[tuple[str, str], float]:
    """(policy, criterion) -> unweighted mean over the personas present."""
    acc: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (_, policy, criterion), score in ratings.items():
        acc[(policy, criterion)].append(score)
    return {k: sum(v) / len(v) for k, v in acc.items()}


def _composites(means: Mapping[tuple[str, str], float]) -> dict[str, dict[str, float]]:
    policies = sorted({p for p, _ in means})
    out: dict[str, dict[str, float]] = {}
    for comp, criteria in COMPOSITES.items():
        scores = {}
        for p in policies:
            values = [means[(p, c)] for c in criteria if (p, c) in means]
            if len(values) == len(criteria):
                scores[p] = sum(values) / len(values)
        out[comp] = scores
    return out


@dataclass(frozen=True)
class Unit:
    policy: str
    criterion: str
    shift: float  # other - baseline panel mean


@dataclass(frozen=True)
class Comparison:
    n_personas: int
    rating: Agreement  # single ratings
    panel: Agreement  # policy x criterion panel means (all rated criteria)
    beyond_m: list[Unit]  # Table 4 units with |shift| > M, largest first
    taus: dict[str, float]  # composite -> Kendall tau-b (NaN when undefined)
    target_rank: float  # on Full Transformation in the other run (NaN when not scored)
    clauses: dict[str, ClauseResult]  # in the other run


def compare(ref: Ratings, other: Ratings, *, target: str, m: float = MATERIALITY_M) -> Comparison:
    """`other` against `ref`, both restricted to the (persona, policy, criterion) keys they share
    so the panel means cover the same raters."""
    shared = set(ref) & set(other)
    ref_s = {k: ref[k] for k in shared}
    oth_s = {k: other[k] for k in shared}
    ref_means, oth_means = _panel_means(ref_s), _panel_means(oth_s)
    units = [
        Unit(p, c, oth_means[(p, c)] - ref_means[(p, c)])
        for (p, c) in sorted(ref_means)
        if c in TABLE4_CRITERIA and abs(oth_means[(p, c)] - ref_means[(p, c)]) > m
    ]
    units.sort(key=lambda u: -abs(u.shift))
    ref_comp, oth_comp = _composites(ref_means), _composites(oth_means)
    taus = {}
    for comp in COMPOSITES:
        policies = sorted(set(ref_comp[comp]) & set(oth_comp[comp]))
        x = [ref_comp[comp][p] for p in policies]
        y = [oth_comp[comp][p] for p in policies]
        tau = kendall_tau_b(x, y) if len(policies) > 1 else None
        taus[comp] = math.nan if tau is None else tau
    full = oth_comp.get(FULL, {})
    rank = descending_ranks(full).get(target, math.nan) if full else math.nan
    return Comparison(
        n_personas=len({k[0] for k in shared}),
        rating=agreement(ref_s, oth_s),
        panel=agreement(ref_means, oth_means),
        beyond_m=units,
        taus=taus,
        target_rank=rank,
        clauses=evaluate_clauses(oth_comp),
    )


@dataclass(frozen=True)
class ProbeResult:
    target: str
    reversed: Comparison  # converted reversed run vs baseline
    rerun: Comparison  # baseline rerun vs baseline: the repeat-noise reference
    raw: Agreement  # raw (unconverted) reversed scores vs baseline; a mirror gives r near -1
    calls: dict[str, int]  # call class -> count
    converted_only: Comparison | None  # without the unconverted calls (secondary)


def _calls(ratings: Ratings) -> dict[tuple[str, str], dict[str, float]]:
    out: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for (persona, policy, criterion), score in ratings.items():
        out[(persona, policy)][criterion] = score
    return out


def analyse(
    baseline: Ratings, rerun: Ratings, reversed_raw: Ratings, *, target: str
) -> ProbeResult:
    base_calls, rev_calls = _calls(baseline), _calls(reversed_raw)
    classes = {k: 0 for k in CALL_CLASSES}
    unconverted: set[tuple[str, str]] = set()
    for call, raw in rev_calls.items():
        common = sorted(set(raw) & set(base_calls.get(call, {})))
        if not common:
            continue
        cls = classify_call([raw[c] for c in common], [base_calls[call][c] for c in common])
        classes[cls] += 1
        if cls == UNCONVERTED:
            unconverted.add(call)
    converted = {k: convert(v) for k, v in reversed_raw.items()}
    kept = {k: v for k, v in converted.items() if (k[0], k[1]) not in unconverted}
    return ProbeResult(
        target=target,
        reversed=compare(baseline, converted, target=target),
        rerun=compare(baseline, rerun, target=target),
        raw=agreement(baseline, reversed_raw),
        calls=classes,
        converted_only=compare(baseline, kept, target=target) if kept else None,
    )
