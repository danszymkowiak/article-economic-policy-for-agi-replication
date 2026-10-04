"""Recommendation robustness (TASK-21; prereg s6 "Recommendation clauses"). Pure, descriptive.

The four clauses restate the paper's claims with cut-offs from Table 4 (the published data pass
all four). Each is reported with its continuous margin: a policy's score minus the k-th best
score among the other policies, so a clause "policy in the top k" holds exactly when the margin
is positive. A tie at the boundary has margin 0 and does not hold (with average ranks it sits
above k). A clause whose policies are not all scored is undefined (None).

- (a) UBC rank 1 on Full Transformation durability (published margin 15.5);
- (b) UBC rank 1 on Ownership of Gains (40.0);
- (c) NIT in the top 3 on Moderate durability (69.8 - UI 65.9 = 3.9; prereg s6 writes 3.8, the
  gap to UBC 66.0 at rank 3);
- (d) UI and EITC both in the top 4 on Mild durability and both below UBC on Full Transformation
  (5.9: EITC 68.9 - UBC 63.0 on Mild); the margin is the smallest of its four parts.

The three-stage sequence (UI/EITC for Mild -> NIT for Moderate -> UBC for Full Transformation)
holds when (a), (c) and (d) all hold; its margin is their smallest. (b) is the ownership claim,
not a stage. The Mild recommendation's employer-led retraining (ALMP) is excluded from the clauses
(prereg s6); its Mild rank is reported.

Flips: a clause flips in a run (or in a cell's repeat mean) when its truth value differs from
B's repeat mean on the same common-complete persona x policy x criterion set (prereg s6, s7).

Score consistency (beyond s6, so exploratory): whether each stage's recommended policy is the
top-scoring one on its scenario, which policies outside the sequence lead a durability composite
(e.g. UBS), and NIT's rank on Political Support next to clause (c). "Low" political support is a
rank below the median policy (our reading; the paper gives no cut-off).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from llm_panel.domain.analysis_baseline import COMPOSITES, TABLE4_CRITERIA, Scores, pearson
from llm_panel.domain.analysis_rank import (
    CellArray,
    align_cells,
    descending_ranks,
    repeat_composites,
)

POLITICAL = "political_support"
RECOMMEND_CRITERIA = (*TABLE4_CRITERIA, POLITICAL)
RECOMMEND_COMPOSITES: dict[str, tuple[str, ...]] = {**COMPOSITES, POLITICAL: (POLITICAL,)}

MILD, MODERATE, FULL = "mild_disruption", "moderate_disruption", "full_transformation"
OWNERSHIP, READINESS = "ownership_of_gains", "implementation_readiness"
DURABILITY_COMPOSITES = (MILD, MODERATE, FULL, "scenario_durability")
# stage scenario -> the policies the paper recommends there
STAGES: dict[str, tuple[str, ...]] = {MILD: ("ui", "eitc"), MODERATE: ("nit",), FULL: ("ubc",)}
SEQUENCE = ("ui", "eitc", "nit", "ubc")
MATERIALITY_M = 5.0  # prereg s6, set in advance
SEQUENCE_CLAUSES = ("a", "c", "d")
CLAUSES = ("a", "b", "c", "d", "sequence")
CLAUSE_TEXT = {
    "a": "UBC rank 1 on Full Transformation durability",
    "b": "UBC rank 1 on Ownership of Gains",
    "c": "NIT in the top 3 on Moderate durability",
    "d": "UI and EITC in the top 4 on Mild, both below UBC on Full Transformation",
    "sequence": "three-stage sequence UI/EITC -> NIT -> UBC: (a), (c) and (d) all hold",
}


@dataclass(frozen=True)
class ClauseResult:
    clause: str
    holds: bool | None  # None when a policy it needs is not scored
    margin: float  # NaN when undefined
    parts: dict[str, float]  # component margins


def margin_top_k(scores: Mapping[str, float], policy: str, k: int) -> float:
    """scores[policy] minus the k-th best score among the other policies; NaN when undefined."""
    others = sorted((v for p, v in scores.items() if p != policy), reverse=True)
    if policy not in scores or len(others) < k:
        return math.nan
    return scores[policy] - others[k - 1]


def _diff(scores: Mapping[str, float], a: str, b: str) -> float:
    return scores[a] - scores[b] if a in scores and b in scores else math.nan


def _result(clause: str, parts: dict[str, float]) -> ClauseResult:
    values = list(parts.values())
    if any(math.isnan(v) for v in values):
        return ClauseResult(clause, None, math.nan, parts)
    margin = min(values)
    return ClauseResult(clause, margin > 0, margin, parts)


def evaluate_clauses(scores: Scores) -> dict[str, ClauseResult]:
    """Clauses (a)-(d) and the sequence on one set of composite scores."""
    mild, moderate, full = (scores.get(c, {}) for c in (MILD, MODERATE, FULL))
    ownership = scores.get(OWNERSHIP, {})
    out = {
        "a": _result("a", {"ubc_top1_full": margin_top_k(full, "ubc", 1)}),
        "b": _result("b", {"ubc_top1_ownership": margin_top_k(ownership, "ubc", 1)}),
        "c": _result("c", {"nit_top3_moderate": margin_top_k(moderate, "nit", 3)}),
        "d": _result("d", {
            "ui_top4_mild": margin_top_k(mild, "ui", 4),
            "eitc_top4_mild": margin_top_k(mild, "eitc", 4),
            "ubc_minus_ui_full": _diff(full, "ubc", "ui"),
            "ubc_minus_eitc_full": _diff(full, "ubc", "eitc"),
        }),
    }  # fmt: skip
    seq = [out[c] for c in SEQUENCE_CLAUSES]
    if any(r.holds is None for r in seq):
        out["sequence"] = ClauseResult("sequence", None, math.nan, {})
    else:
        out["sequence"] = ClauseResult(
            "sequence", all(r.holds for r in seq), min(r.margin for r in seq),
            {f"clause_{r.clause}": r.margin for r in seq},
        )  # fmt: skip
    return out


@dataclass(frozen=True)
class Consistency:
    """Do the recommendations follow from the scores? (exploratory; see module docstring)"""

    leaders: dict[str, tuple[str, ...]]  # durability composite -> top-scoring policies (ties all)
    stage_follows: dict[str, bool | None]  # stage -> its sole leader is a recommended policy
    leaders_outside_sequence: dict[str, tuple[str, ...]]
    ubs_ranks: dict[str, float]  # durability composite -> UBS average rank (NaN if unscored)
    ubs_leads: bool | None  # UBS the sole leader on at least one durability composite
    nit_political_rank: float  # NaN without Political Support scores
    nit_political_score: float
    n_political: int
    nit_low_political: bool | None  # rank below the median policy
    nit_despite_low_political: bool | None  # clause (c) holds and NIT's support is low
    almp_mild_rank: float


def _leaders(scores: Mapping[str, float]) -> tuple[str, ...]:
    if not scores:
        return ()
    top = max(scores.values())
    return tuple(sorted(p for p, v in scores.items() if v == top))


def _rank(scores: Mapping[str, float], policy: str) -> float:
    return descending_ranks(scores)[policy] if policy in scores else math.nan


def consistency(scores: Scores, clauses: Mapping[str, ClauseResult]) -> Consistency:
    leaders = {c: _leaders(scores.get(c, {})) for c in DURABILITY_COMPOSITES}
    stage_follows = {
        stage: (len(leaders[stage]) == 1 and leaders[stage][0] in recommended)
        if leaders[stage] else None
        for stage, recommended in STAGES.items()
    }  # fmt: skip
    outside = {c: tuple(p for p in ls if p not in SEQUENCE) for c, ls in leaders.items()}
    ubs_ranks = {c: _rank(scores.get(c, {}), "ubs") for c in DURABILITY_COMPOSITES}
    ubs_scored = [c for c in DURABILITY_COMPOSITES if "ubs" in scores.get(c, {})]
    ubs_leads = any(leaders[c] == ("ubs",) for c in ubs_scored) if ubs_scored else None
    political = scores.get(POLITICAL, {})
    n = len(political)
    rank = _rank(political, "nit")
    low = None if math.isnan(rank) else rank > (n + 1) / 2
    c_holds = clauses["c"].holds
    despite = None if low is None or c_holds is None else (low and c_holds)
    return Consistency(
        leaders, stage_follows, outside, ubs_ranks, ubs_leads, rank,
        political.get("nit", math.nan), n, low, despite, _rank(scores.get(MILD, {}), "almp"),
    )  # fmt: skip


def ownership_gap(scores: Scores) -> float:
    """UBC minus Sovereign AI Fund (sawf) on Ownership of Gains; NaN when either is unscored."""
    return _diff(scores.get(OWNERSHIP, {}), "ubc", "sawf")


def correlation(x: Mapping[str, float], y: Mapping[str, float]) -> float:
    """Pearson r over the policies on both sides; NaN when undefined."""
    common = sorted(set(x) & set(y))
    r = pearson([x[p] for p in common], [y[p] for p in common])
    return math.nan if r is None else r


@dataclass(frozen=True)
class RunResult:
    """Everything recorded for one run, one repeat mean or B's reference."""

    scores: dict[str, dict[str, float]]  # composite -> policy -> panel score
    clauses: dict[str, ClauseResult]
    consistency: Consistency
    gap: float  # UBC - SAWF on Ownership of Gains
    r_approval: float  # r(public net approval, Full Transformation); NaN without approvals
    r_readiness: float  # r(Implementation Readiness, Full Transformation)


