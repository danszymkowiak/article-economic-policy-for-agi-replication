"""Rank stability between cells (TASK-19; prereg s6 "Rank metrics"). Pure, descriptive.

For every cell versus B, per composite and per aggregation over personas:
- Kendall tau-b between the cell's and B's repeat-mean panel scores (ties count by tau-b's
  correction; ranks for shifts are average ranks, prereg s6);
- a persona-bootstrap percentile interval (secondary, a generalisation caveat only; prereg s3):
  the personas are resampled with replacement, the same draw on both sides when the cell uses B's
  personas ("paired"), an independent draw when it uses another panel (D2b), and no draw on the
  cell's side when it has no personas (D2);
- the single-run range: each repeat of the cell against B's repeat mean (prereg s3);
- the repeat-noise reference from B's own repeats (prereg s3, s6): tau between single repeats
  (pairwise), and the band of tau between a k-repeat mean and the mean of the remaining B repeats
  over every split, k = the cell's repeat count. The band is descriptive, not a test;
- per-policy rank shift and top-3 / bottom-3 set changes.

Aggregations over personas: the unweighted mean (prereg s4, primary), the median and the 10%
trimmed mean (int(0.1 n) cut from each end, scipy's trim_mean convention), each applied within a
repeat, then the mean over repeats. A persona x policy x criterion triplet enters a cell only when
it is present in every repeat of that cell (prereg s7, common-complete set); a paired comparison
also keeps only triplets complete in both cells.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    Observation,
    average_ranks,
)

AGGREGATIONS = ("mean", "median", "trimmed_mean_10")
# prereg s6: the three durability composites and each dimension composite
PREREG_COMPOSITES = (
    "mild_disruption", "moderate_disruption", "full_transformation",
    "welfare_resilience", "agency_voice", "feasibility", "scenario_durability",
)  # fmt: skip
# Placeholder: prereg s12 item 6 (persona bootstrap resample count) is still open.
DEFAULT_RESAMPLES = 1000
TOP_K = 3
NO_PERSONA_ID = "none"  # persona id of D2's calls (no persona)
PAIRED, INDEPENDENT, NO_PERSONAS = "paired", "independent", "no personas"
_CHUNK = 50  # bootstrap replicates per vectorised step (bounds memory)


@dataclass(frozen=True)
class CellArray:
    """One cell's ratings: scores[repeat, criterion, policy, persona], NaN where left out."""

    cell_id: str
    persona_ids: tuple[str, ...]
    policy_ids: tuple[str, ...]
    criteria: tuple[str, ...]
    repeats: tuple[int, ...]
    scores: np.ndarray

    @property
    def has_personas(self) -> bool:
        return self.persona_ids != (NO_PERSONA_ID,)


def build_cell_array(
    cell_id: str,
    observations: Iterable[Observation],
    *,
    policy_ids: Sequence[str],
    criteria: Sequence[str] = TABLE4_CRITERIA,
) -> CellArray:
    """Arrange a cell's ratings; triplets missing from any repeat are NaN in every repeat."""
    obs = [o for o in observations if o.criterion_id in criteria and o.policy_id in policy_ids]
    repeats = tuple(sorted({o.repeat for o in obs}))
    personas = tuple(sorted({o.persona_id for o in obs}))
    r_ix = {r: i for i, r in enumerate(repeats)}
    c_ix = {c: i for i, c in enumerate(criteria)}
    p_ix = {p: i for i, p in enumerate(policy_ids)}
    n_ix = {n: i for i, n in enumerate(personas)}
    scores = np.full((len(repeats), len(criteria), len(policy_ids), len(personas)), np.nan)
    for o in obs:
        scores[r_ix[o.repeat], c_ix[o.criterion_id], p_ix[o.policy_id], n_ix[o.persona_id]] = (
            o.score
        )
    scores[:, np.isnan(scores).any(axis=0)] = np.nan
    return CellArray(cell_id, personas, tuple(policy_ids), tuple(criteria), repeats, scores)


