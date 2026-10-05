"""Materiality shifts (TASK-28; prereg s6 primary metric 2). Pure.

Per cell versus B: the number of policy x criterion panel means whose |shift| from B exceeds
M = 5 points (set in advance; M = 3 and 8 are a descriptive sensitivity, never used to pick M),
with the repeat-noise multiple. A unit's shift is d_u = cell mean - B mean over repeats, both
unweighted panel means on the common-complete set (paired cells: personas and triplets common to
both; the TASK-19 alignment). Its repeat-noise SE is sqrt(MS_UR,B / k_B + MS_UR,cell / k_cell), the
single-run panel-mean noise net of the shared run shift (TASK-20's estimator; a one-repeat cell
borrows B's), pooled over units. In a no-persona cell (D2) a failed call leaves a unit's mean over
its surviving repeats, and the noise comes from the repeats with no failed call (TASK-37); k_cell
stays the repeat count. The noise multiple is d_u / SE, and M / SE says how many SEs the
margin is.

Reference "what repeats do" (prereg s3): the same count for every split of B's repeats into a
k_cell-run mean and the mean of the rest. Descriptive, not a test: the splits overlap.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from llm_panel.domain.analysis_rank import (
    CellArray,
    aggregate,
    align_cells,
    complete_repeats,
    repeat_mean,
)
from llm_panel.domain.analysis_recommend import MATERIALITY_M
from llm_panel.domain.analysis_variance import unit_noise

SENSITIVITY_M = (3.0, 8.0)  # prereg s6: descriptive only
MARGINS = (SENSITIVITY_M[0], MATERIALITY_M, SENSITIVITY_M[1])


@dataclass(frozen=True)
class UnitShift:
    policy_id: str
    criterion: str
    b_mean: float
    cell_mean: float
    shift: float  # cell - B
    noise_multiple: float  # shift / repeat-noise SE of a shift

    def beyond(self, m: float) -> bool:
        return abs(self.shift) > m


@dataclass(frozen=True)
class Materiality:
    cell_id: str
    pairing: str
    k_b: int
    k_cell: int
    n_units: int  # policy x criterion means present on both sides
    noise_se: float  # repeat-noise SE of one unit's shift; NaN when not estimable
    noise_source: str  # "own" | "B" (a one-repeat cell borrows B's noise)
    counts: dict[float, int]  # M -> units with |shift| > M
    band: dict[float, tuple[int, ...]]  # M -> the same count over every split of B's repeats
    units: tuple[UnitShift, ...]

    @property
    def m_noise_multiple(self) -> float:
        """The primary margin M in repeat-noise SEs."""
        return MATERIALITY_M / self.noise_se if self.noise_se > 0 else math.nan


def _count(d: np.ndarray, ms: Sequence[float]) -> dict[float, int]:
    return {float(m): int((np.abs(d) > m).sum()) for m in ms}


def materiality(b: CellArray, cell: CellArray, ms: Sequence[float] = MARGINS) -> Materiality:
    if b.criteria != cell.criteria or b.policy_ids != cell.policy_ids:
        raise ValueError("cells must share criteria and policies")
    xb, xc, pairing = align_cells(b, cell)
    ub = aggregate(xb, "mean").reshape(xb.shape[0], -1)  # [repeat, unit]; unit = criterion x policy
    uc = aggregate(xc, "mean").reshape(xc.shape[0], -1)
    ok = ~np.isnan(ub).any(axis=0) & ~np.isnan(uc).all(axis=0)
    labels = [(p, c) for c in b.criteria for p in b.policy_ids]
    labels = [lab for lab, keep in zip(labels, ok, strict=True) if keep]
    ub, uc = ub[:, ok], uc[:, ok]
    kb, kc = ub.shape[0], uc.shape[0]
    (nb, _), (nc, _) = unit_noise(ub), unit_noise(uc[complete_repeats(uc)])
    source = "own"
    if math.isnan(nc):
        nc, source = nb, "B"
    se = math.sqrt(nb / kb + nc / kc) if kb and kc and not math.isnan(nb) else math.nan
    mb, mc = ub.mean(axis=0), repeat_mean(uc)
    d = mc - mb
    units = tuple(
        UnitShift(p, c, float(x), float(y), float(s), float(s) / se if se > 0 else math.nan)
        for (p, c), x, y, s in zip(labels, mb, mc, d, strict=True)
    )
    splits: list[dict[float, int]] = []
    if 1 <= kc < kb:
        for chosen in itertools.combinations(range(kb), kc):
            rest = [r for r in range(kb) if r not in chosen]
            splits.append(_count(ub[list(chosen)].mean(0) - ub[rest].mean(0), ms))
    return Materiality(
        cell.cell_id, pairing, kb, kc, len(labels), se, source, _count(d, ms),
        {float(m): tuple(s[float(m)] for s in splits) for m in ms}, units,
    )  # fmt: skip
