"""Missing-data sensitivity (TASK-37; prereg s7). Pure.

Cells are compared on the common-complete set (primary, the other analyses). This module gives
the secondary views prereg s7 promises:
- survivor-only: every valid rating, no common-complete filter, no pairing with B;
- the worst-case bound: every failed call's ratings imputed at 0, and separately at 100.

Each view's unit mean is the unweighted panel mean per repeat over the personas present, then the
mean over the repeats present. Per cell against B (both under the same view): the number of Table 4
policy x criterion means shifted by more than M, and the recommendation clauses on the cell's own
means. Descriptive only.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    Observation,
    composite_scores,
)
from llm_panel.domain.analysis_rank import CellArray, aggregate, repeat_mean
from llm_panel.domain.analysis_recommend import CLAUSES, MATERIALITY_M, evaluate_clauses

VARIANTS = ("survivor", "impute_0", "impute_100")
_IMPUTED = {"impute_0": 0.0, "impute_100": 100.0}


@dataclass(frozen=True)
class Failure:
    """The ratings one failed call would have given."""

    repeat: int
    persona_id: str
    policy_ids: tuple[str, ...]
    criterion_ids: tuple[str, ...]


def variant_observations(
    observations: Sequence[Observation], failures: Iterable[Failure], variant: str
) -> list[Observation]:
    """The cell's ratings under one view: survivors as they are, or plus the imputed failures."""
    if variant == "survivor":
        return list(observations)
    if variant not in _IMPUTED:
        raise ValueError(f"unknown variant {variant!r}; expected one of {VARIANTS}")
    value = _IMPUTED[variant]
    imputed = [
        Observation(f.repeat, f.persona_id, p, c, value)
        for f in failures for p in f.policy_ids for c in f.criterion_ids
    ]  # fmt: skip
    return [*observations, *imputed]


def unit_means(cell: CellArray) -> np.ndarray:
    """[criterion, policy]: panel mean per repeat over the personas present, then the mean over
    the repeats present; NaN where nothing was rated."""
    return repeat_mean(aggregate(cell.scores, "mean"))


@dataclass(frozen=True)
class VariantResult:
    n_units: int  # Table 4 policy x criterion means present on both sides
    beyond: int  # of those, |cell - B| > M
    max_abs_shift: float  # NaN when no unit is on both sides
    clauses: dict[str, bool | None]  # clause -> holds on the cell's means (None: undefined)


def variant_comparison(b: CellArray, cell: CellArray, m: float = MATERIALITY_M) -> VariantResult:
    """`cell` against `b`, both built from one view's observations (common_complete=False)."""
    if b.criteria != cell.criteria or b.policy_ids != cell.policy_ids:
        raise ValueError("cells must share criteria and policies")
    mb, mc = unit_means(b), unit_means(cell)
    rows = [i for i, c in enumerate(cell.criteria) if c in TABLE4_CRITERIA]
    d = (mc - mb)[rows]
    d = d[~np.isnan(d)]
    scores = {
        c: {p: float(v) for p, v in zip(cell.policy_ids, mc[i], strict=True) if not np.isnan(v)}
        for i, c in enumerate(cell.criteria)
    }
    parts = {k: v for k, v in COMPOSITES.items() if all(c in scores for c in v)}
    clauses = evaluate_clauses(composite_scores(scores, parts))
    return VariantResult(
        int(d.size), int((np.abs(d) > m).sum()),
        float(np.abs(d).max()) if d.size else float("nan"),
        {k: clauses[k].holds for k in CLAUSES},
    )  # fmt: skip
