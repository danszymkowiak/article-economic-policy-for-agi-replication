"""TASK-19: rank stability between cells, on synthetic observations with known orderings."""

import math
import random

import numpy as np
import pytest

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    Observation,
    kendall_tau_b,
)
from llm_panel.domain.analysis_rank import (
    AGGREGATIONS,
    INDEPENDENT,
    NO_PERSONAS,
    PAIRED,
    PREREG_COMPOSITES,
    aggregate,
    build_cell_array,
    descending_ranks,
    kendall_tau_b_rows,
    rank_stability,
    top_bottom_changes,
)

POLICIES = tuple(f"pol{i:02d}" for i in range(11))
PERSONAS = tuple(f"p{i:02d}" for i in range(21))  # 21: 10% trim cuts 2 each end


def _obs(order, *, repeats=(0, 1, 2), personas=PERSONAS, noise=0.0, seed=0, outlier=None):
    """Every criterion scores policy i at order[i] (plus noise); optional per-persona override."""
    rng = random.Random(seed)
    out = []
    for r in repeats:
        for persona in personas:
            for i, policy in enumerate(POLICIES):
                for c in TABLE4_CRITERIA:
                    score = order[i] + (rng.uniform(-noise, noise) if noise else 0.0)
                    if outlier and persona in outlier:
                        score = outlier[persona][i]
                    out.append(Observation(r, persona, policy, c, min(100.0, max(0.0, score))))
    return out


ASC = [10.0 + 7 * i for i in range(11)]
DESC = list(reversed(ASC))


def _cell(cell_id, observations):
    return build_cell_array(cell_id, observations, policy_ids=POLICIES)


def _by(result, cell, aggregation="mean"):
    return {
        c.composite: c for c in result.comparisons
        if c.cell_id == cell and c.aggregation == aggregation
    }  # fmt: skip


def test_vectorised_tau_matches_pure_tau_b_with_ties():
    rng = random.Random(3)
    for _ in range(50):
        x = [float(rng.randint(0, 4)) for _ in range(11)]
        y = [float(rng.randint(0, 4)) for _ in range(11)]
        expected = kendall_tau_b(x, y)
        got = float(kendall_tau_b_rows(np.array(x), np.array(y)))
        if expected is None:
            assert math.isnan(got)
        else:
            assert got == pytest.approx(expected)


def test_vectorised_tau_leaves_out_missing_policies_and_handles_batches():
    x = np.array([[1.0, 2.0, 3.0, np.nan], [1.0, 2.0, 3.0, 4.0]])
    y = np.array([[1.0, 2.0, 3.0, 0.0], [4.0, 3.0, 2.0, 1.0]])
    assert kendall_tau_b_rows(x, y).tolist() == pytest.approx([1.0, -1.0])
    assert math.isnan(float(kendall_tau_b_rows(np.ones(4), np.arange(4.0))))


def test_aggregations_ignore_missing_and_trim_ten_percent_each_end():
    values = np.array([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 1000.0, np.nan]])
    assert aggregate(values, "mean")[0] == pytest.approx(1045 / 10)
    assert aggregate(values, "median")[0] == pytest.approx(5.5)
    # 10 valid values: one cut from each end (scipy trim_mean convention, int(0.1 * n))
    assert aggregate(values, "trimmed_mean_10")[0] == pytest.approx(sum(range(2, 10)) / 8)
    fifty_one = np.arange(51.0)[None, :]
    assert aggregate(fifty_one, "trimmed_mean_10")[0] == pytest.approx(np.arange(5, 46).mean())
    assert math.isnan(aggregate(np.full((1, 3), np.nan), "median")[0])


def test_descending_ranks_average_ties():
    assert descending_ranks({"a": 65.0, "b": 70.0, "c": 65.0}) == {"a": 2.5, "b": 1.0, "c": 2.5}


def test_top_bottom_changes_with_a_known_swap():
    b = {p: s for p, s in zip("abcdef", [6, 5, 4, 3, 2, 1], strict=True)}
    c = {**b, "c": 3.5, "d": 4.5}  # c and d swap ranks 3 and 4
    top_in, top_out, bottom_in, bottom_out = top_bottom_changes(b, c, k=3)
    assert (top_in, top_out) == (("d",), ("c",))
    assert (bottom_in, bottom_out) == (("c",), ("d",))


def test_incomplete_triplets_are_left_out_of_every_repeat():
    obs = [o for o in _obs(ASC) if not (o.repeat == 1 and o.persona_id == "p00")]
    arr = _cell("B", obs)
    assert arr.scores.shape == (3, len(TABLE4_CRITERIA), 11, len(PERSONAS))
    assert np.isnan(arr.scores[:, :, :, 0]).all()
    assert not np.isnan(arr.scores[:, :, :, 1:]).any()


def test_identical_cell_gives_tau_one_and_no_changes():
    b = _cell("B", _obs(ASC, noise=3.0, seed=1))
    same = _cell("Q1", _obs(ASC, noise=3.0, seed=1))
    result = rank_stability(b, [same], resamples=50, seed=0)
    for aggregation in AGGREGATIONS:
        rows = _by(result, "Q1", aggregation)
        assert set(rows) == set(COMPOSITES)
        for row in rows.values():
            assert row.pairing == PAIRED and row.n_policies == 11
            assert row.tau == pytest.approx(1.0)
            assert row.ci_low == pytest.approx(1.0) and row.ci_high == pytest.approx(1.0)
            assert row.top_entered == row.top_left == row.bottom_entered == () == row.bottom_left
            assert all(rb == rc for rb, rc in row.rank_shifts.values())


