import pytest

from llm_panel.domain.models import Criterion, Persona, Policy
from llm_panel.domain.study_prompt import (
    DEFINITION_ONLY,
    JOINT,
    NAME_AND_DEFINITION,
    PERSONA_POLICY,
    PERSONA_PREAMBLE,
    check_template,
    neutral_codes,
    render_joint,
    render_persona_policy,
    select_template,
)

POLICIES = (
    Policy(id="eitc", name="Earned Income Tax Credit (EITC)", description="A refundable credit.",
           blinded_description="A refundable credit."),
    Policy(id="ubi", name="Universal Basic Income (UBI)", description="A cash transfer to all.",
           blinded_description="A cash transfer to all."),
)  # fmt: skip
CRITERIA = (
    Criterion(id="standards_of_living", name="Standards of Living", description="Alleviates."),
    Criterion(id="full_transformation", name="Full Transformation", description="Resilience."),
)
PERSONA = Persona(id="x", source="named", description="Your traits: {'name': 'A'}")
PP = "{persona_block}{evidence_block}Policy:\n{policy_block}\n\nCriteria:\n{criteria_block}\n{{}}"
JT = "{persona_block}{evidence_block}{criterion_name} - {criterion_description}\n{policy_block}"


def test_check_template_accepts_exact_placeholder_set():
    check_template(PERSONA_POLICY, PP)
    check_template(JOINT, JT)


@pytest.mark.parametrize(
    "unit,text",
    [
        (PERSONA_POLICY, "{persona_block}{evidence_block}{policy_block}"),  # missing criteria
        (PERSONA_POLICY, PP + "{criterion_name}"),  # extra placeholder
        (JOINT, PP),  # wrong unit's contract
        ("nope", PP),  # unknown call unit
    ],
)
def test_check_template_rejects_wrong_placeholders(unit, text):
    with pytest.raises(ValueError):
        check_template(unit, text)


def test_select_template_unknown_wording_fails():
    assert select_template({"baseline": PP}, "baseline") == PP
    with pytest.raises(ValueError, match="unknown"):
        select_template({"baseline": PP}, "para_9")


def test_neutral_codes_follow_input_order():
    assert neutral_codes(POLICIES) == {"eitc": "P1", "ubi": "P2"}


def test_persona_policy_named_shows_name_definition_all_criteria_persona_and_evidence():
    out = render_persona_policy(
        PP, PERSONA, POLICIES[0], "P1", CRITERIA, "Some evidence.", NAME_AND_DEFINITION
    )
    assert out.startswith(PERSONA_PREAMBLE)
    assert "Your traits: {'name': 'A'}" in out
    assert "Some evidence." in out
    assert "Earned Income Tax Credit (EITC): A refundable credit." in out
    for c in CRITERIA:
        assert c.id in out and c.name in out and c.description in out
    assert "{}" in out  # literal braces in a template survive formatting


def test_persona_policy_without_persona_or_evidence_omits_both_blocks():
    out = render_persona_policy(PP, None, POLICIES[0], "P1", CRITERIA, "", NAME_AND_DEFINITION)
    assert out.startswith("Policy:")


def test_definition_only_uses_code_and_definition_not_name():
    out = render_persona_policy(PP, PERSONA, POLICIES[0], "P1", CRITERIA, "", DEFINITION_ONLY)
    assert "P1: A refundable credit." in out
    assert "Earned Income" not in out and "EITC" not in out


def test_definition_override_replaces_the_definition():
    out = render_persona_policy(
        PP, PERSONA, POLICIES[0], "P1", CRITERIA, "", NAME_AND_DEFINITION,
        definition="Reworded credit.",
    )  # fmt: skip
    assert "Reworded credit." in out and "A refundable credit." not in out


def test_unknown_policy_identifier_fails():
    with pytest.raises(ValueError, match="identifier"):
        render_persona_policy(PP, PERSONA, POLICIES[0], "P1", CRITERIA, "", "nickname")


def test_joint_lists_every_policy_under_its_code():
    codes = neutral_codes(POLICIES)
    out = render_joint(JT, PERSONA, CRITERIA[0], POLICIES, codes, "", NAME_AND_DEFINITION)
    assert "Standards of Living - Alleviates." in out
    assert "[P1] Earned Income Tax Credit (EITC): A refundable credit." in out
    assert "[P2] Universal Basic Income (UBI): A cash transfer to all." in out
    blind = render_joint(JT, PERSONA, CRITERIA[0], POLICIES, codes, "", DEFINITION_ONLY)
    assert "[P2] A cash transfer to all." in blind and "UBI" not in blind


def test_render_rejects_template_breaking_the_contract():
    with pytest.raises(ValueError):
        render_persona_policy(JT, PERSONA, POLICIES[0], "P1", CRITERIA, "", NAME_AND_DEFINITION)
