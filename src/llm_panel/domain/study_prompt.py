"""Study prompt rendering (prereg section 4; TASK-16). Pure.

Two call units: B's one persona x one policy with every criterion in one JSON object, and D1's
joint scoring (all policies in one prompt per persona x criterion). The template text lives in
`prompts/<call unit>/<wording>.txt`; this module fixes the placeholder contract each unit's
templates must meet and fills them. Policies are shown by name and definition, or (Q1) by a
neutral code P1..P11 and the definition alone. The persona preamble is EDSL's default wording
(reconstruction.md R2) and is held fixed across instruction paraphrases.

Not yet wired into the job builder (`jobs.py` still uses the placeholder `rendering.py`); that
waits for the user's review of the wording.
"""

from __future__ import annotations

import string
from collections.abc import Mapping, Sequence

from llm_panel.domain.models import Criterion, Persona, Policy
from llm_panel.domain.oat_design import (
    DEFINITION_ONLY,
    JOINT,
    NAME_AND_DEFINITION,
    PERSONA_POLICY,
)

PERSONA_PREAMBLE = "You are answering questions as if you were a human. Do not break character."
PLACEHOLDERS: dict[str, frozenset[str]] = {
    PERSONA_POLICY: frozenset(
        {"persona_block", "evidence_block", "policy_block", "criteria_block"}
    ),
    JOINT: frozenset(
        {"persona_block", "evidence_block", "criterion_name", "criterion_description",
         "policy_block"}
    ),
}  # fmt: skip
IDENTIFIERS = (NAME_AND_DEFINITION, DEFINITION_ONLY)


def template_fields(text: str) -> frozenset[str]:
    return frozenset(f for _, f, _, _ in string.Formatter().parse(text) if f is not None)


def check_template(call_unit: str, text: str) -> None:
    """A template must use exactly its call unit's placeholders, no more and no fewer."""
    if call_unit not in PLACEHOLDERS:
        raise ValueError(f"unknown call unit {call_unit!r}; known: {sorted(PLACEHOLDERS)}")
    found, want = template_fields(text), PLACEHOLDERS[call_unit]
    if found != want:
        raise ValueError(
            f"{call_unit} template placeholders differ: missing {sorted(want - found)}, "
            f"unexpected {sorted(found - want)}"
        )


def select_template(templates: Mapping[str, str], wording: str) -> str:
    if wording not in templates:
        raise ValueError(f"unknown wording {wording!r}; known: {sorted(templates)}")
    return templates[wording]


def neutral_codes(policies: Sequence[Policy]) -> dict[str, str]:
    """P1..Pn in the given (Table 3) order; fixed for a policy across every cell."""
    return {p.id: f"P{i}" for i, p in enumerate(policies, start=1)}


def _persona_block(persona: Persona | None) -> str:
    if persona is None or not persona.description:
        return ""
    return f"{PERSONA_PREAMBLE}\n\n{persona.description}\n\n"


def _evidence_block(evidence_text: str) -> str:
    return f"Evidence:\n{evidence_text}\n\n" if evidence_text else ""


def _policy_text(policy: Policy, identifier: str, definition: str | None) -> str:
    text = policy.description if definition is None else definition
    if identifier == NAME_AND_DEFINITION:
        return f"{policy.name}: {text}"
    if identifier == DEFINITION_ONLY:
        return text
    raise ValueError(f"unknown policy identifier {identifier!r}; known: {IDENTIFIERS}")


def render_persona_policy(
    template: str,
    persona: Persona | None,
    policy: Policy,
    code: str,
    criteria: Sequence[Criterion],
    evidence_text: str,
    identifier: str,
    definition: str | None = None,
) -> str:
    """B and its Q variations. `definition` overrides the policy's own (Q2 paraphrases)."""
    check_template(PERSONA_POLICY, template)
    text = _policy_text(policy, identifier, definition)
    policy_block = f"{code}: {text}" if identifier == DEFINITION_ONLY else text
    criteria_block = "\n".join(f"- {c.id} ({c.name}): {c.description}" for c in criteria)
    return template.format(
        persona_block=_persona_block(persona),
        evidence_block=_evidence_block(evidence_text),
        policy_block=policy_block,
        criteria_block=criteria_block,
    )


def render_joint(
    template: str,
    persona: Persona | None,
    criterion: Criterion,
    policies: Sequence[Policy],
    codes: Mapping[str, str],
    evidence_text: str,
    identifier: str,
) -> str:
    """D1: every policy in one prompt, each under its neutral code (the response label)."""
    check_template(JOINT, template)
    lines = [f"[{codes[p.id]}] {_policy_text(p, identifier, None)}" for p in policies]
    return template.format(
        persona_block=_persona_block(persona),
        evidence_block=_evidence_block(evidence_text),
        criterion_name=criterion.name,
        criterion_description=criterion.description,
        policy_block="\n".join(lines),
    )
