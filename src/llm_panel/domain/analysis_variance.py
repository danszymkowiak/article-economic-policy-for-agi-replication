"""Variance decomposition (TASK-20; prereg s6 "Secondary descriptives"). Pure, descriptive.

Estimator: a balanced crossed random-effects ANOVA (method of moments). For factors F with
n_f levels and a subset S of F, the effect array of S comes from the marginal means by
inclusion-exclusion, MS_S = SS_S / prod_{f in S}(n_f - 1), and

    E[MS_S] = sum_{T >= S} c_T sigma2_T,  c_T = prod_{f not in T} n_f,

which inverts (Moebius inversion over the subsets) to

    sigma2_S = (1 / c_S) sum_{T >= S} (-1)^{|T| - |S|} MS_T.

With one rating per combination, the full interaction is confounded with the residual. Raw
estimates can be negative and are reported as such; shares use estimates truncated at 0. Policy
and criterion are fixed in the design; their "components" are then read as the variance of their
effects (divisor n - 1), the usual descriptive reading of an all-random fit. Factors with one level
are dropped: their components are not identified.

Three questions are answered within a cell (B is primary):
- the four-way persona x policy x criterion x repeat decomposition on personas complete in every
  rated triplet: how much variance persona explains (main effect and all persona terms without
  repeat), against repeat noise (every term with repeat) and the policy/criterion structure;
- per policy x criterion, a persona x repeat decomposition: persona share
  sigma2_P / (sigma2_P + sigma2_R + sigma2_PR,e), and the intraclass correlation of two personas'
  ratings within one run, icc_run = sigma2_R / (same total): the run shock is the only term the
  personas of a cell share. Effective number of independent raters, the design-effect formula
  n_eff = n / (1 + (n - 1) icc), n the personas in that policy x criterion;
- per criterion, a persona x policy x repeat decomposition: agreement correlation between two
  personas' single-run ratings across policies, icc_agree = (sigma2_J + sigma2_JR) /
  (sigma2_J + sigma2_JR + sigma2_PJ + sigma2_PJR,e). Its complement is the persona-specific
  (persona x policy) and noise share; n_eff by the same formula ("the panel behaves as one
  model", prereg H4).

Varied factors (one-at-a-time design, not factorial): each cell against B at panel-mean level,
units = policy x criterion. d_u = cell mean - B mean over repeats, both panel means over the
cell's common-complete personas (paired cells: personas and triplets common to both); a cell without
personas (D2) is decomposed on its repeats with no failed call (TASK-37). With
MS_UR the unit x repeat mean square of a cell's panel means (single-run noise net of the shared
run shift), E[var_u d] = sigma2_shift + MS_UR,B / k_B + MS_UR,cell / k_cell, so
sigma2_shift = var_u(d) - MS_UR,B / k_B - MS_UR,cell / k_cell is the unit-specific shift the factor
adds beyond repeat noise (a one-repeat cell borrows B's MS_UR). It is reported against B's
single-run noise (ratio_to_noise = sigma2_shift / MS_UR,B), with the same estimator applied to
every split of B's repeats into k_cell and the rest as the repeat-noise band (prereg s3; overlapping
splits, descriptive, not a test). The level shift mean_u d has noise SE
sqrt(MS_R,B / (n_u k_B) + MS_R,cell / (n_u k_cell)).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from llm_panel.domain.analysis_rank import CellArray, aggregate, align_cells, complete_repeats

PERSONA, POLICY, CRITERION, REPEAT, UNIT = "persona", "policy", "criterion", "repeat", "unit"
CELL_FACTORS = (REPEAT, CRITERION, POLICY, PERSONA)  # CellArray axis order


@dataclass(frozen=True)
class Components:
    """Variance components of a balanced crossed design; keys follow `all_factors` order."""

    all_factors: tuple[str, ...]  # as passed, size-1 factors included
    factors: tuple[str, ...]  # identified (two or more levels)
    sizes: dict[str, int]
    estimates: dict[tuple[str, ...], float]  # raw, may be negative
    mean_squares: dict[tuple[str, ...], float]
    dfs: dict[tuple[str, ...], int]

    def key(self, terms: Iterable[str]) -> tuple[str, ...]:
        terms = set(terms)
        return tuple(f for f in self.all_factors if f in terms)

    def identified(self, terms: Iterable[str]) -> bool:
        return self.key(terms) in self.estimates

    def estimate(self, terms: Iterable[str]) -> float:
        return self.estimates.get(self.key(terms), math.nan)

    def truncated(self, terms: Iterable[str]) -> float:
        value = self.estimate(terms)
        return value if math.isnan(value) else max(value, 0.0)

    def mean_square(self, terms: Iterable[str]) -> float:
        return self.mean_squares.get(self.key(terms), math.nan)

    @property
    def total(self) -> float:
        return sum(max(v, 0.0) for v in self.estimates.values())

    def share(self, keys: Iterable[Iterable[str]]) -> float:
        total = self.total
        if total <= 0:
            return math.nan
        return sum(self.truncated(k) for k in keys) / total

    @property
    def residual_key(self) -> tuple[str, ...]:
        return self.factors


def variance_components(x: np.ndarray, factors: Sequence[str]) -> Components:
    """Method-of-moments components of a complete balanced crossed array (one value per cell)."""
    x = np.asarray(x, float)
    if x.ndim != len(factors):
        raise ValueError(f"{x.ndim} axes but {len(factors)} factor names")
    if np.isnan(x).any():
        raise ValueError("variance components need a complete array (no NaN)")
    keep = [i for i, n in enumerate(x.shape) if n >= 2]
    if not keep:
        raise ValueError("needs at least one factor with two or more levels")
    x = x.reshape([x.shape[i] for i in keep])
    names = tuple(factors[i] for i in keep)
    k, sizes, total_n = len(names), x.shape, x.size
    subsets = [s for r in range(k + 1) for s in itertools.combinations(range(k), r)]
    means = {
        s: x.mean(axis=tuple(i for i in range(k) if i not in s), keepdims=True) for s in subsets
    }
    effects = {
        s: sum(
            (-1) ** (len(s) - len(t)) * means[t]
            for r in range(len(s) + 1)
            for t in itertools.combinations(s, r)
        )
        for s in subsets
        if s
    }
    ms, dfs = {}, {}
    for s, eff in effects.items():
        df = math.prod(sizes[i] - 1 for i in s)
        ss = float((eff**2).sum()) * total_n / eff.size
        ms[s], dfs[s] = ss / df, df
    estimates = {}
    for s in effects:
        c = math.prod(sizes[i] for i in range(k) if i not in s)
        acc = sum((-1) ** (len(t) - len(s)) * ms[t] for t in effects if set(s) <= set(t))
        estimates[s] = acc / c

    def label(s):
        return tuple(names[i] for i in s)

    return Components(
        all_factors=tuple(factors),
        factors=names,
        sizes={names[i]: sizes[i] for i in range(k)},
        estimates={label(s): v for s, v in estimates.items()},
        mean_squares={label(s): v for s, v in ms.items()},
        dfs={label(s): v for s, v in dfs.items()},
    )


def effective_n(n: int, icc: float) -> float:
    """Design-effect effective number of independent raters: n / (1 + (n - 1) icc)."""
    if math.isnan(icc):
        return math.nan
    return n / (1 + (n - 1) * icc)


@dataclass(frozen=True)
class CellDecomposition:
    cell_id: str
    n_personas: int  # complete in every rated triplet and repeat
    n_personas_dropped: int
    n_policies: int
    n_criteria: int
    n_repeats: int
    components: Components | None  # None when nothing is left to decompose
    persona_main_share: float
    persona_share: float  # every term with persona and without repeat
    repeat_share: float  # every term with repeat (repeat noise, incl. the residual)
    structure_share: float  # policy, criterion and policy x criterion
    noise_confounded: bool  # one repeat: the top (persona) interaction holds the noise


def _complete(scores: np.ndarray) -> tuple[np.ndarray, int]:
    """Drop policies and criteria nobody rated, then personas missing any triplet."""
    rated = ~np.isnan(scores)
    scores = scores[:, rated.any(axis=(0, 2, 3))]
    scores = scores[:, :, ~np.isnan(scores).all(axis=(0, 1, 3))]
    full = ~np.isnan(scores).any(axis=(0, 1, 2))
    return scores[..., full], int((~full).sum())


def decompose_cell(cell: CellArray) -> CellDecomposition:
    scores, dropped = _complete(cell.scores[complete_repeats(cell.scores)])
    n_r, n_c, n_j, n_p = scores.shape
    if not cell.has_personas:
        n_p, dropped = 0, 0
    try:
        comp = variance_components(scores, CELL_FACTORS)
    except ValueError:
        comp = None
    nan = math.nan
    if comp is None:
        return CellDecomposition(cell.cell_id, n_p, dropped, n_j, n_c, n_r, None,
                                 nan, nan, nan, nan, n_r < 2)  # fmt: skip
    keys = list(comp.estimates)
    with_p = [k for k in keys if PERSONA in k and REPEAT not in k]
    with_r = [k for k in keys if REPEAT in k]
    structure = [k for k in keys if set(k) <= {POLICY, CRITERION}]
    has_p = PERSONA in comp.factors
    return CellDecomposition(
        cell.cell_id, n_p, dropped, n_j, n_c, n_r, comp,
        comp.share([(PERSONA,)]) if has_p else nan,
        comp.share(with_p) if has_p else nan,
        comp.share(with_r) if REPEAT in comp.factors else nan,
        comp.share(structure),
        REPEAT not in comp.factors,
    )  # fmt: skip


@dataclass(frozen=True)
class PersonaCell:
    """One policy x criterion: persona x repeat decomposition (NaN where not identified)."""

    policy_id: str
    criterion: str
    n_personas: int
    n_repeats: int
    var_persona: float
    var_run: float
    var_residual: float  # persona x run interaction and error
    persona_share: float
    icc_run: float
    n_eff_run: float


def persona_cells(cell: CellArray) -> list[PersonaCell]:
    out = []
    for ci, criterion in enumerate(cell.criteria):
        for ji, policy in enumerate(cell.policy_ids):
            x = cell.scores[:, ci, ji, :]  # [repeat, persona]
            x = x[:, ~np.isnan(x).any(axis=0)]
            n_r, n_p = x.shape
            if n_p == 0:
                continue
            values = [math.nan] * 6
            if n_r >= 2 and n_p >= 2:
                comp = variance_components(x, (REPEAT, PERSONA))
                vp, vr = comp.truncated((PERSONA,)), comp.truncated((REPEAT,))
                ve = comp.truncated((REPEAT, PERSONA))
                total = vp + vr + ve
                share = vp / total if total > 0 else math.nan
                icc = vr / total if total > 0 else math.nan
                values = [vp, vr, ve, share, icc, effective_n(n_p, icc)]
            out.append(PersonaCell(policy, criterion, n_p, n_r, *values))
    return out


@dataclass(frozen=True)
class CriterionAgreement:
    criterion: str
    n_personas: int
    n_policies: int
    n_repeats: int
    icc_agree: float
    persona_policy_share: float  # persona x policy share of a single-run rating's policy variance
    n_eff_agree: float
    noise_confounded: bool  # one repeat: persona x policy holds the noise too


def criterion_agreement(cell: CellArray) -> list[CriterionAgreement]:
    out = []
    for ci, criterion in enumerate(cell.criteria):
        x = cell.scores[:, ci]  # [repeat, policy, persona]
        x = x[:, ~np.isnan(x).all(axis=(0, 2))]
        x = x[..., ~np.isnan(x).any(axis=(0, 1))]
        n_r, n_j, n_p = x.shape
        if n_j < 2 or n_p < 2:
            continue
        comp = variance_components(x, (REPEAT, POLICY, PERSONA))
        shared = comp.truncated((POLICY,)) + (comp.truncated((REPEAT, POLICY)) if n_r >= 2 else 0.0)
        own = comp.truncated((POLICY, PERSONA))
        noise = comp.truncated((REPEAT, POLICY, PERSONA)) if n_r >= 2 else 0.0
        denom = shared + own + noise
        icc = shared / denom if denom > 0 else math.nan
        share = own / denom if denom > 0 else math.nan
        out.append(CriterionAgreement(criterion, n_p, n_j, n_r, icc, share,
                                      effective_n(n_p, icc), n_r < 2))  # fmt: skip
    return out


@dataclass(frozen=True)
class FactorShift:
    """One varied cell against B at panel-mean level (units = policy x criterion)."""

    cell_id: str
    pairing: str
    n_units: int
    k_b: int
    k_cell: int
    level_shift: float  # mean over units of cell - B
    level_se: float  # repeat-noise SE of the level shift
    shift_var: float  # unit-specific shift variance beyond repeat noise (raw, may be < 0)
    noise_var_b: float  # MS_UR of B: single-run panel-mean noise variance per unit
    noise_var_cell: float
    noise_source: str  # "own" | "B" (one-repeat cell borrows B's)
    ratio_to_noise: float  # shift_var / noise_var_b
    band: tuple[float, ...]  # the same ratio over every split of B's repeats (k_cell vs rest)

    @property
    def shift_sd(self) -> float:
        return math.sqrt(max(self.shift_var, 0.0)) if not math.isnan(self.shift_var) else math.nan

    @property
    def share_vs_noise(self) -> float:
        """Share of a single-run unit deviation's variance the factor adds."""
        v = max(self.shift_var, 0.0)
        return v / (v + self.noise_var_b) if v + self.noise_var_b > 0 else math.nan


