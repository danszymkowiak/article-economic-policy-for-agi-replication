from dataclasses import replace

import pytest

from llm_panel.domain.models import Persona
from llm_panel.domain.oat_design import (
    DROP_FIRST,
    PARAPHRASE_LEVELS,
    PRIORITY_ORDER,
    DSettings,
    Factors,
    ModelRef,
    OatDesign,
    differing_factors,
    expand_cells,
    paired_persona_ids,
    plan_budget,
    run_order,
)

BASE = Factors(
    model=ModelRef("fake", "fake-1"),
    temperature=None,  # provider default
    persona_source="named",
    evidence="wikipedia",
)


def design(**kw):
    base = dict(
        baseline=BASE,
        k_r=5,
        k_q=3,
        rt_temperatures=(0.0, 1.0),
        d_cells={
            "D1": DSettings(),
            "D2": DSettings(),
            "D2b": DSettings(persona_source="synthetic"),
            "D3": DSettings(model=ModelRef("fake", "fake-2")),
        },
        base_seed=100,
        order_seed=7,
    )
    base.update(kw)
    return OatDesign(**base)


def by_id(cells):
    return {c.cell_id: c for c in cells}


# --- expansion (AC1) --------------------------------------------------------------------


def test_expands_every_prereg_cell_in_blocks_r_q_d():
    cells = by_id(expand_cells(design()))
    assert set(cells) == {
        "B", "B'", "R-T0", "R-T1",
        "Q1", "Q2a", "Q2b", "Q2c", "Q3a", "Q3b", "Q3c", "Q4",
        "D1", "D2", "D2b", "D3",
    }  # fmt: skip
    assert {cells[c].block for c in ("B", "B'", "R-T0", "R-T1")} == {"R"}
    assert {c.block for c in cells.values() if c.cell_id.startswith("Q")} == {"Q"}
    assert {c.block for c in cells.values() if c.cell_id.startswith("D")} == {"D"}


def test_repeat_counts_follow_k_r_and_k_q():
    # Prereg s8: B gets k_R, B' one, D2 d2_repeats (51); every Q, R-T and other D cell gets k_Q.
    cells = by_id(expand_cells(design()))
    assert cells["B"].repeats == 5 and cells["B'"].repeats == 1
    assert cells["D2"].repeats == 51  # 11 x 51 = 561 calls, one B repeat's worth
    assert all(c.repeats == 3 for c in cells.values() if c.cell_id not in ("B", "B'", "D2"))
    k4 = by_id(expand_cells(design(k_q=4, d2_repeats=7)))
    assert all(k4[c].repeats == 4 for c in ("R-T0", "R-T1", "D1", "D2b", "D3"))
    assert k4["D2"].repeats == 7


def test_b_prime_seed_differs_from_every_r_repeat_so_its_job_ids_are_new():
    cells = by_id(expand_cells(design()))
    assert cells["B"].seeds == (100, 101, 102, 103, 104)
    assert cells["B'"].seeds == (105,)
    assert cells["Q1"].seeds == (100, 101, 102)  # paired with B's first k_q repeats


def test_cell_factor_values():
    cells = by_id(expand_cells(design()))
    assert cells["B"].factors == BASE and cells["B'"].factors == BASE
    assert cells["R-T0"].factors.temperature == 0.0 and cells["R-T1"].factors.temperature == 1.0
    assert cells["Q1"].factors.policy_identifier == "definition_only"
    assert [cells[f"Q2{s}"].factors.description_wording for s in "abc"] == list(PARAPHRASE_LEVELS)
    assert [cells[f"Q3{s}"].factors.instruction_wording for s in "abc"] == list(PARAPHRASE_LEVELS)
    assert PARAPHRASE_LEVELS == ("para_1", "para_2", "para_3")
    assert cells["Q4"].factors.evidence == "none"
    assert cells["D1"].factors.call_unit == "joint"
    assert cells["D2"].factors.persona_source == "none"
    assert cells["D2b"].factors.persona_source == "synthetic"
    assert cells["D3"].factors.model == ModelRef("fake", "fake-2")


def test_unconfigured_d_cells_are_not_expanded():
    cells = by_id(expand_cells(design(d_cells={"D1": DSettings()})))
    assert "D1" in cells and not {"D2", "D2b", "D3"} & set(cells)


# --- one factor at a time and pairing (AC2) ---------------------------------------------