def run_result(scores: dict[str, dict[str, float]], net_approval: Mapping[str, float] | None):
    clauses = evaluate_clauses(scores)
    return RunResult(
        scores, clauses, consistency(scores, clauses), ownership_gap(scores),
        correlation(net_approval, scores.get(FULL, {})) if net_approval else math.nan,
        correlation(scores.get(READINESS, {}), scores.get(FULL, {})),
    )  # fmt: skip


@dataclass(frozen=True)
class CellRecommendations:
    cell_id: str
    pairing: str
    n_repeats: int
    reference: RunResult  # B's repeat mean on the set shared with this cell
    mean: RunResult  # the cell's repeat mean
    runs: tuple[RunResult, ...]  # each single repeat of the cell

    def flip_count(self, clause: str) -> int:
        """Single runs whose truth value differs from B's repeat mean (both defined)."""
        ref = self.reference.clauses[clause].holds
        if ref is None:
            return 0
        return sum(
            1 for r in self.runs if r.clauses[clause].holds is not None
            and r.clauses[clause].holds != ref
        )  # fmt: skip

    def mean_flipped(self, clause: str) -> bool | None:
        ref, mine = self.reference.clauses[clause].holds, self.mean.clauses[clause].holds
        return None if ref is None or mine is None else ref != mine


