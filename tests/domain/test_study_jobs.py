"""TASK-33: one-at-a-time cells -> rendered jobs (persona x policy with that policy's packet;
joint scoring for D1) and call counts."""

from collections import Counter

import pytest

from llm_panel.domain.models import Criterion, Persona, Policy
from llm_panel.domain.oat_design import (
    PARAPHRASE_LEVELS,
    DSettings,
    Factors,
    ModelRef,
    OatDesign,
    expand_cells,
)
from llm_panel.domain.study_jobs import (
    JOINT_EVIDENCE_SEPARATOR,
    StudyMaterials,
    count_cell_calls,
    jobs_for_cell,
)
from tests.name_patterns import names_found

PP = "{persona_block}{evidence_block}INSTR-{wording}\n{policy_block}\n{criteria_block}"
JT = (
    "{persona_block}{evidence_block}JOINT {criterion_name}: {criterion_description}\n{policy_block}"
)
POLICIES = (
    Policy("ubi", "Universal Basic Income (UBI)", "Everyone gets cash.", "Everyone gets cash."),
    Policy("nit", "Negative Income Tax (NIT)", "Low earners get cash.", "Low earners get cash."),
    Policy("ui", "Unemployment Insurance (UI)", "Job losers get cash.", "Job losers get cash."),
)
CRITERIA = (
    Criterion("standards_of_living", "Standards of Living", "Living standards."),
    Criterion("full_transformation", "Full Transformation", "Scenario: full."),
)
NAMED = tuple(Persona(f"n{i}", "named", f"Economist {i}") for i in range(4))
SYNTH = tuple(Persona(f"s{i}", "synthetic", f"Trait profile {i}") for i in range(4))
PACKETS = {
    "wikipedia": {
        "ubi": "# Evidence packet: Universal Basic Income (UBI)\nUBI pilots; unlike NIT.",
        "nit": "# Evidence packet: Negative Income Tax (NIT)\nNIT experiments.",
        "ui": "# Evidence packet: Unemployment Insurance (UI)\nUI raises search time.",
    }
}
PARAS = {lv: {p.id: f"{p.description} ({lv})" for p in POLICIES} for lv in PARAPHRASE_LEVELS}


def materials(**kw):
    base = dict(
        panels={"named": NAMED, "synthetic": SYNTH},
        policies=POLICIES,
        criteria=CRITERIA,
        packets=PACKETS,
        templates={
            "persona_policy": {
                w: PP.replace("{wording}", w) for w in ("baseline", *PARAPHRASE_LEVELS)
            },
            "joint": {"baseline": JT},
        },
        description_paraphrases=PARAS,
    )
    base.update(kw)
    return StudyMaterials(**base)


DESIGN = OatDesign(
    baseline=Factors(ModelRef("fake", "fake-1"), None, "named", "wikipedia"),
    k_r=2,
    k_q=1,
    d2_repeats=3,
    rt_temperatures=(0.0, 1.0),
    d_cells={
        "D1": DSettings(),
        "D2": DSettings(),
        "D2b": DSettings(persona_source="synthetic"),
        "D3": DSettings(model=ModelRef("fake", "fake-2")),
    },
    n_personas=4,
)
CELLS = {c.cell_id: c for c in expand_cells(DESIGN)}


def jobs(cell_id, m=None):
    return jobs_for_cell(CELLS[cell_id], m or materials())


def test_baseline_is_one_call_per_persona_policy_repeat_with_all_criteria():
    js = jobs("B")
    assert len(js) == 4 * 3 * 2
    assert Counter((j.persona_id, j.policy_ids, j.repeat) for j in js).most_common(1)[0][1] == 1
    for j in js:
        assert j.criterion_ids == ("standards_of_living", "full_transformation")
        assert j.criterion_id == "" and j.cell_id == "B" and j.temperature is None
        assert j.seed == DESIGN.base_seed + j.repeat


def test_each_job_carries_its_own_policys_packet_only():
    for j in jobs("B"):
        (pid,) = j.policy_ids
        assert PACKETS["wikipedia"][pid] in j.prompt
        others = [t for k, t in PACKETS["wikipedia"].items() if k != pid]
        assert not any(t in j.prompt for t in others)