def test_every_q_and_r_t_cell_differs_from_baseline_in_exactly_one_factor():
    cells = expand_cells(design())
    checked = [c for c in cells if c.block == "Q" or c.cell_id.startswith("R-T")]
    assert len(checked) == 10
    for cell in checked:
        assert len(differing_factors(cell.factors, BASE)) == 1, cell.cell_id
    assert {differing_factors(c.factors, BASE)[0] for c in checked} == {
        "temperature", "policy_identifier", "description_wording", "instruction_wording",
        "evidence",
    }  # fmt: skip


def test_d_cells_also_change_one_factor_and_r_repeats_change_none():
    cells = by_id(expand_cells(design()))
    assert differing_factors(cells["B"].factors, BASE) == ()
    assert differing_factors(cells["B'"].factors, BASE) == ()
    assert differing_factors(cells["D1"].factors, BASE) == ("call_unit",)
    assert differing_factors(cells["D2"].factors, BASE) == ("persona_source",)
    assert differing_factors(cells["D2b"].factors, BASE) == ("persona_source",)
    assert differing_factors(cells["D3"].factors, BASE) == ("model",)


def _panel(source, n, prefix="p"):
    return tuple(Persona(id=f"{prefix}_{i:02d}", source=source, description="") for i in range(n))


def test_all_persona_cells_share_the_same_51_personas():
    cells = expand_cells(design())
    panels = {"named": _panel("named", 51), "synthetic": _panel("synthetic", 51, "econ")}
    ids = paired_persona_ids(cells, panels)
    assert len(ids) == 51 and ids == tuple(p.id for p in panels["named"])
    paired = [c for c in cells if c.cell_id not in ("D2", "D2b")]
    assert all(c.factors.persona_source == "named" for c in paired)


def test_paired_persona_check_rejects_wrong_panel_size():
    cells = expand_cells(design())
    with pytest.raises(ValueError, match="51"):
        paired_persona_ids(cells, {"named": _panel("named", 50)})


# --- validation -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kw",
    [
        dict(k_r=0),
        dict(k_q=0),
        dict(rt_temperatures=(0.0,)),
        dict(rt_temperatures=(0.5, 1.0)),  # must include temperature 0
        dict(rt_temperatures=(0.0, 0.0)),
        dict(baseline=replace(BASE, temperature=0.0)),  # R-T0 would equal B
        dict(baseline=replace(BASE, evidence="none")),
        dict(baseline=replace(BASE, persona_source="none")),
        dict(baseline=replace(BASE, description_wording="para_1")),
        dict(d_cells={"D9": DSettings()}),
        dict(d2_repeats=0),
        dict(d_cells={"D2b": DSettings()}),  # needs a persona source
        dict(d_cells={"D2b": DSettings(persona_source="named")}),
        dict(d_cells={"D3": DSettings()}),  # needs a model
        dict(d_cells={"D3": DSettings(model=ModelRef("fake", "fake-1"))}),
        dict(d_cells={"D1": DSettings(model=ModelRef("fake", "fake-2"))}),
    ],
)
def test_invalid_designs_rejected(kw):
    with pytest.raises(ValueError):
        expand_cells(design(**kw))


# --- run order (AC3) --------------------------------------------------------------------


def test_run_order_covers_every_repeat_once_and_records_seed():
    cells = expand_cells(design())
    order = run_order(cells, seed=7)
    assert order.seed == 7
    slots = [(s.cell_id, s.repeat) for s in order.slots]
    expected = [(c.cell_id, r) for c in cells for r in range(c.repeats)]
    assert sorted(slots) == sorted(expected) and len(slots) == len(set(slots))
    seeds = {(c.cell_id, r): c.seeds[r] for c in cells for r in range(c.repeats)}
    assert all(s.seed == seeds[(s.cell_id, s.repeat)] for s in order.slots)


def test_run_order_is_deterministic_per_seed_and_differs_across_seeds():
    cells = expand_cells(design())
    assert run_order(cells, seed=7) == run_order(cells, seed=7)
    assert run_order(cells, seed=7).slots != run_order(cells, seed=8).slots


def test_b_prime_runs_last():
    cells = expand_cells(design())
    for seed in range(5):
        assert run_order(cells, seed=seed).slots[-1].cell_id == "B'"


def test_run_order_interleaves_cells_rather_than_running_block_by_block():
    cells = expand_cells(design())
    ids = [s.cell_id for s in run_order(cells, seed=7).slots]
    runs = sum(1 for a, b in zip(ids, ids[1:], strict=False) if a != b) + 1
    n_cells = len({c.cell_id for c in cells})
    assert runs > 2 * n_cells  # block-by-block order would give exactly n_cells runs