def _per_repeat(x: np.ndarray, criteria: Sequence[str]) -> np.ndarray:
    return repeat_composites(x, "mean", criteria, RECOMMEND_COMPOSITES)  # [repeat, comp, policy]


def _to_scores(values: np.ndarray, policies: Sequence[str]) -> dict[str, dict[str, float]]:
    """[composite, policy] -> composite -> policy -> score, NaN left out."""
    return {
        name: {p: float(v) for p, v in zip(policies, values[i], strict=True) if not np.isnan(v)}
        for i, name in enumerate(RECOMMEND_COMPOSITES)
    }


def analyse_cell(
    b: CellArray, cell: CellArray, net_approval: Mapping[str, float] | None = None
) -> CellRecommendations:
    """The cell's single runs and repeat mean against B's repeat mean (aligned as in TASK-19).
    Passing B as the cell gives B's own single runs against its mean: the noise floor."""
    xb, xc, pairing = align_cells(b, cell)
    pb = _per_repeat(xb, b.criteria)
    pc = _per_repeat(xc, cell.criteria)
    return CellRecommendations(
        cell.cell_id, pairing, len(cell.repeats),
        run_result(_to_scores(pb.mean(axis=0), b.policy_ids), net_approval),
        run_result(_to_scores(pc.mean(axis=0), cell.policy_ids), net_approval),
        tuple(run_result(_to_scores(r, cell.policy_ids), net_approval) for r in pc),
    )  # fmt: skip


@dataclass(frozen=True)
class SplitNoise:
    """B's repeats split into a k-repeat mean and the mean of the rest, over every split."""

    k: int
    n_splits: int
    flip_fraction: dict[str, float]  # clause -> share of splits where the two disagree
    gap_differences: tuple[float, ...]  # k-mean gap minus rest gap, per split


def noise_floor(b: CellArray, ks: Iterable[int]) -> dict[int, SplitNoise]:
    """Repeat-noise reference for cells with k repeats (prereg s3): descriptive, not a test (the
    splits overlap). Only 1 <= k < B's repeat count has splits."""
    per = _per_repeat(b.scores, b.criteria)
    n = len(b.repeats)
    out = {}
    for k in sorted(set(ks)):
        if not 1 <= k < n:
            continue
        differs = {c: 0 for c in CLAUSES}
        defined = {c: 0 for c in CLAUSES}
        gaps = []
        for chosen in itertools.combinations(range(n), k):
            rest = [r for r in range(n) if r not in chosen]
            sa = _to_scores(per[list(chosen)].mean(axis=0), b.policy_ids)
            sr = _to_scores(per[rest].mean(axis=0), b.policy_ids)
            ca, cr = evaluate_clauses(sa), evaluate_clauses(sr)
            for c in CLAUSES:
                if ca[c].holds is not None and cr[c].holds is not None:
                    defined[c] += 1
                    differs[c] += ca[c].holds != cr[c].holds
            gaps.append(ownership_gap(sa) - ownership_gap(sr))
        out[k] = SplitNoise(
            k, len(gaps),
            {c: differs[c] / defined[c] if defined[c] else math.nan for c in CLAUSES},
            tuple(gaps),
        )  # fmt: skip
    return out
