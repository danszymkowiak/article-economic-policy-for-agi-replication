"""Claude arm versus the main arm's B (TASK-35, prereg s9a comparison 1 and 2): the pure
comparison. Observations are parsed ratings (repeat, persona, policy, criterion)."""

import pytest

from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA, Observation
from subagent_arm.compare_b import (
    b_single_run_counts,
    compare_models,
    panel_means,
    shared_keys,
    units_beyond,
)

PERSONAS = ("n1", "n2")
LEVELS = {"ubc": 80.0, "sawf": 65.0, "nit": 55.0, "ui": 45.0, "eitc": 35.0}
CRITERIA = TABLE4_CRITERIA


def _obs(repeats, policies=tuple(LEVELS), shift=None, noise=0.0):
    shift = shift or {}
    out = []
    for r in repeats:
        for n in PERSONAS:
            for p in policies:
                for c in CRITERIA:
                    s = LEVELS[p] + shift.get((p, c), 0.0) + (noise if r % 2 else -noise)
                    out.append(Observation(r, n, p, c, s))
    return out


def test_panel_means_average_personas_then_repeats():
    obs = [Observation(0, "a", "x", "c", 10.0), Observation(0, "b", "x", "c", 20.0),
           Observation(1, "a", "x", "c", 30.0)]  # fmt: skip
    assert panel_means(obs) == {("x", "c"): pytest.approx((15.0 + 30.0) / 2)}


def test_shared_keys_need_every_b_repeat_and_the_claude_pass():
    b = _obs(range(3))
    b = [o for o in b if not (o.repeat == 2 and o.persona_id == "n1" and o.policy_id == "ubc")]
    c = _obs([0])
    keys = shared_keys(b, c)
    assert ("n1", "ubc", CRITERIA[0]) not in keys
    assert ("n2", "ubc", CRITERIA[0]) in keys


def test_units_beyond_m_strictly():
    ref = {("x", "a"): 50.0, ("x", "b"): 50.0}
    other = {("x", "a"): 55.0, ("x", "b"): 56.0}
    assert [(u.policy, u.criterion, u.shift) for u in units_beyond(ref, other)] == [("x", "b", 6.0)]


def test_b_single_run_counts_compare_each_repeat_with_the_mean_of_the_others():
    b = _obs(range(2), noise=3.0)  # repeats at -3 and +3: each 6 points from the other
    keys = shared_keys(b, b)
    assert b_single_run_counts(b, keys) == [len(LEVELS) * len(CRITERIA)] * 2
    assert b_single_run_counts(_obs(range(4)), keys) == [0, 0, 0, 0]


def test_compare_models_counts_shifts_and_keeps_b_clauses():
    b = _obs(range(3))
    c = _obs([0], shift={("ubc", "full_transformation"): -30.0})  # UBC falls to last on Full
    c += _obs([1, 2], policies=("ubc",), shift={("ubc", "full_transformation"): -30.0})
    res = compare_models(b, c)
    assert res.beyond_m_table4 == [("ubc", "full_transformation", pytest.approx(-30.0))]
    assert res.clauses_b["a"].holds
    assert res.clauses_claude["a"].holds is False
    assert [x["a"].holds for x in res.clauses_per_pass] == [False, False, False]
    assert res.taus["full_transformation"] < 1.0
    assert res.taus["ownership_of_gains"] == pytest.approx(1.0)
    ubc = {row.criterion: row for row in res.ubc_rows}
    assert ubc["full_transformation"].claude_mean == pytest.approx(50.0)
    assert ubc["full_transformation"].b_sd == pytest.approx(0.0)
    assert ubc["full_transformation"].claude_sd == pytest.approx(0.0)


def test_distribution_rows_describe_single_ratings_of_each_model():
    b = _obs([0, 1])
    c = _obs([0])
    res = compare_models(b, c)
    row = next(d for d in res.distribution if d.criterion == CRITERIA[0])
    assert row.b_mean == pytest.approx(sum(LEVELS.values()) / len(LEVELS))
    assert row.b_share_mult5 == pytest.approx(1.0)
    assert row.claude_mean == pytest.approx(row.b_mean)


def test_report_is_headed_as_a_separate_arm_with_the_bundle_caveat():
    from subagent_arm.compare_b import HEADER, render_markdown

    b = _obs(range(3))
    c = _obs([0]) + _obs([1, 2], policies=("ubc",))
    text = render_markdown(compare_models(b, c))
    assert text.startswith(HEADER)
    assert "model-and-harness bundles" in text
    assert "not that the recommendations are wrong" in text
