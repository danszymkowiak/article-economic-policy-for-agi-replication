"""TASK-20: variance components (balanced crossed random-effects ANOVA), planted shares."""

import math

import numpy as np
import pytest

from llm_panel.domain.analysis_rank import CellArray
from llm_panel.domain.analysis_variance import (
    criterion_agreement,
    decompose_cell,
    effective_n,
    factor_shift,
    panel_mean_run_spread,
    persona_cells,
    variance_components,
)


def _cell(scores, cell_id="B", personas=None):
    r, c, j, p = scores.shape
    return CellArray(
        cell_id,
        tuple(personas or (f"p{i:03d}" for i in range(p))),
        tuple(f"pol{i:02d}" for i in range(j)),
        tuple(f"crit{i:02d}" for i in range(c)),
        tuple(range(r)),
        scores,
    )


def test_persona_only_data_gives_persona_variance_exactly():
    a = np.array([1.0, 4.0, -2.0, 7.0, 0.5])
    x = np.repeat(a[:, None], 4, axis=1)  # [persona, repeat]
    comp = variance_components(x, ("persona", "repeat"))
    assert comp.estimate(("persona",)) == pytest.approx(np.var(a, ddof=1))
    assert comp.estimate(("repeat",)) == pytest.approx(0.0, abs=1e-12)
    assert comp.estimate(("persona", "repeat")) == pytest.approx(0.0, abs=1e-12)
    assert comp.share([("persona",)]) == pytest.approx(1.0)


def test_two_way_matches_textbook_formulas():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(7, 5))
    comp = variance_components(x, ("persona", "repeat"))
    n_p, n_r = x.shape
    grand = x.mean()
    ms_p = n_r * ((x.mean(1) - grand) ** 2).sum() / (n_p - 1)
    ms_r = n_p * ((x.mean(0) - grand) ** 2).sum() / (n_r - 1)
    resid = x - x.mean(1, keepdims=True) - x.mean(0, keepdims=True) + grand
    ms_e = (resid**2).sum() / ((n_p - 1) * (n_r - 1))
    assert comp.mean_square(("persona",)) == pytest.approx(ms_p)
    assert comp.estimate(("persona",)) == pytest.approx((ms_p - ms_e) / n_r)
    assert comp.estimate(("repeat",)) == pytest.approx((ms_r - ms_e) / n_p)
    assert comp.estimate(("persona", "repeat")) == pytest.approx(ms_e)


def test_size_one_axes_are_dropped_and_nan_is_refused():
    x = np.arange(12.0).reshape(1, 3, 4)
    comp = variance_components(x, ("repeat", "persona", "policy"))
    assert comp.factors == ("persona", "policy")
    assert not comp.identified(("repeat",))
    with pytest.raises(ValueError):
        variance_components(np.array([[1.0, np.nan], [2.0, 3.0]]), ("a", "b"))


def _planted(rng, sizes, sd):
    """scores[repeat, criterion, policy, persona] with independent normal effects."""
    n_r, n_c, n_j, n_p = sizes
    effects = {
        "persona": rng.normal(0, sd["persona"], (1, 1, 1, n_p)),
        "policy": rng.normal(0, sd["policy"], (1, 1, n_j, 1)),
        "criterion": rng.normal(0, sd["criterion"], (1, n_c, 1, 1)),
        "persona x policy": rng.normal(0, sd["pj"], (1, 1, n_j, n_p)),
        "repeat": rng.normal(0, sd["repeat"], (n_r, 1, 1, 1)),
        "residual": rng.normal(0, sd["residual"], sizes),
    }
    return 50 + sum(effects.values()), effects


SD = {"persona": 4.0, "policy": 10.0, "criterion": 5.0, "pj": 6.0, "repeat": 2.0, "residual": 3.0}


