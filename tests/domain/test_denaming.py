"""Rule-based de-naming of evidence packets for the description-only cell Q1 (TASK-33)."""

import pytest

from llm_panel.domain.denaming import denamed_packet, name_rules
from llm_panel.domain.models import Policy
from llm_panel.domain.study_prompt import neutral_codes
from tests.name_patterns import names_found


def pol(pid, name):
    return Policy(id=pid, name=name, description="d", blinded_description="d")


POLICIES = (
    pol("eitc", "Earned Income Tax Credit (EITC)"),
    pol("ui", "Unemployment Insurance (UI)"),
    pol("almp", "Active Labour-Market Policies (ALMP)"),
    pol("ubi", "Universal Basic Income (UBI)"),
    pol("nit", "Negative Income Tax (NIT)"),
    pol("sawf", "Sovereign AI Fund / Dividend (SAWF)"),
)
CODES = neutral_codes(POLICIES)  # eitc P1, ui P2, almp P3, ubi P4, nit P5, sawf P6

PACKET = """# Evidence packet: Universal Basic Income (UBI)

Source: English Wikipedia (text licensed CC BY-SA 4.0; excerpts are shared alike).
- Universal basic income, revision 1: https://en.wikipedia.org/w/index.php?oldid=1 (fetched x)
- Alaska Permanent Fund, revision 2: https://en.wikipedia.org/w/index.php?oldid=2 (fetched y)
The union of two independent extraction passes is shown; character overlap between the passes: Universal basic income 96%, Alaska Permanent Fund 74%.

## Work (Universal basic income)
In negative income tax experiments, hours fell. A UBI of $1,000/month cut non-UBI income.

## Dividends (Alaska Permanent Fund)
The Alaska Permanent Fund pays a dividend, unlike the earned income tax credit or UI benefits.
"""  # noqa: E501


def test_header_names_only_the_neutral_code():
    out = denamed_packet(PACKET, "ubi", POLICIES, CODES)
    assert out.splitlines()[0] == "# Evidence packet: P4"


def test_policy_names_and_acronyms_become_each_policys_own_code():
    out = denamed_packet(PACKET, "ubi", POLICIES, CODES)
    assert "In P5 experiments" in out  # another policy's name -> that policy's code
    assert "A P4 of $1,000/month cut non-P4 income" in out
    assert "the P1 or P2 benefits" in out
    assert names_found(out) == []


def test_source_article_titles_become_numbered_sources_in_the_metadata_only():
    out = denamed_packet(PACKET, "ubi", POLICIES, CODES)
    assert "- P4 source 1, revision 1:" in out
    assert "- P4 source 2, revision 2:" in out
    assert "passes: P4 source 1 96%, P4 source 2 74%." in out
    assert "## Work (P4 source 1)" in out and "## Dividends (P4 source 2)" in out
    # body text keeps real-world programme names that are not policy names
    assert "The Alaska Permanent Fund pays a dividend" in out


def test_attribution_links_survive():
    out = denamed_packet(PACKET, "ubi", POLICIES, CODES)
    assert "oldid=1" in out and "oldid=2" in out and "CC BY-SA 4.0" in out


def test_acronyms_match_whole_words_and_case():
    rules = name_rules(POLICIES, CODES)
    text = "BUILD, GUI and ui stay; UI goes; ALMPs go."
    assert rules(text) == "BUILD, GUI and ui stay; P2 goes; P3 go."


@pytest.mark.parametrize(
    "phrase,code",
    [
        ("Active labour market policies", "P3"),
        ("active labor-market programmes", "P3"),
        ("sovereign wealth funds", "P6"),
        ("Sovereign AI Fund", "P6"),
        ("universal basic income", "P4"),
        ("Negative Income Taxes", "P5"),
        ("Earned Income Tax Credits", "P1"),
        ("EIC", "P1"),
        ("SWFs", "P6"),
    ],
)
def test_name_variants(phrase, code):
    assert name_rules(POLICIES, CODES)(phrase) == code


def test_unknown_policy_id_is_rejected():
    with pytest.raises(ValueError, match="unknown policy"):
        denamed_packet(PACKET, "zzz", POLICIES, CODES)


def test_titles_are_relabelled_only_in_a_headings_trailing_parenthetical():
    text = (
        "# Evidence packet: Unemployment Insurance (UI)\n"
        "- Unemployment benefits, revision 7: https://x?oldid=7 (fetched z)\n"
        "## Unemployment benefits effect on unemployment (Unemployment benefits)\n"
        "- Unemployment benefits are paid weekly.\n"
    )
    out = denamed_packet(text, "ui", POLICIES, CODES)
    assert "## Unemployment benefits effect on unemployment (P2 source 1)" in out
    assert "- P2 source 1, revision 7:" in out
    assert "- Unemployment benefits are paid weekly." in out  # body bullet untouched
