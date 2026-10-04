import math

import pytest

from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    Observation,
    average_ranks,
    compare,
    composite_scores,
    kendall_tau_b,
    repeat_mean_panel,
    spearman,
)


def test_average_ranks_share_ties():
    assert average_ranks([10.0, 30.0, 20.0, 30.0]) == [1.0, 3.5, 2.0, 3.5]


def test_spearman_matches_reference_value_with_ties():
    # scipy.stats.spearmanr([1, 2, 3, 4, 5], [5, 6, 7, 8, 7]) = 0.8207826816681233
    assert spearman([1, 2, 3, 4, 5], [5, 6, 7, 8, 7]) == pytest.approx(0.8207826816681233)


def test_kendall_tau_b_matches_reference_value_with_ties():
    # scipy.stats.kendalltau([12, 2, 1, 12, 2], [1, 4, 7, 1, 0]) = -0.47140452079103173
    assert kendall_tau_b([12, 2, 1, 12, 2], [1, 4, 7, 1, 0]) == pytest.approx(-0.4714045207910317)


def test_perfect_and_reversed_order():
    x, y = [1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]
    assert spearman(x, y) == pytest.approx(1.0) and kendall_tau_b(x, y) == pytest.approx(1.0)
    assert spearman(x, y[::-1]) == pytest.approx(-1.0)
    assert kendall_tau_b(x, y[::-1]) == pytest.approx(-1.0)


def test_correlations_undefined_for_constant_or_tiny_inputs():
    assert spearman([1.0, 2.0, 3.0], [5.0, 5.0, 5.0]) is None
    assert kendall_tau_b([1.0, 2.0, 3.0], [5.0, 5.0, 5.0]) is None
    assert spearman([1.0], [2.0]) is None and kendall_tau_b([1.0], [2.0]) is None


def test_composites_follow_table4():
    assert COMPOSITES["welfare_resilience"] == (
        "standards_of_living", "meaning_human_value", "macro_stabilisation",
    )  # fmt: skip
    assert COMPOSITES["agency_voice"] == (
        "economic_agency_mobility", "ownership_of_gains", "democratic_voice",
    )  # fmt: skip
    # Table 4's Feasibility block holds only these two columns (see module docstring)
    assert COMPOSITES["feasibility"] == ("economic_feasibility", "implementation_readiness")
    assert COMPOSITES["scenario_durability"] == (
        "mild_disruption", "moderate_disruption", "full_transformation",
    )  # fmt: skip
    singles = [k for k, v in COMPOSITES.items() if v == (k,)]
    assert len(singles) == 11
    flat = {c for parts in COMPOSITES.values() for c in parts}
    assert "political_support" not in flat and "admin_capacity_speed" not in flat


def test_composite_scores_are_unweighted_means_and_need_every_part():
    scores = {
        "mild_disruption": {"a": 42.5, "b": 60.0},
        "moderate_disruption": {"a": 20.6, "b": 60.0},
        "full_transformation": {"a": 5.9},
    }
    out = composite_scores(scores, {"scenario_durability": COMPOSITES["scenario_durability"]})
    # paper text: ALMP "lowest durability score, with 23 on average" = mean(42.5, 20.6, 5.9)
    assert out["scenario_durability"] == {"a": pytest.approx(23.0)}


def _obs(repeat, persona, policy, score, criterion="c"):
    return Observation(repeat, persona, policy, criterion, score)


def test_repeat_mean_panel_uses_common_complete_pairs():
    observations = [
        _obs(0, "p1", "a", 10.0), _obs(1, "p1", "a", 20.0),
        _obs(0, "p2", "a", 90.0),  # p2 x a missing in repeat 1: dropped from both repeats
        _obs(0, "p1", "b", 40.0), _obs(1, "p1", "b", 60.0),
        _obs(0, "p2", "b", 50.0), _obs(1, "p2", "b", 70.0),
    ]  # fmt: skip
    panel = repeat_mean_panel(observations)
    assert panel.scores == {"c": {"a": pytest.approx(15.0), "b": pytest.approx(55.0)}}
    assert panel.n_repeats == 2
    assert panel.n_pairs == 3 and panel.dropped_pairs == 1


def test_repeat_mean_panel_averages_personas_within_repeat_then_repeats():
    observations = [
        _obs(0, "p1", "a", 0.0), _obs(0, "p2", "a", 100.0),
        _obs(1, "p1", "a", 20.0), _obs(1, "p2", "a", 40.0),
    ]  # fmt: skip
    assert repeat_mean_panel(observations).scores["c"]["a"] == pytest.approx((50.0 + 30.0) / 2)


def test_repeat_mean_panel_empty():
    panel = repeat_mean_panel([])
    assert panel.scores == {} and panel.n_repeats == 0 and panel.n_pairs == 0


def test_compare_reports_rank_correlations_and_mean_absolute_difference():
    ours = {"x": {"a": 10.0, "b": 20.0, "c": 30.0, "d": 45.0}}
    published = {"x": {"a": 12.0, "b": 25.0, "c": 22.0, "d": 40.0, "e": 50.0}}
    (agreement,) = compare(ours, published, ("x",))
    assert agreement.composite == "x"
    assert agreement.n_policies == 4  # only policies present on both sides
    assert agreement.spearman == pytest.approx(0.8)
    assert agreement.kendall_tau_b == pytest.approx(2 / 3)
    assert agreement.mean_abs_diff == pytest.approx((2 + 5 + 8 + 5) / 4)
    assert agreement.differences == {"a": -2.0, "b": -5.0, "c": 8.0, "d": 5.0}


def test_compare_with_no_overlap_is_reported_not_dropped():
    (agreement,) = compare({}, {"x": {"a": 1.0}}, ("x",))
    assert agreement.n_policies == 0
    assert agreement.spearman is None and agreement.kendall_tau_b is None
    assert math.isnan(agreement.mean_abs_diff)
