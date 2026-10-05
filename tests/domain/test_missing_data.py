"""TASK-37: missing data. In a no-persona cell (D2) a failed call drops only its repeat x policy;
survivor-only means and the worst-case bound with failures imputed at 0 and 100 (prereg s7)."""

from pathlib import Path

import numpy as np
import pytest

from llm_panel.bootstrap.published_loader import load_published
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA, Observation
from llm_panel.domain.analysis_materiality import materiality
from llm_panel.domain.analysis_missing import (
    Failure,
    unit_means,
    variant_comparison,
    variant_observations,
)
from llm_panel.domain.analysis_rank import (
    CellArray,
    build_cell_array,
    complete_repeats,
    rank_stability,
)
from llm_panel.domain.analysis_recommend import RECOMMEND_CRITERIA, analyse_cell
from llm_panel.domain.analysis_variance import decompose_cell, factor_shift

ROOT = Path(__file__).resolve().parents[2]
CRIT = ("crit0", "crit1")
POLS = ("pol0", "pol1", "pol2")


def _grid(personas, repeats, score=50.0, *, skip=(), policies=POLS, criteria=CRIT):
    """Every rating at `score`; `skip` holds (repeat, persona, policy) calls that failed."""
    return [
        Observation(r, n, p, c, score)
        for r in repeats for n in personas for p in policies for c in criteria
        if (r, n, p) not in skip
    ]  # fmt: skip


def _build(cell_id, obs, **kw):
    return build_cell_array(cell_id, obs, policy_ids=kw.pop("policies", POLS),
                            criteria=kw.pop("criteria", CRIT), **kw)  # fmt: skip


def test_no_persona_cell_drops_only_the_failed_call():
    d2 = _build("D2", _grid(("none",), range(4), skip={(2, "none", "pol1")}))
    assert np.isnan(d2.scores[2, :, 1, 0]).all()
    assert not np.isnan(np.delete(d2.scores, 2, axis=0)).any()
    assert not np.isnan(d2.scores[2, :, [0, 2], 0]).any()


def test_persona_cell_keeps_the_common_complete_rule_unless_asked():
    obs = _grid(("p0", "p1"), range(3), skip={(1, "p1", "pol1")})
    cc = _build("B", obs)
    assert np.isnan(cc.scores[:, :, 1, 1]).all()  # the pair is gone from every repeat
    assert not np.isnan(cc.scores[:, :, 1, 0]).any()
    raw = _build("B", obs, common_complete=False)
    assert np.isnan(raw.scores[1, :, 1, 1]).all()
    assert not np.isnan(raw.scores[[0, 2], :, 1, 1]).any()


def test_complete_repeats_marks_repeats_without_a_failed_call():
    d2 = _build("D2", _grid(("none",), range(4), skip={(2, "none", "pol1")}))
    assert complete_repeats(d2.scores).tolist() == [True, True, False, True]
    cc = _build("B", _grid(("p0", "p1"), range(3), skip={(1, "p1", "pol1")}))
    assert complete_repeats(cc.scores).all()
    unrated = _build("D2", _grid(("none",), range(2), policies=POLS[:2]))  # pol2 never rated
    assert complete_repeats(unrated.scores).all()


def _d2_with_gap(rng, value=60.0):
    """B: 3 repeats x 5 personas around 50; D2: 6 repeats, pol1 at `value`, one call failed."""
    b = _build("B", [
        Observation(o.repeat, o.persona_id, o.policy_id, o.criterion_id,
                    o.score + rng.normal(0, 1))
        for o in _grid(tuple(f"p{i}" for i in range(5)), range(3))
    ])  # fmt: skip
    obs = [
        Observation(o.repeat, o.persona_id, o.policy_id, o.criterion_id,
                    (value if o.policy_id == "pol1" else o.score) + rng.normal(0, 1))
        for o in _grid(("none",), range(6), skip={(4, "none", "pol1")})
    ]  # fmt: skip
    return b, _build("D2", obs)


def test_materiality_keeps_the_policy_with_a_failed_call():
    b, d2 = _d2_with_gap(np.random.default_rng(0))
    res = materiality(b, d2)
    assert res.n_units == len(POLS) * len(CRIT)
    pol1 = [u for u in res.units if u.policy_id == "pol1"]
    assert all(u.shift == pytest.approx(10.0, abs=2.0) for u in pol1)
    expected = np.nanmean(d2.scores[:, 0, 1, 0])  # mean over the 5 surviving repeats
    assert pol1[0].cell_mean == pytest.approx(expected)
    assert np.isfinite(res.noise_se) and res.noise_source == "own"


def test_variance_uses_the_complete_repeats_of_a_no_persona_cell():
    b, d2 = _d2_with_gap(np.random.default_rng(1))
    dec = decompose_cell(d2)
    assert dec.n_repeats == 5 and dec.n_policies == 3 and dec.components is not None
    fs = factor_shift(b, d2)
    assert fs.n_units == 6 and fs.k_cell == 5


def test_rank_stability_ranks_every_policy_of_a_no_persona_cell():
    b, d2 = _d2_with_gap(np.random.default_rng(2), value=90.0)
    criteria = {"c": CRIT}
    res = rank_stability(b, [d2], resamples=10, aggregations=("mean",), composites=criteria)
    (cmp,) = res.comparisons
    assert cmp.n_policies == 3
    assert not np.isnan(cmp.single_run_min) and not np.isnan(cmp.tau)


