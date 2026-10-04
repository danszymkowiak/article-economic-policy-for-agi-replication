"""The study's real inputs and prompt drafts (TASK-16): criteria, policies, templates,
paraphrases and their hash manifest."""

import re
from pathlib import Path

import pytest
import yaml

from llm_panel.bootstrap.inputs_loader import load_inputs
from llm_panel.bootstrap.prompt_files import (
    file_sha256,
    load_description_paraphrases,
    load_templates,
    manifest_mismatches,
)
from llm_panel.domain.models import Persona
from llm_panel.domain.oat_design import (
    DEFINITION_ONLY,
    JOINT,
    NAME_AND_DEFINITION,
    PARAPHRASE_LEVELS,
    PERSONA_POLICY,
)
from llm_panel.domain.study_prompt import neutral_codes, render_joint, render_persona_policy

REPO = Path(__file__).parents[2]
INPUTS = REPO / "designs" / "inputs"
PROMPTS = REPO / "prompts"
PARAPHRASES = INPUTS / "description_paraphrases"

CRITERION_IDS = (
    "standards_of_living", "meaning_human_value", "macro_stabilisation",
    "economic_agency_mobility", "ownership_of_gains", "democratic_voice",
    "political_support", "economic_feasibility", "admin_capacity_speed",
    "implementation_readiness",
    "mild_disruption", "moderate_disruption", "full_transformation",
)  # fmt: skip
POLICY_IDS = (
    "eitc", "ui", "almp", "wage_insurance", "directed_industrial_policy", "fjg",
    "ubi", "nit", "ubs", "ubc", "sawf",
)  # fmt: skip
# Every name, short name and acronym that would identify a policy (Q1 must show none of them).
NAME_PATTERNS = (
    r"earned income", r"\bEITC\b", r"unemployment insurance", r"\bUI\b", r"active labou?r",
    r"\bALMPs?\b", r"wage insurance", r"industrial policy", r"jobs? guarantee", r"\bFJG\b",
    r"basic income", r"\bUBI\b", r"negative income tax", r"\bNIT\b", r"basic services",
    r"\bUBS\b", r"basic capital", r"\bUBC\b", r"sovereign", r"\bSAWF\b", r"AI fund",
    r"AI dividend",
)  # fmt: skip
PERSONA = Persona(id="p", source="named", description="Your traits: {'name': 'A B'}")
LEFTOVER = re.compile(r"\{[a-z_]+\}")


@pytest.fixture(scope="module")
def inputs():
    return load_inputs(INPUTS)


@pytest.fixture(scope="module")
def templates():
    return load_templates(PROMPTS)


def test_criteria_count_and_ids(inputs):
    assert tuple(c.id for c in inputs.criteria) == CRITERION_IDS
    assert all(c.name and c.description and c.group for c in inputs.criteria)


def test_policies_are_the_eleven_table3_policies_in_order(inputs):
    assert tuple(p.id for p in inputs.policies) == POLICY_IDS
    assert neutral_codes(inputs.policies)["sawf"] == "P11"


def test_templates_present_for_both_call_units(templates):
    assert set(templates) == {PERSONA_POLICY, JOINT}
    assert set(templates[PERSONA_POLICY]) == {"baseline", *PARAPHRASE_LEVELS}
    assert set(templates[JOINT]) == {"baseline"}


def test_every_persona_policy_template_renders_completely(inputs, templates):
    codes = neutral_codes(inputs.policies)
    for wording, text in templates[PERSONA_POLICY].items():
        for ident in (NAME_AND_DEFINITION, DEFINITION_ONLY):
            for p in inputs.policies:
                out = render_persona_policy(
                    text, PERSONA, p, codes[p.id], inputs.criteria, "Ev.", ident
                )
                assert not LEFTOVER.search(out), (wording, ident, p.id)
                assert all(c.id in out for c in inputs.criteria)


def test_joint_template_renders_completely(inputs, templates):
    codes = neutral_codes(inputs.policies)
    for c in inputs.criteria:
        out = render_joint(
            templates[JOINT]["baseline"],
            PERSONA,
            c,
            inputs.policies,
            codes,
            "",
            NAME_AND_DEFINITION,
        )
        assert not LEFTOVER.search(out)
        assert all(f"[{code}]" in out for code in codes.values())


def test_description_only_prompt_shows_no_policy_name(inputs, templates):
    codes = neutral_codes(inputs.policies)
    levels = load_description_paraphrases(PARAPHRASES, POLICY_IDS)
    definitions = [None] + [levels[lv] for lv in PARAPHRASE_LEVELS]
    for text in templates[PERSONA_POLICY].values():
        for defs in definitions:
            for p in inputs.policies:
                out = render_persona_policy(
                    text, None, p, codes[p.id], inputs.criteria, "", DEFINITION_ONLY,
                    definition=None if defs is None else defs[p.id],
                )  # fmt: skip
                for pat in NAME_PATTERNS:
                    assert not re.search(pat, out, re.IGNORECASE if pat.islower() else 0), (
                        p.id,
                        pat,
                    )


def test_description_paraphrases_cover_every_policy_and_differ(inputs):
    levels = load_description_paraphrases(PARAPHRASES, POLICY_IDS)
    assert tuple(levels) == PARAPHRASE_LEVELS
    for p in inputs.policies:
        texts = [p.description] + [levels[lv][p.id] for lv in PARAPHRASE_LEVELS]
        assert len(set(texts)) == len(texts), p.id


def test_load_description_paraphrases_rejects_wrong_policy_set(tmp_path):
    (tmp_path / "para_1.yaml").write_text(yaml.safe_dump({"eitc": "x"}))
    with pytest.raises(ValueError, match="policy ids"):
        load_description_paraphrases(tmp_path, ("eitc", "ui"))


def test_load_templates_rejects_unknown_unit_and_bad_placeholders(tmp_path):
    (tmp_path / "persona_policy").mkdir()
    (tmp_path / "persona_policy" / "baseline.txt").write_text("{persona_block}")
    with pytest.raises(ValueError, match="placeholders"):
        load_templates(tmp_path)
    (tmp_path / "persona_policy" / "baseline.txt").unlink()
    (tmp_path / "mystery").mkdir()
    (tmp_path / "mystery" / "baseline.txt").write_text("x")
    with pytest.raises(ValueError, match="unknown call unit"):
        load_templates(tmp_path)


def test_manifest_records_the_hash_of_every_template_and_paraphrase():
    manifest = yaml.safe_load((PROMPTS / "manifest.yaml").read_text())
    recorded = {e["path"] for e in manifest["files"]}
    on_disk = {
        str(f.relative_to(REPO)) for f in [*PROMPTS.glob("*/*.txt"), *PARAPHRASES.glob("*.yaml")]
    }
    assert recorded == on_disk
    assert manifest_mismatches(PROMPTS / "manifest.yaml", REPO) == []
    for e in manifest["files"]:
        if "para_" in e["path"]:
            assert e["equivalence_check"], e["path"]


def test_manifest_mismatches_reports_an_edited_file(tmp_path):
    (tmp_path / "a.txt").write_text("one")
    m = tmp_path / "manifest.yaml"
    m.write_text(
        yaml.safe_dump({"files": [{"path": "a.txt", "sha256": file_sha256(tmp_path / "a.txt")}]})
    )
    assert manifest_mismatches(m, tmp_path) == []
    (tmp_path / "a.txt").write_text("two")
    assert manifest_mismatches(m, tmp_path) == ["a.txt"]
