"""EXPLORATORY reversed-scale probe (TASK-38): the pure analysis. Ratings are keyed
(persona, policy, criterion); the reversed run's raw scores are converted with 100 - x."""

import math

import pytest

from llm_panel.domain.analysis_baseline import COMPOSITES, TABLE4_CRITERIA
from scale_probe.analysis import (
    CONVERTED,
    UNCONVERTED,
    UNDECIDABLE,
    agreement,
    analyse,
    classify_call,
    compare,
    convert,
)

PERSONAS = ("p1", "p2", "p3")
# a clear ranking on every criterion: ubc > sawf > nit > ui > eitc, plus small persona effects
LEVELS = {"ubc": 85.0, "sawf": 70.0, "nit": 60.0, "ui": 40.0, "eitc": 30.0}
CRITERIA = TABLE4_CRITERIA


def _ratings(shift=0.0):
    out = {}
    for i, persona in enumerate(PERSONAS):
        for policy, level in LEVELS.items():
            for j, criterion in enumerate(CRITERIA):
                out[(persona, policy, criterion)] = level + i - 1 + (j % 3) * 0.5 + shift
    return out


def _mirror(ratings):
    return {k: 100.0 - v for k, v in ratings.items()}


def test_convert_maps_the_reversed_scale_back():
    assert convert(0.0) == 100.0
    assert convert(100.0) == 0.0
    assert convert(30.0) == 70.0


@pytest.mark.parametrize(
    ("raw", "base", "expected"),
    [
        ([20.0, 30.0], [80.0, 70.0], CONVERTED),  # the mirror image of the baseline call
        ([80.0, 70.0], [80.0, 70.0], UNCONVERTED),  # the model kept 100 = best
        ([50.0, 52.0], [52.0, 50.0], UNDECIDABLE),  # baseline mean 51: both readings agree
        ([40.0, 40.0], [45.0, 47.0], UNDECIDABLE),  # baseline mean 46, within 5 of 50
        ([30.0, 30.0], [56.0, 54.0], CONVERTED),  # nearer 100 - 55 = 45 than 55
    ],
)
def test_classify_call(raw, base, expected):
    assert classify_call(raw, base) == expected


def test_agreement_is_paired_on_common_keys_and_signed_other_minus_reference():
    ref = {("a", "x", "c"): 10.0, ("a", "y", "c"): 20.0, ("a", "z", "c"): 30.0}
    other = {
        ("a", "x", "c"): 12.0,
        ("a", "y", "c"): 22.0,
        ("a", "z", "c"): 32.0,
        ("b", "x", "c"): 0,
    }
    a = agreement(ref, other)
    assert a.n == 3
    assert a.r == pytest.approx(1.0)
    assert a.mean_signed == pytest.approx(2.0)
    assert a.mean_abs == pytest.approx(2.0)


def test_compare_identical_runs():
    base = _ratings()
    c = compare(base, base, target="ubc")
    assert c.n_personas == 3
    assert c.panel.mean_abs == 0.0
    assert c.beyond_m == []
    assert all(c.taus[k] == pytest.approx(1.0) for k in COMPOSITES)
    assert c.target_rank == 1.0
    assert c.clauses["a"].holds and c.clauses["b"].holds


def test_compare_counts_table4_units_beyond_m_with_their_shift():
    base = _ratings()
    other = dict(base)
    for p in PERSONAS:
        other[(p, "nit", "democratic_voice")] += 6.0  # > M = 5 at the panel mean
        other[(p, "ui", "democratic_voice")] += 5.0  # exactly M: not beyond
    c = compare(base, other, target="ubc")
    assert [(u.policy, u.criterion) for u in c.beyond_m] == [("nit", "democratic_voice")]
    assert c.beyond_m[0].shift == pytest.approx(6.0)


def test_compare_ignores_criteria_outside_table4_for_the_primary_count():
    base = _ratings()
    base.update({(p, "ubc", "political_support"): 50.0 for p in PERSONAS})
    other = dict(base)
    other.update({(p, "ubc", "political_support"): 90.0 for p in PERSONAS})
    assert compare(base, other, target="ubc").beyond_m == []


def test_analyse_a_faithful_mirror_matches_the_baseline_after_conversion():
    base = _ratings()
    rerun = _ratings(shift=0.5)
    result = analyse(base, rerun, _mirror(base), target="ubc")
    assert result.calls == {CONVERTED: 15, UNCONVERTED: 0, UNDECIDABLE: 0}
    assert result.reversed.panel.mean_abs == pytest.approx(0.0)
    assert result.reversed.target_rank == 1.0
    assert result.rerun.panel.mean_signed == pytest.approx(0.5)
    assert result.raw.r == pytest.approx(-1.0)  # raw reversed scores run against the baseline


def test_analyse_a_model_that_ignores_the_reversal_puts_the_target_last():
    base = _ratings()
    result = analyse(base, base, dict(base), target="ubc")  # raw scores kept 100 = best
    assert result.calls[UNCONVERTED] == 15
    assert result.reversed.target_rank == len(LEVELS)
    assert result.reversed.taus["full_transformation"] == pytest.approx(-1.0)
    assert result.converted_only is None  # no call left to compare


def test_analyse_converted_only_drops_calls_that_look_unconverted():
    base = _ratings()
    raw = _mirror(base)
    for criterion in CRITERIA:  # one call ignored the reversal
        raw[("p1", "ubc", criterion)] = base[("p1", "ubc", criterion)]
    result = analyse(base, base, raw, target="ubc")
    assert result.calls[UNCONVERTED] == 1
    assert result.reversed.panel.mean_abs > 0
    assert result.converted_only.panel.mean_abs == pytest.approx(0.0)
    assert result.converted_only.rating.n == len(base) - len(CRITERIA)


def test_a_call_missing_from_the_baseline_is_not_classified():
    base = _ratings()
    raw = _mirror(base)
    del base[("p1", "ubc", CRITERIA[0])]
    result = analyse(base, base, raw, target="ubc")
    assert sum(result.calls.values()) == 15  # p1 x ubc still has 10 criteria in common
    assert not math.isnan(result.reversed.rating.r)