def unit_noise(units: np.ndarray) -> tuple[float, float]:
    """(MS_UR, MS_R) of [repeat, unit] panel means; NaN with one repeat."""
    if units.shape[0] < 2 or units.shape[1] < 2:
        return math.nan, math.nan
    comp = variance_components(units, (REPEAT, UNIT))
    return comp.mean_square((REPEAT, UNIT)), comp.mean_square((REPEAT,))


def _shift(ub: np.ndarray, uc: np.ndarray, fallback: tuple[float, float]):
    """(level, level_se, shift_var, noise_b, noise_c, source); a side with one repeat borrows
    `fallback`."""
    (nb, rb), (nc, rc) = unit_noise(ub), unit_noise(uc)
    source = "own"
    if math.isnan(nb):
        nb, rb = fallback
    if math.isnan(nc):
        (nc, rc), source = fallback, "B"
    kb, kc, n_u = ub.shape[0], uc.shape[0], ub.shape[1]
    d = uc.mean(axis=0) - ub.mean(axis=0)
    shift_var = float(np.var(d, ddof=1)) - nb / kb - nc / kc
    level_se = math.sqrt(rb / (n_u * kb) + rc / (n_u * kc))
    return float(d.mean()), level_se, shift_var, nb, nc, source


def factor_shift(b: CellArray, cell: CellArray) -> FactorShift:
    if b.criteria != cell.criteria or b.policy_ids != cell.policy_ids:
        raise ValueError("cells must share criteria and policies")
    xb, xc, pairing = align_cells(b, cell)
    xc = xc[complete_repeats(xc)]  # no-persona cell: the repeats with no failed call
    n_units = len(b.criteria) * len(b.policy_ids)
    ub = aggregate(xb, "mean").reshape(xb.shape[0], n_units)  # [repeat, unit]
    uc = aggregate(xc, "mean").reshape(xc.shape[0], n_units)
    ok = ~np.isnan(ub).any(axis=0) & ~np.isnan(uc).any(axis=0)
    ub, uc = ub[:, ok], uc[:, ok]
    kb, kc, n_u = ub.shape[0], uc.shape[0], ub.shape[1]
    nan = math.nan
    if n_u < 2 or kb < 1 or kc < 1:
        return FactorShift(cell.cell_id, pairing, n_u, kb, kc, nan, nan, nan, nan, nan, "own",
                           nan, ())  # fmt: skip
    full_b = unit_noise(ub)
    level, se, shift_var, nb, nc, source = _shift(ub, uc, full_b)
    band = []
    if 1 <= kc < kb:
        for chosen in itertools.combinations(range(kb), kc):
            rest = [r for r in range(kb) if r not in chosen]
            *_, v, _, _, _ = _shift(ub[rest], ub[list(chosen)], full_b)
            band.append(v / full_b[0])
    return FactorShift(
        cell.cell_id, pairing, n_u, kb, kc, level, se, shift_var, nb, nc, source,
        shift_var / nb if nb > 0 else nan, tuple(band),
    )  # fmt: skip