def aggregate(values: np.ndarray, how: str) -> np.ndarray:
    """Aggregate over the last axis, ignoring NaN; NaN where nothing is left."""
    ordered = np.sort(values, axis=-1)  # NaN sorts last
    m = (~np.isnan(values)).sum(axis=-1)
    safe = np.maximum(m, 1)
    if how == "mean":
        out = np.nansum(values, axis=-1) / safe
    elif how == "median":
        lo = np.take_along_axis(ordered, ((safe - 1) // 2)[..., None], axis=-1)[..., 0]
        hi = np.take_along_axis(ordered, (safe // 2)[..., None], axis=-1)[..., 0]
        out = (lo + hi) / 2
    elif how == "trimmed_mean_10":
        g = m // 10  # int(0.1 * m) without float rounding
        pos = np.arange(values.shape[-1])
        keep = (pos >= g[..., None]) & (pos < (m - g)[..., None])
        out = np.where(keep, np.nan_to_num(ordered), 0.0).sum(axis=-1) / np.maximum(m - 2 * g, 1)
    else:
        raise ValueError(f"unknown aggregation {how!r}; expected one of {AGGREGATIONS}")
    return np.where(m > 0, out, np.nan)


def repeat_composites(
    scores: np.ndarray,
    how: str,
    criteria: Sequence[str],
    composites: Mapping[str, Sequence[str]] = COMPOSITES,
) -> np.ndarray:
    """scores[..., repeat, criterion, policy, persona] -> composites[..., repeat, composite,
    policy]: panel aggregate per repeat, then the unweighted mean of each composite's criteria
    (NaN when any part is missing)."""
    panel = aggregate(scores, how)
    index = {c: i for i, c in enumerate(criteria)}
    return np.stack(
        [panel[..., [index[c] for c in parts], :].mean(axis=-2) for parts in composites.values()],
        axis=-2,
    )


def kendall_tau_b_rows(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Kendall tau-b over the last axis, batched over leading axes; positions NaN on either side
    are left out; NaN when undefined. Agrees with analysis_baseline.kendall_tau_b."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    n = x.shape[-1]
    i, j = np.triu_indices(n, k=1)
    dx = x[..., i] - x[..., j]
    dy = y[..., i] - y[..., j]
    valid = ~(np.isnan(dx) | np.isnan(dy))
    sx = np.where(valid, np.sign(np.nan_to_num(dx)), 0.0)
    sy = np.where(valid, np.sign(np.nan_to_num(dy)), 0.0)
    pairs = valid.sum(axis=-1)
    untied_x = pairs - (valid & (sx == 0)).sum(axis=-1)
    untied_y = pairs - (valid & (sy == 0)).sum(axis=-1)
    denom = np.sqrt(untied_x.astype(float) * untied_y)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(denom > 0, (sx * sy).sum(axis=-1) / np.where(denom > 0, denom, 1), np.nan)


def descending_ranks(scores: Mapping[str, float]) -> dict[str, float]:
    """Rank 1 = highest score; ties share their average rank (prereg s6)."""
    policies = list(scores)
    return dict(zip(policies, average_ranks([-scores[p] for p in policies]), strict=True))


def top_bottom_changes(
    b: Mapping[str, float], cell: Mapping[str, float], k: int = TOP_K
) -> tuple[tuple[str, ...], ...]:
    """(top-k entered, top-k left, bottom-k entered, bottom-k left) of the cell versus B. A policy
    is in the top k when its average rank is <= k, so a tie straddling the boundary is in neither
    set."""
    rb, rc = descending_ranks(b), descending_ranks(cell)
    n = len(rb)
    top_b, top_c = {p for p, r in rb.items() if r <= k}, {p for p, r in rc.items() if r <= k}
    bot_b = {p for p, r in rb.items() if r >= n - k + 1}
    bot_c = {p for p, r in rc.items() if r >= n - k + 1}
    return (
        tuple(sorted(top_c - top_b)), tuple(sorted(top_b - top_c)),
        tuple(sorted(bot_c - bot_b)), tuple(sorted(bot_b - bot_c)),
    )  # fmt: skip


@dataclass(frozen=True)
class CellComparison:
    cell_id: str
    aggregation: str
    composite: str
    pairing: str  # PAIRED | INDEPENDENT | NO_PERSONAS
    n_repeats: int
    n_policies: int  # scored on both sides
    tau: float  # NaN when undefined
    ci_low: float  # persona-bootstrap 2.5th percentile (secondary; prereg s3)
    ci_high: float
    n_boot_undefined: int  # replicates where tau was undefined (left out of the interval)
    single_run_min: float  # each cell repeat versus B's repeat mean
    single_run_max: float
    band_min: float  # repeat-noise split band for k = n_repeats; NaN when k >= B's repeats
    band_max: float
    top_entered: tuple[str, ...]
    top_left: tuple[str, ...]
    bottom_entered: tuple[str, ...]
    bottom_left: tuple[str, ...]
    rank_shifts: dict[str, tuple[float, float]]  # policy -> (rank in B, rank in cell)


@dataclass(frozen=True)
class NoiseSummary:
    """Tau among B's own repeats: "pairwise" single repeats or "split_k<k>" (k-mean vs rest)."""

    aggregation: str
    composite: str
    kind: str
    n: int
    minimum: float
    median: float
    maximum: float


@dataclass(frozen=True)
class AggregationAgreement:
    cell_id: str
    composite: str
    aggregation_a: str
    aggregation_b: str
    tau: float


@dataclass(frozen=True)
class RankStability:
    comparisons: list[CellComparison]
    noise: list[NoiseSummary]
    aggregation_agreement: list[AggregationAgreement]
    resamples: int
    seed: int
    b_repeats: int


def _reindex(arr: CellArray, personas: tuple[str, ...]) -> np.ndarray:
    out = np.full((*arr.scores.shape[:3], len(personas)), np.nan)
    pos = {p: i for i, p in enumerate(personas)}
    out[..., [pos[p] for p in arr.persona_ids]] = arr.scores
    return out


def align_cells(b: CellArray, cell: CellArray) -> tuple[np.ndarray, np.ndarray, str]:
    """Both score arrays ready to compare, and the pairing rule that applies."""
    if not cell.has_personas:
        return b.scores, cell.scores, NO_PERSONAS
    if not set(b.persona_ids) & set(cell.persona_ids):
        return b.scores, cell.scores, INDEPENDENT
    personas = tuple(sorted(set(b.persona_ids) | set(cell.persona_ids)))
    xb, xc = _reindex(b, personas), _reindex(cell, personas)
    both = ~np.isnan(xb[0]) & ~np.isnan(xc[0])
    xb[:, ~both] = np.nan
    xc[:, ~both] = np.nan
    return xb, xc, PAIRED


def _boot_means(
    scores: np.ndarray, idx: np.ndarray | None, how: str, criteria, composites, resamples: int
) -> np.ndarray:
    """Repeat-mean composites per bootstrap replicate: [replicate, composite, policy]."""
    if idx is None:
        point = repeat_composites(scores, how, criteria, composites).mean(axis=0)
        return np.broadcast_to(point, (resamples, *point.shape))
    parts = []
    for start in range(0, len(idx), _CHUNK):
        sub = np.moveaxis(np.take(scores, idx[start : start + _CHUNK], axis=-1), -2, 0)
        parts.append(repeat_composites(sub, how, criteria, composites).mean(axis=1))
    return np.concatenate(parts)


def _summary(values: np.ndarray) -> tuple[float, float, float]:
    ok = values[~np.isnan(values)]
    if not len(ok):
        return (np.nan, np.nan, np.nan)
    return (float(ok.min()), float(np.median(ok)), float(ok.max()))


def _noise(b: CellArray, how: str, ks: Iterable[int], composites) -> dict[str, np.ndarray]:
    """kind -> tau[split or pair, composite] among B's repeats."""
    per = repeat_composites(b.scores, how, b.criteria, composites)  # [repeat, composite, policy]
    n = len(b.repeats)
    out = {}
    pairs = list(itertools.combinations(range(n), 2))
    if pairs:
        out["pairwise"] = np.stack([kendall_tau_b_rows(per[r], per[s]) for r, s in pairs])
    for k in sorted(set(ks)):
        if not 1 <= k < n:
            continue
        taus = []
        for chosen in itertools.combinations(range(n), k):
            rest = [r for r in range(n) if r not in chosen]
            taus.append(kendall_tau_b_rows(per[list(chosen)].mean(0), per[rest].mean(0)))
        out[f"split_k{k}"] = np.stack(taus)
    return out


def _as_dict(policies: Sequence[str], values: np.ndarray) -> dict[str, float]:
    return {p: float(v) for p, v in zip(policies, values, strict=True) if not np.isnan(v)}


def rank_stability(
    b: CellArray,
    cells: Sequence[CellArray],
    *,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = 0,
    aggregations: Sequence[str] = AGGREGATIONS,
    composites: Mapping[str, Sequence[str]] = COMPOSITES,
) -> RankStability:
    """Every cell against B (all composites, all aggregations), B's repeat-noise reference, and
    the agreement between aggregations within each cell (B included)."""
    names = list(composites)
    comparisons: list[CellComparison] = []
    noise: list[NoiseSummary] = []
    agreement: list[AggregationAgreement] = []
    ks = {len(c.repeats) for c in cells}
    for how in aggregations:
        bands = _noise(b, how, ks, composites)
        for kind, taus in bands.items():
            for j, name in enumerate(names):
                lo, mid, hi = _summary(taus[:, j])
                noise.append(NoiseSummary(how, name, kind, len(taus), lo, mid, hi))
        for cell in cells:
            xb, xc, pairing = align_cells(b, cell)
            pb = repeat_composites(xb, how, b.criteria, composites)
            pc = repeat_composites(xc, how, cell.criteria, composites)
            mb, mc = pb.mean(axis=0), pc.mean(axis=0)
            tau = kendall_tau_b_rows(mb, mc)
            single = kendall_tau_b_rows(pc, mb[None])  # [repeat, composite]
            rng = np.random.default_rng(seed)  # common draws across cells
            idx_b = rng.integers(0, xb.shape[-1], size=(resamples, xb.shape[-1]))
            idx_c = {
                PAIRED: idx_b,
                NO_PERSONAS: None,
                INDEPENDENT: rng.integers(0, xc.shape[-1], size=(resamples, xc.shape[-1])),
            }[pairing]
            boot = kendall_tau_b_rows(
                _boot_means(xb, idx_b, how, b.criteria, composites, resamples),
                _boot_means(xc, idx_c, how, cell.criteria, composites, resamples),
            )  # [replicate, composite]
            band = bands.get(f"split_k{len(cell.repeats)}")
            for j, name in enumerate(names):
                sb, sc = _as_dict(b.policy_ids, mb[j]), _as_dict(cell.policy_ids, mc[j])
                common = sorted(set(sb) & set(sc))
                sb, sc = {p: sb[p] for p in common}, {p: sc[p] for p in common}
                rb, rc = descending_ranks(sb), descending_ranks(sc)
                ok = boot[:, j][~np.isnan(boot[:, j])]
                lo_ci, hi_ci = (
                    (float(np.percentile(ok, 2.5)), float(np.percentile(ok, 97.5)))
                    if len(ok) else (np.nan, np.nan)
                )  # fmt: skip
                s_lo, _, s_hi = _summary(single[:, j])
                b_lo, _, b_hi = _summary(band[:, j]) if band is not None else (np.nan,) * 3
                comparisons.append(
                    CellComparison(
                        cell.cell_id, how, name, pairing, len(cell.repeats), len(common),
                        float(tau[j]), lo_ci, hi_ci, int(resamples - len(ok)), s_lo, s_hi,
                        b_lo, b_hi, *top_bottom_changes(sb, sc),
                        {p: (rb[p], rc[p]) for p in common},
                    )
                )  # fmt: skip
    for cell in (b, *cells):
        means = {
            how: repeat_composites(cell.scores, how, cell.criteria, composites).mean(axis=0)
            for how in aggregations
        }
        for a, z in itertools.combinations(aggregations, 2):
            taus = kendall_tau_b_rows(means[a], means[z])
            for j, name in enumerate(names):
                agreement.append(AggregationAgreement(cell.cell_id, name, a, z, float(taus[j])))
    return RankStability(comparisons, noise, agreement, resamples, seed, len(b.repeats))