@pytest.fixture(scope="module")
def table4():
    return load_published(ROOT / "analysis/published/paper_table4.csv")


def _published_array(pub, cell_id, n_repeats, personas):
    x = np.empty((n_repeats, len(RECOMMEND_CRITERIA), len(pub.policy_order), len(personas)))
    for c, crit in enumerate(RECOMMEND_CRITERIA):
        for j, pol in enumerate(pub.policy_order):
            x[:, c, j, :] = pub.scores.get(crit, {}).get(pol, 50.0)
    return CellArray(cell_id, personas, pub.policy_order, RECOMMEND_CRITERIA,
                     tuple(range(n_repeats)), x)  # fmt: skip


def test_recommendations_keep_policies_and_take_single_runs_from_complete_repeats(table4):
    b = _published_array(table4, "B", 3, ("p0", "p1"))
    d2 = _published_array(table4, "D2", 4, ("none",))
    d2.scores[0, :, table4.policy_order.index("ubc"), 0] = np.nan
    res = analyse_cell(b, d2)
    assert res.mean.clauses["a"].holds is True
    assert res.mean.clauses["a"].margin == pytest.approx(15.5)
    assert len(res.runs) == 3


def test_variant_observations_drop_or_impute_failed_calls():
    obs = _grid(("p0", "p1"), range(2), skip={(0, "p1", "pol0")})
    fail = Failure(0, "p1", ("pol0",), CRIT)
    assert variant_observations(obs, [fail], "survivor") == obs
    low = variant_observations(obs, [fail], "impute_0")
    added = low[len(obs) :]
    assert {(o.repeat, o.persona_id, o.policy_id, o.score) for o in added} == {
        (0, "p1", "pol0", 0.0)
    }
    assert {o.criterion_id for o in added} == set(CRIT)
    high = variant_observations(obs, [fail], "impute_100")
    assert {o.score for o in high[len(obs) :]} == {100.0}
    with pytest.raises(ValueError):
        variant_observations(obs, [fail], "impute_50")


def test_unit_means_average_surviving_personas_then_repeats():
    obs = [Observation(0, "p0", "pol0", "crit0", 40.0), Observation(0, "p1", "pol0", "crit0", 60.0),
           Observation(1, "p0", "pol0", "crit0", 80.0)]  # fmt: skip
    cell = _build("B", obs, common_complete=False, policies=("pol0",), criteria=("crit0",))
    assert unit_means(cell)[0, 0] == pytest.approx((50.0 + 80.0) / 2)


def _variant_cell(cell_id, obs, failures, variant):
    return build_cell_array(cell_id, variant_observations(obs, failures, variant),
                            policy_ids=POLS, criteria=TABLE4_CRITERIA,
                            common_complete=False)  # fmt: skip


def test_variant_comparison_counts_units_beyond_m_under_each_imputation():
    personas = ("p0", "p1")
    b_obs = _grid(personas, range(2), criteria=TABLE4_CRITERIA)
    q_obs = _grid(personas, range(2), skip={(0, "p1", "pol0")}, criteria=TABLE4_CRITERIA)
    fails = [Failure(0, "p1", ("pol0",), TABLE4_CRITERIA)]
    counts = {}
    for variant in ("survivor", "impute_0", "impute_100"):
        b = _variant_cell("B", b_obs, [], variant)
        q = _variant_cell("Q1", q_obs, fails, variant)
        res = variant_comparison(b, q)
        assert res.n_units == len(POLS) * len(TABLE4_CRITERIA)
        counts[variant] = res.beyond
    # pol0: survivors 50; at 0 the repeat-0 panel mean is 25, so (25 + 50) / 2 = 37.5
    assert counts == {"survivor": 0, "impute_0": 11, "impute_100": 11}


def test_variant_comparison_reports_clauses_under_imputation(table4):
    pols = table4.policy_order
    obs = [
        Observation(0, n, p, c, table4.scores.get(c, {}).get(p, 50.0))
        for n in ("p0", "p1") for p in pols for c in RECOMMEND_CRITERIA
        if not (n == "p1" and p == "ubc")
    ]  # fmt: skip
    fails = [Failure(0, "p1", ("ubc",), RECOMMEND_CRITERIA)]
    out = {}
    for variant in ("survivor", "impute_0", "impute_100"):
        cell = build_cell_array("D2", variant_observations(obs, fails, variant), policy_ids=pols,
                                criteria=RECOMMEND_CRITERIA, common_complete=False)  # fmt: skip
        out[variant] = variant_comparison(cell, cell).clauses
    assert out["survivor"]["a"] is True and out["impute_100"]["a"] is True
    assert out["impute_0"]["a"] is False  # UBC's Full Transformation mean is halved


def test_no_persona_cell_without_a_complete_repeat_is_not_estimable_rather_than_an_error():
    b, _ = _d2_with_gap(np.random.default_rng(3))
    skip = {(0, "none", "pol0"), (1, "none", "pol1")}
    d2 = _build("D2", _grid(("none",), range(2), skip=skip))
    fs = factor_shift(b, d2)
    assert fs.k_cell == 0 and np.isnan(fs.shift_var)
    assert decompose_cell(d2).components is None
    mat = materiality(b, d2)
    assert mat.noise_source == "B" and not np.isnan(mat.noise_se)  # borrows B's noise