def test_job_id_covers_the_evidence_text():
    other = {"wikipedia": {**PACKETS["wikipedia"], "ubi": "# Evidence packet: x\nDifferent."}}
    a = {(j.persona_id, j.policy_ids, j.repeat): j.job_id for j in jobs("B")}
    b = {
        (j.persona_id, j.policy_ids, j.repeat): j.job_id
        for j in jobs("B", materials(packets=other))
    }
    changed = {k for k in a if a[k] != b[k]}
    assert changed and all(k[1] == ("ubi",) for k in changed)


def test_q4_none_level_has_no_evidence_block():
    for j in jobs("Q4"):
        assert "Evidence:" not in j.prompt
    assert all("Evidence:" in j.prompt for j in jobs("B"))


def test_q1_shows_codes_and_a_denamed_packet():
    js = jobs("Q1")
    assert len(js) == 4 * 3
    for j in js:
        assert names_found(j.prompt) == [], j.prompt
        (pid,) = j.policy_ids
        code = {"ubi": "P1", "nit": "P2", "ui": "P3"}[pid]
        assert j.policy_labels == (code,)
        assert f"# Evidence packet: {code}" in j.prompt


def test_q2_uses_the_description_paraphrase_and_q3_the_instruction_paraphrase():
    for j in jobs("Q2b"):
        assert "(para_2)" in j.prompt and "INSTR-baseline" in j.prompt
    for j in jobs("Q3c"):
        assert "INSTR-para_3" in j.prompt and "(para_" not in j.prompt


def test_rt_cells_set_temperature():
    assert {j.temperature for j in jobs("R-T0")} == {0.0}
    assert {j.temperature for j in jobs("R-T1")} == {1.0}


def test_d2_has_no_persona_and_its_own_repeats():
    js = jobs("D2")
    assert len(js) == 3 * 3
    assert {j.persona_id for j in js} == {"none"}
    assert all("Economist" not in j.prompt for j in js)


def test_d2b_and_d3_change_only_personas_or_model():
    assert {j.persona_id for j in jobs("D2b")} == {p.id for p in SYNTH}
    assert {j.model_snapshot for j in jobs("D3")} == {"fake-2"}


def test_d1_joint_is_one_call_per_persona_criterion_with_every_packet_in_order():
    js = jobs("D1")
    assert len(js) == 4 * 2
    evidence = JOINT_EVIDENCE_SEPARATOR.join(PACKETS["wikipedia"][p.id] for p in POLICIES)
    for j in js:
        assert j.criterion_ids == () and j.criterion_id in {c.id for c in CRITERIA}
        assert j.policy_ids == ("ubi", "nit", "ui") and j.policy_labels == ("P1", "P2", "P3")
        assert evidence in j.prompt and "JOINT" in j.prompt


def test_no_job_ids_collide_across_cells():
    all_ids = [j.job_id for c in CELLS for j in jobs(c)]
    assert len(all_ids) == len(set(all_ids))


@pytest.mark.parametrize("cell_id", sorted(CELLS))
def test_count_matches_the_jobs_built(cell_id):
    c = count_cell_calls(CELLS[cell_id], materials())
    js = jobs(cell_id)
    assert c.calls == len(js)
    assert c.ratings == sum(j.n_ratings for j in js)


def test_counts_at_study_size_561_per_baseline_repeat_663_per_joint_repeat():
    named = tuple(Persona(f"n{i}", "named", "") for i in range(51))
    pols = tuple(Policy(f"p{i}", f"Policy {i}", "d", "d") for i in range(11))
    crits = tuple(Criterion(f"c{i}", f"C{i}", "d") for i in range(13))
    m = materials(panels={"named": named, "synthetic": named}, policies=pols, criteria=crits)
    one = {cid: count_cell_calls(c, m) for cid, c in CELLS.items()}
    assert one["B"].calls == 561 * DESIGN.k_r and one["B"].ratings == 7293 * DESIGN.k_r
    assert one["D1"].calls == 663 * DESIGN.k_q and one["D1"].ratings == 7293 * DESIGN.k_q
    assert one["D2"].calls == 11 * DESIGN.d2_repeats


def test_missing_packet_is_an_error():
    short = {"wikipedia": {"ubi": "x", "nit": "y"}}
    with pytest.raises(ValueError, match="no evidence packet"):
        jobs("B", materials(packets=short))
