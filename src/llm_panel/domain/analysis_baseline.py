"""Baseline B versus the paper's published scores (TASK-18; prereg s6 "Comparison with the paper").
Pure: rank statistics, Table 4 composites, and the repeat-mean panel. Descriptive only.

Composites follow the column groups of the paper's Table 4, as unweighted means of their columns
(prereg s4 Aggregation; reconstruction.md R8):
- every Table 4 panel column on its own (11);
- Welfare & Resilience: Living, Meaning, Stab.; Agency & Voice: Agency, Owner., Voice;
- Feasibility: Econ. F. and Ready only. Reading of an ambiguity: Table 1's Feasibility dimension
  also names Political Support, Popular Support and Administrative Capacity & Speed, but Table 4's
  Feasibility block holds only these two columns, Popular Support is survey data, and the other
  two are never published per policy in the paper. We rate Political Support and Administrative
  Capacity & Speed but leave them out of every composite compared here. (The essay's own
  Feasibility composite is the mean of six columns, e.g. EITC 79.8 = mean of Political 75.2,
  Econ. F. 83.2, Popular 77.3, Admin. 77.9, Speed 69.8, Ready 95.3; not comparable to ours.);
- Scenario Durability: mean of Mild, Moderate and Full Transformation (the paper's text uses it,
  e.g. ALMP "23 on average").
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

WELFARE = ("standards_of_living", "meaning_human_value", "macro_stabilisation")
AGENCY = ("economic_agency_mobility", "ownership_of_gains", "democratic_voice")
FEASIBILITY = ("economic_feasibility", "implementation_readiness")
DURABILITY = ("mild_disruption", "moderate_disruption", "full_transformation")
TABLE4_CRITERIA = WELFARE + AGENCY + FEASIBILITY + DURABILITY

# composite id -> criterion ids averaged; report order
COMPOSITES: dict[str, tuple[str, ...]] = {
    **{c: (c,) for c in TABLE4_CRITERIA},
    "welfare_resilience": WELFARE,
    "agency_voice": AGENCY,
    "feasibility": FEASIBILITY,
    "scenario_durability": DURABILITY,
}

Scores = Mapping[str, Mapping[str, float]]  # criterion or composite id -> policy id -> score

NET_APPROVAL = "public_net_approval_pct"  # survey data in the paper, not a panel rating


@dataclass(frozen=True)
class PublishedTable:
    """The paper's per-policy numbers as transcribed, with their provenance lines."""

    provenance: tuple[str, ...]
    scores: dict[str, dict[str, float]]  # column id -> policy id -> value
    policy_order: tuple[str, ...]  # Table 3 / Table 4 order


def average_ranks(values: Sequence[float]) -> list[float]:
    """1-based ranks, ties sharing their average rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def _pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    n = len(x)
    if n < 2:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Spearman rho (Pearson on average ranks); None when undefined."""
    return _pearson(average_ranks(x), average_ranks(y))


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Kendall tau-b (tie-corrected); None when undefined."""
    n = len(x)
    concordant = discordant = ties_x = ties_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0:
                ties_x += 1
                ties_y += 1
            elif dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    pairs = n * (n - 1) // 2
    denom = math.sqrt((pairs - ties_x) * (pairs - ties_y))
    if denom == 0:
        return None
    return (concordant - discordant) / denom


def composite_scores(
    scores: Scores, composites: Mapping[str, Sequence[str]] = COMPOSITES
) -> dict[str, dict[str, float]]:
    """Composite -> policy -> unweighted mean of its criteria; a policy missing any part is left
    out of that composite."""
    out: dict[str, dict[str, float]] = {}
    for name, parts in composites.items():
        policies = set.intersection(*(set(scores.get(c, {})) for c in parts))
        out[name] = {p: sum(scores[c][p] for c in parts) / len(parts) for p in sorted(policies)}
    return out


@dataclass(frozen=True)
class Observation:
    """One parsed rating of cell B: persona x policy x criterion in one repeat."""

    repeat: int
    persona_id: str
    policy_id: str
    criterion_id: str
    score: float


@dataclass(frozen=True)
class PanelMeans:
    scores: dict[str, dict[str, float]]  # criterion -> policy -> repeat-mean panel score
    n_repeats: int
    n_pairs: int  # persona x policy pairs complete in every repeat (common-complete set)
    dropped_pairs: int  # pairs seen in some repeat but not all


def repeat_mean_panel(observations: Iterable[Observation]) -> PanelMeans:
    """Panel mean per repeat (unweighted over personas), then the mean over repeats, on the
    persona x policy pairs present in every repeat (prereg s7, common-complete set)."""
    obs = list(observations)
    repeats = sorted({o.repeat for o in obs})
    present: dict[tuple[str, str], set[int]] = defaultdict(set)
    for o in obs:
        present[(o.persona_id, o.policy_id)].add(o.repeat)
    complete = {pair for pair, rs in present.items() if len(rs) == len(repeats)}
    per_repeat: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for o in obs:
        if (o.persona_id, o.policy_id) in complete:
            per_repeat[(o.criterion_id, o.policy_id, o.repeat)].append(o.score)
    by_cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (criterion, policy, _repeat), values in per_repeat.items():
        by_cell[(criterion, policy)].append(sum(values) / len(values))
    scores: dict[str, dict[str, float]] = defaultdict(dict)
    for (criterion, policy), means in sorted(by_cell.items()):
        scores[criterion][policy] = sum(means) / len(means)
    return PanelMeans(dict(scores), len(repeats), len(complete), len(present) - len(complete))


@dataclass(frozen=True)
class Agreement:
    composite: str
    n_policies: int
    spearman: float | None
    kendall_tau_b: float | None
    mean_abs_diff: float  # NaN when no policy is on both sides
    differences: dict[str, float]  # policy -> ours minus published


def compare(ours: Scores, published: Scores, composites: Sequence[str]) -> list[Agreement]:
    """Per composite, on the policies scored on both sides: rank agreement and score gap."""
    out = []
    for name in composites:
        mine, theirs = ours.get(name, {}), published.get(name, {})
        policies = sorted(set(mine) & set(theirs))
        x = [mine[p] for p in policies]
        y = [theirs[p] for p in policies]
        diffs = {p: mine[p] - theirs[p] for p in policies}
        mad = sum(abs(d) for d in diffs.values()) / len(diffs) if diffs else math.nan
        out.append(Agreement(name, len(policies), spearman(x, y), kendall_tau_b(x, y), mad, diffs))
    return out