# --- priority and cost-based stopping (AC4) ---------------------------------------------


def test_priority_order_and_drop_first_match_prereg_section_8():
    assert PRIORITY_ORDER == ("R", "Q1", "Q2", "Q4", "Q3", "R-T", "D2", "D2b", "D1", "D3")
    assert DROP_FIRST == ("Q3", "R-T", "D3")


def test_cells_carry_their_priority_unit():
    cells = by_id(expand_cells(design()))
    assert cells["B"].unit == cells["B'"].unit == "R"
    assert cells["Q2b"].unit == "Q2" and cells["Q3c"].unit == "Q3"
    assert cells["R-T0"].unit == cells["R-T1"].unit == "R-T"
    assert cells["D2b"].unit == "D2b"


def _costs(cells, each=1.0, **override):
    return {c.cell_id: override.get(c.cell_id, each) for c in cells}


def test_everything_runs_when_the_budget_covers_all():
    cells = expand_cells(design())
    plan = plan_budget(cells, _costs(cells), budget_usd=100.0)
    assert set(plan.run) == {c.cell_id for c in cells}
    assert plan.not_run == () and plan.dropped_first == ()
    assert plan.planned_cost_usd == pytest.approx(16.0)


def test_drop_first_units_are_removed_in_listed_order_until_the_rest_fits():
    cells = expand_cells(design())  # 16 cells at 1 USD; Q3 = 3, R-T = 2, D3 = 1
    plan = plan_budget(cells, _costs(cells), budget_usd=13.0)
    assert plan.dropped_first == ("Q3",)
    assert {"Q3a", "Q3b", "Q3c"} & set(plan.run) == set()
    assert {"R-T0", "R-T1", "D3"} <= set(plan.run)
    reasons = {n.cell_id: n.reason for n in plan.not_run}
    assert set(reasons) == {"Q3a", "Q3b", "Q3c"}
    assert all("dropped first" in r for r in reasons.values())

    plan = plan_budget(cells, _costs(cells), budget_usd=11.0)
    assert plan.dropped_first == ("Q3", "R-T")
    assert "D3" in plan.run


def test_after_drop_first_the_priority_order_stops_at_the_first_unit_that_does_not_fit():
    cells = expand_cells(design())
    # without Q3, R-T, D3: R(2) Q1(1) Q2(3) Q4(1) D2(1) D2b(1) D1(1) = 10
    plan = plan_budget(cells, _costs(cells), budget_usd=7.5)
    assert plan.dropped_first == DROP_FIRST
    assert set(plan.run) == {"B", "B'", "Q1", "Q2a", "Q2b", "Q2c", "Q4"}
    reasons = {n.cell_id: n.reason for n in plan.not_run}
    assert "budget" in reasons["D2"] and "budget" in reasons["D1"]
    assert plan.planned_cost_usd <= 7.5


def test_stopping_rule_does_not_skip_ahead_to_cheaper_lower_priority_units():
    cells = expand_cells(design())
    costs = _costs(cells, D2=5.0)
    plan = plan_budget(cells, costs, budget_usd=9.0)  # D2 does not fit; D2b and D1 would
    assert "D2" not in plan.run and "D2b" not in plan.run and "D1" not in plan.run


def test_nothing_runs_if_block_r_does_not_fit():
    cells = expand_cells(design())
    plan = plan_budget(cells, _costs(cells), budget_usd=1.5)
    assert plan.run == ()
    assert len(plan.not_run) == 16


def test_units_missing_from_the_design_are_reported_as_not_run():
    cells = expand_cells(design(d_cells={}))
    plan = plan_budget(cells, _costs(cells), budget_usd=100.0)
    missing = {n.cell_id: n.reason for n in plan.not_run}
    assert set(missing) == {"D1", "D2", "D2b", "D3"}
    assert all("not in design" in r for r in missing.values())


def test_missing_or_negative_cost_rejected():
    cells = expand_cells(design())
    costs = _costs(cells)
    del costs["Q1"]
    with pytest.raises(ValueError, match="Q1"):
        plan_budget(cells, costs, budget_usd=100.0)
    with pytest.raises(ValueError):
        plan_budget(cells, {**_costs(cells), "Q1": -1.0}, budget_usd=100.0)


def test_run_order_over_planned_cells_only():
    cells = expand_cells(design())
    plan = plan_budget(cells, _costs(cells), budget_usd=7.5)
    chosen = [c for c in cells if c.cell_id in plan.run]
    ids = {s.cell_id for s in run_order(chosen, seed=1).slots}
    assert ids == set(plan.run)
