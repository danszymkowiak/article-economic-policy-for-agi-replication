"""Persona builders. Pure: no I/O.

A persona is a dictionary of traits rendered the way EDSL renders agent traits. The synthetic
panel is OUR stand-in for the authors' unpublished survey of 51 economists; the IGM builder maps
anonymous expert-panel records to traits. Every panel carries a provenance record.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from llm_panel.domain.models import Persona

# Levels per trait dimension (a stand-in design choice, recorded in prereg/reconstruction.md).
# Each dimension is assigned independently and balanced, so attitudes are not correlated with
# one another: this spreads the panel but does not mimic how real economists' views cluster.
TRAIT_SPACE: dict[str, tuple[str, ...]] = {
    "field": (
        "labor economics", "macroeconomics", "public economics", "development economics",
        "behavioral economics", "industrial organization", "economic history", "econometrics",
    ),
    "political_leaning": (
        "very liberal", "liberal", "centrist", "conservative", "very conservative",
    ),
    "redistribution_view": (
        "strongly favors redistribution", "favors redistribution", "mixed views",
        "skeptical of redistribution", "opposes redistribution",
    ),
    "ai_labor_view": (
        "AI will mostly complement human labor", "AI will cause modest, manageable disruption",
        "AI will cause large-scale job displacement",
        "AI will make human labor largely obsolete",
    ),
    "government_role_view": (
        "market-oriented", "mixed, case by case", "favors an active state",
    ),
    "seniority": ("PhD student", "early-career", "mid-career", "senior"),
    "country": (
        "United States", "United Kingdom", "Germany", "France", "Canada", "India", "Brazil",
        "Japan",
    ),
}  # fmt: skip

IDENTIFYING_KEYS = ("name", "email", "full_name", "first_name", "last_name")


@dataclass(frozen=True)
class PersonaPanel:
    personas: tuple[Persona, ...]
    traits: tuple[dict, ...]  # parallel to personas
    provenance: dict


def render_traits(traits: Mapping[str, str]) -> str:
    """EDSL's persona text: `Your traits: {...}` (dict repr, insertion order)."""
    return f"Your traits: {dict(traits)}"


def _panel(source: str, prefix: str, traits: Sequence[dict], provenance: dict) -> PersonaPanel:
    width = max(2, len(str(len(traits))))
    personas = tuple(
        Persona(id=f"{prefix}_{i:0{width}d}", source=source, description=render_traits(t))
        for i, t in enumerate(traits, start=1)
    )
    return PersonaPanel(personas, tuple(traits), provenance)


def build_synthetic_panel(n: int, seed: int, source: str = "reconstructed") -> PersonaPanel:
    columns: dict[str, list[str]] = {}
    for dim, levels in TRAIT_SPACE.items():
        values = [levels[i % len(levels)] for i in range(n)]  # balanced to within one
        random.Random(f"{seed}|{dim}").shuffle(values)
        columns[dim] = values
    traits = [{dim: columns[dim][i] for dim in TRAIT_SPACE} for i in range(n)]
    provenance = {
        "source": source,
        "kind": "synthetic",
        "stand_in": True,
        "n": n,
        "seed": seed,
        "method": "balanced independent assignment of trait levels, shuffled per dimension",
        "trait_space": {dim: list(levels) for dim, levels in TRAIT_SPACE.items()},
        "notes": "Our own stand-in for the authors' unpublished survey of 51 economists; "
        "not the authors' personas.",
    }
    return _panel(source, "econ", traits, provenance)


def build_igm_panel(
    records: Sequence[Mapping[str, str]],
    *,
    source: str,
    origin: str,
    retrieved: str,
    input_sha256: str,
) -> PersonaPanel:
    """Personas from anonymous expert-panel records (one per respondent, no identifying fields)."""
    if not records:
        raise ValueError("no records to build personas from")
    traits = []
    for record in records:
        bad = [k for k in record if k.lower() in IDENTIFYING_KEYS]
        if bad:
            raise ValueError(f"records must be anonymous; identifying field(s): {bad}")
        traits.append({k: v for k, v in record.items() if k != "respondent"})
    provenance = {
        "source": source,
        "kind": "igm",
        "stand_in": False,
        "n": len(traits),
        "origin": origin,
        "retrieved": retrieved,
        "input_sha256": input_sha256,
        "method": "one persona per anonymous respondent record; traits are the record's fields",
        "notes": "Public expert-panel data, not the authors' personas.",
    }
    return _panel(source, source, traits, provenance)


NAMED_TRAITS = ("name", "institution", "primary_field")
NAMED_PANEL_SIZE = 51


def build_named_panel(
    records: Sequence[Mapping[str, str]],
    *,
    source: str,
    retrieved: str,
    input_sha256: str,
) -> PersonaPanel:
    """The paper's 51 named economists (Appendix A, Table 7), in table order.

    Persona content is limited to the three traits the paper publishes; nothing about any
    economist's views or results is added.
    """
    if len(records) != NAMED_PANEL_SIZE:
        raise ValueError(f"roster must have exactly {NAMED_PANEL_SIZE} names, got {len(records)}")
    for record in records:
        if set(record) != set(NAMED_TRAITS):
            missing = sorted(set(NAMED_TRAITS) - set(record))
            extra = sorted(set(record) - set(NAMED_TRAITS))
            raise ValueError(
                f"roster columns must be {list(NAMED_TRAITS)}; missing {missing}, extra {extra}"
            )
    names = [r["name"] for r in records]
    if len(set(names)) != len(names):
        raise ValueError("roster names must be unique")
    traits = [{k: record[k] for k in NAMED_TRAITS} for record in records]
    provenance = {
        "source": source,
        "kind": "named",
        "stand_in": False,
        "n": len(traits),
        "origin": "Jacobs and Imas, Economic Policy for AGI (SSRN 7470000), Appendix A, Table 7",
        "table": "Table 7. Simulated Economist Panel Roster (N = 51)",
        "retrieved": retrieved,
        "input_sha256": input_sha256,
        "method": "one persona per Table 7 row, in table order; traits are name, institution "
        "and primary field exactly as printed",
        "notes": "John Cochrane is named in the paper text but absent from Table 7; he is "
        "excluded, so the roster follows the table. Table 7 status marks (alumni, hiatus) "
        "were dropped: they are not traits. Persona text carries only the three published "
        "traits, no reported results or opinions.",
    }
    return _panel(source, source, traits, provenance)
