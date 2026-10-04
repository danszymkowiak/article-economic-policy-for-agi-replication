from collections import Counter

import pytest

from llm_panel.domain.personas import (
    TRAIT_SPACE,
    build_igm_panel,
    build_named_panel,
    build_synthetic_panel,
    render_traits,
)


def test_render_traits_matches_edsl_persona_wording():
    assert render_traits({"party": "Democrat", "field": "labor"}) == (
        "Your traits: {'party': 'Democrat', 'field': 'labor'}"
    )


def test_synthetic_panel_has_n_personas_with_stable_ids_and_all_trait_dimensions():
    panel = build_synthetic_panel(51, seed=7)
    assert [p.id for p in panel.personas][:2] == ["econ_01", "econ_02"]
    assert len(panel.personas) == 51 and all(p.source == "reconstructed" for p in panel.personas)
    assert set(panel.traits[0]) == set(TRAIT_SPACE)
    assert "country" in TRAIT_SPACE


def test_synthetic_panel_is_deterministic_per_seed_and_differs_across_seeds():
    assert build_synthetic_panel(51, seed=7) == build_synthetic_panel(51, seed=7)
    assert build_synthetic_panel(51, seed=7).traits != build_synthetic_panel(51, seed=8).traits


def test_every_dimension_is_balanced_to_within_one_persona():
    panel = build_synthetic_panel(51, seed=7)
    for dim, levels in TRAIT_SPACE.items():
        counts = Counter(t[dim] for t in panel.traits)
        assert set(counts) == set(levels)
        assert max(counts.values()) - min(counts.values()) <= 1, dim


def test_no_two_synthetic_personas_are_identical():
    panel = build_synthetic_panel(51, seed=7)
    assert len({tuple(t.items()) for t in panel.traits}) == 51


def test_persona_description_is_the_rendered_traits():
    panel = build_synthetic_panel(5, seed=1)
    assert panel.personas[0].description == render_traits(panel.traits[0])


def test_synthetic_provenance_says_stand_in_and_records_seed_and_method():
    prov = build_synthetic_panel(51, seed=7).provenance
    assert prov["source"] == "reconstructed" and prov["stand_in"] is True
    assert prov["seed"] == 7 and prov["n"] == 51 and prov["kind"] == "synthetic"
    assert "not the authors" in prov["notes"].lower()


RECORDS = [
    {"respondent": "r1", "country": "United States", "q_ubi": "Disagree", "q_eitc": "Agree"},
    {"respondent": "r2", "country": "United States", "q_ubi": "Agree", "q_eitc": "Agree"},
]


def test_igm_panel_builds_personas_from_anonymous_records_with_provenance():
    panel = build_igm_panel(
        RECORDS, source="igm_us", origin="IGM Forum, US panel", retrieved="2026-10-04",
        input_sha256="abc",
    )  # fmt: skip
    assert [p.id for p in panel.personas] == ["igm_us_01", "igm_us_02"]
    assert panel.traits[0] == {"country": "United States", "q_ubi": "Disagree", "q_eitc": "Agree"}
    assert panel.provenance["stand_in"] is False and panel.provenance["kind"] == "igm"
    assert panel.provenance["input_sha256"] == "abc" and panel.provenance["n"] == 2


@pytest.mark.parametrize("key", ["name", "Name", "email", "full_name"])
def test_igm_builder_refuses_identifying_fields(key):
    with pytest.raises(ValueError, match="identif"):
        build_igm_panel([{"respondent": "r1", key: "x"}], source="igm_us", origin="o",
                        retrieved="d", input_sha256="h")  # fmt: skip


def test_igm_builder_refuses_empty_input():
    with pytest.raises(ValueError, match="no records"):
        build_igm_panel([], source="igm_us", origin="o", retrieved="d", input_sha256="h")


def _roster(n=51):
    return [
        {"name": f"Person {i}", "institution": f"Inst {i}", "primary_field": f"Field {i} (X)"}
        for i in range(1, n + 1)
    ]


def _named(records):
    return build_named_panel(records, source="named", retrieved="2026-10-04", input_sha256="h")


def test_named_panel_has_three_traits_in_roster_order_and_provenance():
    panel = _named(_roster())
    assert [p.id for p in panel.personas][:2] == ["named_01", "named_02"]
    assert panel.personas[-1].id == "named_51"
    assert panel.traits[0] == {
        "name": "Person 1", "institution": "Inst 1", "primary_field": "Field 1 (X)",
    }  # fmt: skip
    prov = panel.provenance
    assert prov["kind"] == "named" and prov["stand_in"] is False and prov["n"] == 51
    assert prov["retrieved"] == "2026-10-04" and prov["input_sha256"] == "h"
    assert "Table 7" in prov["origin"] and "7470000" in prov["origin"]
    assert "Cochrane" in prov["notes"] and "excluded" in prov["notes"]


def test_named_persona_text_is_exactly_the_three_traits():
    panel = _named(_roster())
    for p, t in zip(panel.personas, panel.traits, strict=True):
        assert p.description == (
            f"Your traits: {{'name': '{t['name']}', 'institution': '{t['institution']}', "
            f"'primary_field': '{t['primary_field']}'}}"
        )  # nothing beyond the three traits: no opinions, no reported results


@pytest.mark.parametrize("n", [0, 50, 52])
def test_named_builder_requires_exactly_51(n):
    with pytest.raises(ValueError, match="51"):
        _named(_roster(n))


def test_named_builder_refuses_duplicate_names():
    records = _roster()
    records[1] = dict(records[1], name=records[0]["name"])
    with pytest.raises(ValueError, match="unique"):
        _named(records)


def test_named_builder_refuses_missing_or_extra_columns():
    records = _roster()
    records[3] = {"name": "x", "institution": "y"}
    with pytest.raises(ValueError, match="primary_field"):
        _named(records)
    records = [dict(r, stance="pro") for r in _roster()]
    with pytest.raises(ValueError, match="stance"):
        _named(records)