def test_planted_four_way_components_are_recovered():
    rng = np.random.default_rng(7)
    scores, eff = _planted(rng, (6, 11, 11, 60), SD)
    d = decompose_cell(_cell(scores))
    comp = d.components
    pj = eff["persona x policy"]
    pj_c = pj - pj.mean(axis=3, keepdims=True) - pj.mean(axis=2, keepdims=True) + pj.mean()
    var = {k: np.var(v.ravel(), ddof=1) for k, v in eff.items() if k != "residual"}
    v_pj = pj_c.var() * pj_c.size / ((11 - 1) * (60 - 1))
    # realized targets: a main effect's marginal means include the interaction's, and the
    # estimator subtracts the interaction's expected share of them (v_pj / levels averaged)
    realized = {
        **var,
        "persona": np.var((eff["persona"] + pj.mean(axis=2, keepdims=True)).ravel(), ddof=1)
        - v_pj / 11,
        "policy": np.var((eff["policy"] + pj.mean(axis=3, keepdims=True)).ravel(), ddof=1)
        - v_pj / 60,
        "persona x policy": v_pj,
    }
    assert comp.estimate(("persona",)) == pytest.approx(realized["persona"], rel=0.15)
    assert comp.estimate(("policy",)) == pytest.approx(realized["policy"], rel=0.1)
    assert comp.estimate(("criterion",)) == pytest.approx(realized["criterion"], rel=0.1)
    pj_est = comp.estimate(("persona", "policy"))
    assert pj_est == pytest.approx(realized["persona x policy"], rel=0.1)
    assert comp.estimate(("repeat",)) == pytest.approx(realized["repeat"], rel=0.15)
    top = ("persona", "policy", "criterion", "repeat")
    assert comp.estimate(top) == pytest.approx(9.0, rel=0.05)
    for zero in [("persona", "criterion"), ("policy", "criterion"), ("persona", "repeat")]:
        assert abs(comp.estimate(zero)) < 0.5
    total = sum(realized.values()) + 9.0
    persona_terms = realized["persona"] + realized["persona x policy"]
    assert d.persona_share == pytest.approx(persona_terms / total, abs=0.03)
    assert d.persona_main_share == pytest.approx(realized["persona"] / total, abs=0.02)
    assert d.repeat_share == pytest.approx((realized["repeat"] + 9.0) / total, abs=0.03)
    assert d.n_personas == 60 and d.n_personas_dropped == 0 and not d.noise_confounded


def test_decompose_cell_drops_incomplete_personas_and_flags_single_repeat():
    rng = np.random.default_rng(3)
    scores, _ = _planted(rng, (1, 3, 4, 6), SD)
    scores[:, 0, 1, 2] = np.nan
    d = decompose_cell(_cell(scores))
    assert d.n_personas == 5 and d.n_personas_dropped == 1
    assert d.noise_confounded  # no repeat axis: the top interaction holds the noise
    assert math.isnan(d.repeat_share)


def test_effective_n_formula():
    assert effective_n(51, 0.0) == pytest.approx(51)
    assert effective_n(51, 1.0) == pytest.approx(1)
    assert effective_n(51, 0.1) == pytest.approx(51 / (1 + 50 * 0.1))
    assert math.isnan(effective_n(51, math.nan))


def test_persona_cells_recover_persona_share_and_run_icc():
    rng = np.random.default_rng(11)
    n_r, n_p = 40, 40
    a = rng.normal(0, 3.0, n_p)  # persona: var 9
    b = rng.normal(0, 2.0, n_r)  # run shock shared by personas: var 4
    e = rng.normal(0, np.sqrt(3.0), (n_r, n_p))  # var 3
    scores = (60 + a[None, :] + b[:, None] + e)[:, None, None, :]
    (cell,) = persona_cells(_cell(scores))
    total = np.var(a, ddof=1) + np.var(b, ddof=1) + 3.0
    assert cell.persona_share == pytest.approx(np.var(a, ddof=1) / total, abs=0.04)
    assert cell.icc_run == pytest.approx(np.var(b, ddof=1) / total, abs=0.04)
    assert cell.n_eff_run == pytest.approx(effective_n(n_p, cell.icc_run))
    assert cell.n_personas == n_p and cell.n_repeats == n_r


def test_persona_cells_unidentified_with_one_repeat():
    scores = np.random.default_rng(0).normal(size=(1, 2, 3, 5))
    cells = persona_cells(_cell(scores))
    assert len(cells) == 6
    assert all(math.isnan(c.persona_share) and math.isnan(c.n_eff_run) for c in cells)


def test_criterion_agreement_recovers_shared_policy_view():
    rng = np.random.default_rng(5)
    n_r, n_j, n_p = 4, 11, 80
    view = rng.normal(0, 6.0, (1, 1, n_j, 1))  # the model's shared view of each policy
    own = rng.normal(0, 3.0, (1, 1, n_j, n_p))  # persona-specific view
    noise = rng.normal(0, 2.0, (n_r, 1, n_j, n_p))
    scores = 50 + view + own + noise + rng.normal(0, 4.0, (1, 1, 1, n_p))  # + persona main
    (agr,) = criterion_agreement(_cell(scores))
    j, pj = np.var(view.ravel(), ddof=1), np.var(own.ravel(), ddof=1)
    assert agr.icc_agree == pytest.approx(j / (j + pj + 4.0), abs=0.05)
    assert agr.persona_policy_share == pytest.approx(pj / (j + pj + 4.0), abs=0.03)
    assert agr.n_eff_agree == pytest.approx(effective_n(n_p, agr.icc_agree))