@dataclass(frozen=True)
class PanelMeanSpread:
    """Run-to-run spread of a cell's policy x criterion panel means (prereg H1: precision)."""

    cell_id: str
    n_runs: int
    sds: tuple[float, ...]  # per unit: SD (n - 1) of its single-run panel means
    ranges: tuple[float, ...]  # per unit: max - min of its single-run panel means

    @property
    def n_units(self) -> int:
        return len(self.sds)


def panel_mean_run_spread(
    cell: CellArray, criteria: Sequence[str] | None = None
) -> PanelMeanSpread:
    """Per policy x criterion unit, the spread across the cell's complete repeats of its panel
    mean (unweighted mean over the personas present). Units need every complete repeat; no units
    with fewer than two repeats."""
    scores = cell.scores[complete_repeats(cell.scores)]
    keep = [i for i, c in enumerate(cell.criteria) if criteria is None or c in criteria]
    scores = scores[:, keep]
    n_runs = scores.shape[0]
    if n_runs < 2:
        return PanelMeanSpread(cell.cell_id, n_runs, (), ())
    n = (~np.isnan(scores)).sum(axis=3)
    means = np.where(n > 0, np.nansum(scores, axis=3) / np.maximum(n, 1), np.nan)
    units = means.reshape(n_runs, -1)
    units = units[:, ~np.isnan(units).any(axis=0)]
    return PanelMeanSpread(
        cell.cell_id,
        n_runs,
        tuple(float(x) for x in units.std(axis=0, ddof=1)),
        tuple(float(x) for x in units.max(axis=0) - units.min(axis=0)),
    )
