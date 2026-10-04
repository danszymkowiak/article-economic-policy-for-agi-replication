"""TASK-21: recommendation clauses (prereg s6), score consistency, blinding gap. Pure."""

import copy
import math
from pathlib import Path

import numpy as np
import pytest

from llm_panel.bootstrap.published_loader import NET_APPROVAL, load_published
from llm_panel.domain.analysis_baseline import composite_scores
from llm_panel.domain.analysis_rank import CellArray
from llm_panel.domain.analysis_recommend import (
    CLAUSES,
    POLITICAL,
    RECOMMEND_COMPOSITES,
    analyse_cell,
    consistency,
    correlation,
    evaluate_clauses,
    margin_top_k,
    noise_floor,
    ownership_gap,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def table4():
    pub = load_published(ROOT / "analysis/published/paper_table4.csv")
    return pub, composite_scores(pub.scores, RECOMMEND_COMPOSITES)


def _scores(table4):
    return copy.deepcopy(table4[1])


def test_margin_top_k_is_gap_to_kth_best_other():
    s = {"a": 10.0, "b": 8.0, "c": 7.0, "d": 7.0}
    assert margin_top_k(s, "a", 1) == 2.0
    assert margin_top_k(s, "b", 1) == -2.0
    assert margin_top_k(s, "c", 2) == -1.0
    assert margin_top_k(s, "c", 3) == 0.0  # tie at the boundary: not strictly in the top 3
    assert math.isnan(margin_top_k(s, "zz", 1))
    assert math.isnan(margin_top_k({"a": 1.0}, "a", 1))  # no other policy


def test_published_table4_passes_every_clause_with_its_margins(table4):
    res = evaluate_clauses(_scores(table4))
    assert set(res) == set(CLAUSES)
    assert all(r.holds for r in res.values())
    assert res["a"].margin == pytest.approx(15.5)
    assert res["b"].margin == pytest.approx(40.0)
    assert res["c"].margin == pytest.approx(3.9)  # 69.8 - UI 65.9 (rank 4)
    assert res["d"].margin == pytest.approx(5.9)  # EITC 68.9 - UBC 63.0 on Mild
    assert res["d"].parts["eitc_top4_mild"] == pytest.approx(5.9)
    assert res["d"].parts["ubc_minus_ui_full"] == pytest.approx(43.4)
    assert res["sequence"].margin == pytest.approx(3.9)


def test_clause_a_fails_when_ubs_tops_full_transformation(table4):
    s = _scores(table4)
    s["full_transformation"]["ubs"] = 95.0
    res = evaluate_clauses(s)
    assert res["a"].holds is False and res["a"].margin == pytest.approx(-1.5)
    assert res["d"].holds  # UI and EITC still below UBC
    assert res["sequence"].holds is False


def test_clause_b_fails_when_sawf_owns_more(table4):
    s = _scores(table4)
    s["ownership_of_gains"]["sawf"] = 96.0
    res = evaluate_clauses(s)
    assert res["b"].holds is False and res["b"].margin == pytest.approx(-1.1)
    assert res["sequence"].holds  # (b) is not part of the sequence


def test_clause_c_fails_when_nit_drops_out_of_moderate_top3(table4):
    s = _scores(table4)
    s["moderate_disruption"]["nit"] = 60.0
    res = evaluate_clauses(s)
    # UI 65.9 is now the 3rd best other policy
    assert res["c"].holds is False and res["c"].margin == pytest.approx(60.0 - 65.9)
    assert res["sequence"].holds is False


def test_clause_d_fails_on_mild_rank_or_on_full_order(table4):
    s = _scores(table4)
    s["mild_disruption"]["eitc"] = 50.0
    assert evaluate_clauses(s)["d"].holds is False
    s = _scores(table4)
    s["full_transformation"]["ui"] = 94.0  # UI above UBC on Full (also breaks (a))
    res = evaluate_clauses(s)
    assert res["d"].holds is False and res["d"].parts["ubc_minus_ui_full"] < 0


def test_tie_for_rank_one_does_not_hold(table4):
    s = _scores(table4)
    s["ownership_of_gains"]["sawf"] = s["ownership_of_gains"]["ubc"]
    res = evaluate_clauses(s)
    assert res["b"].holds is False and res["b"].margin == 0.0


def test_missing_policy_leaves_clause_undefined(table4):
    s = _scores(table4)
    del s["full_transformation"]["ubc"]
    res = evaluate_clauses(s)
    assert res["a"].holds is None and math.isnan(res["a"].margin)
    assert res["d"].holds is None and res["sequence"].holds is None
    assert res["b"].holds  # unaffected


def test_consistency_on_published_scores(table4):
    s = _scores(table4)
    s[POLITICAL] = {p: 50.0 + i for i, p in enumerate(sorted(s["mild_disruption"]))}
    s[POLITICAL]["nit"] = 10.0  # lowest political support
    c = consistency(s, evaluate_clauses(s))
    assert c.leaders == {
        "mild_disruption": ("nit",), "moderate_disruption": ("ubs",),
        "full_transformation": ("ubc",), "scenario_durability": ("ubs",),
    }  # fmt: skip
    assert c.stage_follows == {
        "mild_disruption": False,
        "moderate_disruption": False,
        "full_transformation": True,
    }
    assert c.leaders_outside_sequence == {
        "mild_disruption": (), "moderate_disruption": ("ubs",),
        "full_transformation": (), "scenario_durability": ("ubs",),
    }  # fmt: skip
    assert c.ubs_leads is True and c.ubs_ranks["full_transformation"] == 2.0
    assert c.nit_political_rank == 11.0 and c.nit_low_political is True
    assert c.nit_despite_low_political is True
    assert c.almp_mild_rank == 8.0


def test_consistency_when_nit_is_politically_strong_and_ubs_trails(table4):
    s = _scores(table4)
    s[POLITICAL] = {p: 50.0 for p in s["mild_disruption"]}
    s[POLITICAL]["nit"] = 90.0
    durability = ("mild_disruption", "moderate_disruption", "full_transformation")
    for comp in durability:
        s[comp]["ubs"] = 10.0
    s["scenario_durability"]["ubs"] = 10.0
    c = consistency(s, evaluate_clauses(s))
    assert c.ubs_leads is False
    assert c.nit_political_rank == 1.0 and c.nit_low_political is False
    assert c.nit_despite_low_political is False


def test_consistency_without_political_support_is_undefined(table4):
    c = consistency(_scores(table4), evaluate_clauses(_scores(table4)))
    assert c.nit_low_political is None and c.nit_despite_low_political is None
    assert math.isnan(c.nit_political_rank)


def test_ownership_gap_and_published_correlations(table4):
    pub, s = table4
    assert ownership_gap(s) == pytest.approx(40.0)
    assert correlation(pub.scores[NET_APPROVAL], s["full_transformation"]) == pytest.approx(
        -0.569, abs=5e-4
    )
    assert correlation(s["implementation_readiness"], s["full_transformation"]) == pytest.approx(
        -0.51, abs=5e-3
    )
    assert math.isnan(correlation({"a": 1.0}, {"a": 2.0}))
    assert math.isnan(ownership_gap({}))


# --- per-cell analysis on arrays -------------------------------------------------------------

POLICIES = ("eitc", "ui", "almp", "wage_insurance", "directed_industrial_policy", "fjg", "ubi",
            "nit", "ubs", "ubc", "sawf")  # fmt: skip
CRITERIA = (
    "standards_of_living", "meaning_human_value", "macro_stabilisation",
    "economic_agency_mobility", "ownership_of_gains", "democratic_voice",
    "economic_feasibility", "implementation_readiness", "mild_disruption",
    "moderate_disruption", "full_transformation", POLITICAL,
)  # fmt: skip


def _array(pub, cell_id, n_repeats, n_personas=4, edits=None, noise=0.0, seed=0):
    """Every persona rates every policy at the published value, plus per-repeat edits
    {repeat: {(criterion, policy): value}} and optional noise."""
    rng = np.random.default_rng(seed)
    x = np.empty((n_repeats, len(CRITERIA), len(POLICIES), n_personas))
    for c, crit in enumerate(CRITERIA):
        for j, pol in enumerate(POLICIES):
            x[:, c, j, :] = pub.scores.get(crit, {}).get(pol, 50.0)
    for r, changes in (edits or {}).items():
        for (crit, pol), v in changes.items():
            x[r, CRITERIA.index(crit), POLICIES.index(pol), :] = v
    x += rng.normal(0, noise, x.shape)
    personas = tuple(f"p{i}" for i in range(n_personas))
    return CellArray(cell_id, personas, POLICIES, CRITERIA, tuple(range(n_repeats)), x)


def test_analyse_cell_counts_single_run_flips_in_b(table4):
    pub, _ = table4
    b = _array(pub, "B", 3, edits={1: {("full_transformation", "ubs"): 99.0}})
    res = analyse_cell(b, b, net_approval=pub.scores[NET_APPROVAL])
    # repeat mean: UBS (78+99+78)/3 = 85 < 93.5, so (a) holds in the mean
    assert res.mean.clauses["a"].holds and res.reference.clauses["a"].holds
    assert [run.clauses["a"].holds for run in res.runs] == [True, False, True]
    assert res.flip_count("a") == 1 and res.flip_count("b") == 0
    assert res.flip_count("sequence") == 1
    assert res.mean_flipped("a") is False
    assert -1 < res.mean.r_approval < 0 and -1 < res.mean.r_readiness < 0


def test_analyse_cell_blinding_moves_ownership_gap(table4):
    pub, _ = table4
    b = _array(pub, "B", 3)
    edit = {("ownership_of_gains", "ubc"): 60.0, ("ownership_of_gains", "sawf"): 70.0}
    q1 = _array(pub, "Q1", 2, edits={0: edit, 1: edit})
    res = analyse_cell(b, q1)
    assert res.reference.gap == pytest.approx(40.0)
    assert res.mean.gap == pytest.approx(-10.0)
    assert res.mean_flipped("b") is True and res.flip_count("b") == 2
    assert res.mean_flipped("a") is False
    assert res.pairing == "paired"


def test_analyse_cell_aligns_on_common_complete_triplets(table4):
    pub, _ = table4
    b = _array(pub, "B", 2)
    q = _array(pub, "Q4", 2)
    scores = q.scores.copy()
    scores[:, CRITERIA.index("ownership_of_gains"), POLICIES.index("ubc"), 0] = np.nan
    scores[:, CRITERIA.index("ownership_of_gains"), POLICIES.index("ubc"), 1:] = 0.0
    q = CellArray("Q4", q.persona_ids, POLICIES, CRITERIA, q.repeats, scores)
    res = analyse_cell(b, q)
    assert res.mean.scores["ownership_of_gains"]["ubc"] == 0.0  # persona 0 dropped
    assert res.reference.scores["ownership_of_gains"]["ubc"] == pytest.approx(94.9)


def test_noise_floor_split_flip_rates_and_gap_band(table4):
    pub, _ = table4
    b = _array(pub, "B", 4, edits={0: {("ownership_of_gains", "sawf"): 200.0}})
    floor = noise_floor(b, ks=[1, 2, 4])
    assert sorted(floor) == [1, 2]  # k >= n has no split
    k1 = floor[1]
    assert k1.n_splits == 4
    # chosen {0}: SAWF 200 > UBC (flip); rest mean SAWF 54.9 -> holds; other splits: chosen
    # holds, rest mean SAWF (200+2*54.9)/3 = 103.3 > 94.9 -> fails: every split differs.
    assert k1.flip_fraction["b"] == 1.0
    assert k1.flip_fraction["a"] == 0.0
    assert len(k1.gap_differences) == 4
    assert min(k1.gap_differences) < 0 < max(k1.gap_differences)