def _two_cells(rng, *, k_b=5, k_x=3, level=0.0, unit_sd=0.0, noise=2.0, run=1.0):
    n_c, n_j, n_p = 6, 11, 20
    truth = rng.normal(50, 10, (1, n_c, n_j, n_p))
    shift = level + rng.normal(0, unit_sd, (1, n_c, n_j, 1)) if unit_sd else level

    def draw(k, base):
        return (base + rng.normal(0, run, (k, 1, 1, 1))
                + rng.normal(0, noise, (k, n_c, n_j, n_p)))  # fmt: skip

    b, x = draw(k_b, truth), draw(k_x, truth + shift)
    return _cell(b), _cell(x, "Q1"), shift


def test_factor_shift_recovers_planted_level_and_unit_shift():
    rng = np.random.default_rng(2)
    b, x, shift = _two_cells(rng, level=3.0, unit_sd=4.0)
    fs = factor_shift(b, x)
    realized = np.var(np.asarray(shift).ravel(), ddof=1)
    assert abs(fs.level_shift - float(np.mean(shift))) < 3 * fs.level_se
    assert fs.shift_var == pytest.approx(realized, rel=0.25)
    assert fs.n_units == 66 and fs.k_b == 5 and fs.k_cell == 3
    assert fs.pairing == "paired" and fs.noise_source == "own"
    # panel-mean noise: persona x run noise var 4 / 20 personas = 0.2 per unit and run
    assert fs.noise_var_b == pytest.approx(0.2, rel=0.35)
    assert fs.ratio_to_noise > 10
    assert len(fs.band) == math.comb(5, 3)
    assert fs.ratio_to_noise > max(fs.band)


def test_factor_shift_without_change_sits_in_the_repeat_noise_band():
    rng = np.random.default_rng(4)
    b, x, _ = _two_cells(rng, k_x=2)
    fs = factor_shift(b, x)
    assert abs(fs.shift_var) < 0.1
    assert len(fs.band) == math.comb(5, 2)
    assert min(fs.band) < 0.5 and max(fs.band) > -0.5
    assert abs(fs.level_shift) < 4 * fs.level_se


def test_factor_shift_single_repeat_cell_borrows_b_noise_and_d2_style_cell():
    rng = np.random.default_rng(6)
    b, x, _ = _two_cells(rng, k_x=1, level=1.0)
    fs = factor_shift(b, x)
    assert fs.noise_source == "B" and fs.noise_var_cell == fs.noise_var_b
    no_persona = CellArray("D2", ("none",), b.policy_ids, b.criteria, (0, 1, 2),
                           b.scores[:3, :, :, :1])  # fmt: skip
    fs2 = factor_shift(b, no_persona)
    assert fs2.pairing == "no personas" and fs2.n_units == 66
    assert len(fs2.band) == math.comb(5, 3)
    many = CellArray("D2", ("none",), b.policy_ids, b.criteria, tuple(range(6)),
                     np.concatenate([b.scores, b.scores[:1]])[:, :, :, :1])  # fmt: skip
    assert factor_shift(b, many).band == ()  # k_cell >= k_b: no split of B has that size


def test_panel_mean_run_spread_is_the_sd_and_range_of_single_run_panel_means():
    scores = np.zeros((3, 2, 2, 2))  # repeat, criterion, policy, persona
    scores[:, 0, 0, :] = np.array([[10.0, 20.0], [12.0, 22.0], [14.0, 24.0]])  # means 15, 17, 19
    scores[:, 1, 1, 1] = np.nan  # crit01 x pol01: one persona left, panel mean 0 in every run
    spread = panel_mean_run_spread(_cell(scores))
    assert spread.n_runs == 3 and spread.n_units == 4
    assert max(spread.sds) == pytest.approx(2.0)
    assert max(spread.ranges) == pytest.approx(4.0)
    assert sorted(spread.sds)[:3] == [0.0, 0.0, 0.0]


def test_panel_mean_run_spread_keeps_only_the_named_criteria_and_needs_two_runs():
    scores = np.zeros((2, 2, 1, 2))
    scores[1, 1] += 3.0
    only = panel_mean_run_spread(_cell(scores), criteria=("crit00",))
    assert only.n_units == 1 and only.sds == (0.0,)
    assert panel_mean_run_spread(_cell(scores[:1])).n_units == 0