def test_reversed_cell_gives_tau_minus_one():
    b = _cell("B", _obs(ASC))
    rev = _cell("Q4", _obs(DESC))
    rows = _by(rank_stability(b, [rev], resamples=20, seed=0), "Q4")
    for row in rows.values():
        assert row.tau == pytest.approx(-1.0)
        assert row.single_run_min == pytest.approx(-1.0) == row.single_run_max
        assert set(row.top_entered) == {"pol00", "pol01", "pol02"}
    shifts = rows["full_transformation"].rank_shifts
    assert shifts["pol10"] == (1.0, 11.0) and shifts["pol00"] == (11.0, 1.0)


def test_noisy_cell_tau_is_between_and_ci_is_ordered_and_reproducible():
    near = [50.0 + 0.5 * i for i in range(11)]  # near-ties, so noise swaps some
    b = _cell("B", _obs(near, noise=10.0, seed=1))
    noisy = _cell("Q2a", _obs(near, noise=10.0, seed=2))
    first = _by(rank_stability(b, [noisy], resamples=200, seed=7), "Q2a")
    again = _by(rank_stability(b, [noisy], resamples=200, seed=7), "Q2a")
    for name, row in first.items():
        assert -1.0 <= row.ci_low <= row.ci_high <= 1.0
        assert 0.0 < row.tau < 1.0
        assert (row.ci_low, row.ci_high) == (again[name].ci_low, again[name].ci_high)
    assert min(r.tau for r in first.values()) < 1.0


def test_repeat_noise_reference_from_b_repeats():
    b = _cell("B", _obs(ASC, repeats=(0, 1, 2, 3, 4), noise=10.0, seed=4))
    cell = _cell("Q3a", _obs(ASC, repeats=(0, 1), noise=10.0, seed=5))
    result = rank_stability(b, [cell], resamples=10, seed=0)
    kinds = {(n.aggregation, n.kind) for n in result.noise}
    assert ("mean", "pairwise") in kinds and ("mean", "split_k2") in kinds
    pairwise = [n for n in result.noise if n.kind == "pairwise" and n.aggregation == "mean"]
    assert {n.composite for n in pairwise} == set(COMPOSITES)
    assert all(n.n == 10 and n.minimum <= n.median <= n.maximum for n in pairwise)
    split = [n for n in result.noise if n.kind == "split_k2" and n.aggregation == "mean"]
    assert all(n.n == 10 for n in split)  # C(5, 2) splits
    row = _by(result, "Q3a")["moderate_disruption"]
    match = next(n for n in split if n.composite == "moderate_disruption")
    assert (row.band_min, row.band_max) == (match.minimum, match.maximum)


def test_band_is_not_applicable_when_cell_has_as_many_repeats_as_b():
    b = _cell("B", _obs(ASC, repeats=(0, 1)))
    cell = _cell("Q1", _obs(ASC, repeats=(0, 1)))
    row = _by(rank_stability(b, [cell], resamples=5, seed=0), "Q1")["feasibility"]
    assert math.isnan(row.band_min) and math.isnan(row.band_max)


def test_outlier_persona_moves_mean_but_not_median():
    b = _cell("B", _obs(ASC))
    # two of 21 personas give an extreme profile; median and 10% trim both drop them
    outlier = {"p00": [100.0 if i == 0 else 0.0 for i in range(11)]}
    outlier["p01"] = outlier["p00"]
    cell = _cell("Q1", _obs(ASC, outlier=outlier))
    result = rank_stability(b, [cell], resamples=5, seed=0)
    assert _by(result, "Q1", "median")["full_transformation"].tau == pytest.approx(1.0)
    assert _by(result, "Q1", "mean")["full_transformation"].tau < 1.0
    agree = {
        (a.aggregation_a, a.aggregation_b): a.tau for a in result.aggregation_agreement
        if a.cell_id == "Q1" and a.composite == "full_transformation"
    }  # fmt: skip
    assert agree[("mean", "median")] < 1.0
    assert agree[("median", "trimmed_mean_10")] == pytest.approx(1.0)


def test_pairing_rules_for_other_panels_and_no_persona_cells():
    b = _cell("B", _obs(ASC))
    synthetic = _cell("D2b", _obs(ASC, personas=("s1", "s2", "s3")))
    no_persona = _cell("D2", _obs(ASC, personas=("none",), repeats=tuple(range(6))))
    result = rank_stability(b, [synthetic, no_persona], resamples=20, seed=0)
    assert _by(result, "D2b")["agency_voice"].pairing == INDEPENDENT
    d2 = _by(result, "D2")["agency_voice"]
    assert d2.pairing == NO_PERSONAS and d2.tau == pytest.approx(1.0)


def test_prereg_composites_are_the_durability_and_dimension_composites():
    assert set(PREREG_COMPOSITES) <= set(COMPOSITES)
    assert len(PREREG_COMPOSITES) == 7
