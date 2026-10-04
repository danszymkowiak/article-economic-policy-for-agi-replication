"""ADVERSARIAL ARM: the fixed, versioned catalogue of small plausible perturbations. Pure.

Fixed before any adversarial data (prereg s9). A change to any entry is a new catalogue version;
the config names the version it searches with and the loader refuses any other.

Kinds (the slot says which perturbations exclude each other in a depth-2 combination):
- wording: one meaning-preserving edit of one sentence of the persona x policy template (each
  sentence its own slot, so two different sentences can be combined);
- evidence: one edit of the TARGET policy's evidence packet (drop its last or first excerpt,
  reverse the excerpt order, keep the first half); one slot;
- persona_subset: drop, at evaluation, the search-panel persona who rated the target highest on
  the primary composite (no new calls);
- temperature: 0 or 1 instead of the provider default; one slot;
- criterion_order: the criteria listed in reverse, or the primary composite's criteria first.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

CATALOGUE_VERSION = "adv-catalogue-v1"

WORDING = "wording"
EVIDENCE = "evidence"
PERSONA_SUBSET = "persona_subset"
TEMPERATURE = "temperature"
CRITERION_ORDER = "criterion_order"
KINDS = (WORDING, EVIDENCE, PERSONA_SUBSET, TEMPERATURE, CRITERION_ORDER)

EVIDENCE_OPS = ("drop_last", "drop_first", "reverse", "keep_first_half")
CRITERION_OPS = ("reverse", "primary_first")
DROP_TOP_PERSONA = "drop_top_persona"


@dataclass(frozen=True)
class Perturbation:
    id: str
    kind: str
    slot: str  # two perturbations in one slot are never combined
    description: str
    old: str = ""  # wording: exact fragment of the baseline template
    new: str = ""  # wording: its replacement
    op: str = ""  # evidence, persona_subset and criterion_order operation
    temperature: float | None = None  # temperature level


def _wording(pid: str, old: str, new: str) -> Perturbation:
    return Perturbation(pid, WORDING, f"{WORDING}:{pid}", f'"{old}" -> "{new}"', old=old, new=new)


def _evidence(op: str, text: str) -> Perturbation:
    return Perturbation(f"e_{op}", EVIDENCE, EVIDENCE, f"target packet: {text}", op=op)


CATALOGUE: tuple[Perturbation, ...] = (
    _wording("w_household", "a household-facing economic policy",
             "a household-level economic policy"),
    _wording("w_could_help", "that could help the United States",
             "that might help the United States"),
    _wording("w_agi", "artificial general intelligence (AGI).",
             "artificial general intelligence."),
    _wording("w_higher_better", "does better on that criterion",
             "performs better on that criterion"),
    _wording("w_rationale", "Give a one-sentence rationale", "Give a brief rationale"),
    _evidence("drop_last", "drop the last excerpt"),
    _evidence("drop_first", "drop the first excerpt"),
    _evidence("reverse", "excerpts in reverse order"),
    _evidence("keep_first_half", "keep the first half of the excerpts (rounded up)"),
    Perturbation("p_drop_top", PERSONA_SUBSET, PERSONA_SUBSET,
                 "drop the search-panel persona most favourable to the target",
                 op=DROP_TOP_PERSONA),
    Perturbation("t_0", TEMPERATURE, TEMPERATURE, "temperature 0", temperature=0.0),
    Perturbation("t_1", TEMPERATURE, TEMPERATURE, "temperature 1", temperature=1.0),
    Perturbation("c_reverse", CRITERION_ORDER, CRITERION_ORDER, "criteria in reverse order",
                 op="reverse"),
    Perturbation("c_primary_first", CRITERION_ORDER, CRITERION_ORDER,
                 "primary composite's criteria listed first", op="primary_first"),
)  # fmt: skip


def check_catalogue(catalogue: Sequence[Perturbation], template: str) -> None:
    """Ids unique, kinds and operations known, each wording fragment exactly once in the
    template (so an edit is one well-defined replacement)."""
    seen: set[str] = set()
    for p in catalogue:
        if p.id in seen:
            raise ValueError(f"duplicate perturbation id {p.id!r}")
        seen.add(p.id)
        if p.kind not in KINDS:
            raise ValueError(f"{p.id}: unknown kind {p.kind!r}")
        if p.kind == WORDING:
            if template.count(p.old) != 1:
                raise ValueError(f"{p.id}: fragment {p.old!r} must occur exactly once in template")
            if not p.new or p.new == p.old or "{" in p.new or "}" in p.new:
                raise ValueError(f"{p.id}: replacement must differ and hold no placeholder")
        elif p.kind == EVIDENCE and p.op not in EVIDENCE_OPS:
            raise ValueError(f"{p.id}: unknown evidence operation {p.op!r}")
        elif p.kind == CRITERION_ORDER and p.op not in CRITERION_OPS:
            raise ValueError(f"{p.id}: unknown criterion order {p.op!r}")
        elif p.kind == PERSONA_SUBSET and p.op != DROP_TOP_PERSONA:
            raise ValueError(f"{p.id}: unknown persona subset {p.op!r}")
        elif p.kind == TEMPERATURE and p.temperature is None:
            raise ValueError(f"{p.id}: temperature level missing")
