"""Prompt rendering. Pure.

The templates here are a PLACEHOLDER baseline so the pipeline runs end to end. The study's
reconstructed templates and paraphrases are built in the prompt-templates task.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from llm_panel.domain.models import Criterion, Persona, Policy, RunSpec

LABEL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

TEMPLATES: dict[str, str] = {
    "baseline": (
        "{persona_block}{evidence_block}"
        'Rate each policy below on this criterion: "{criterion_name}" - {criterion_description}\n'
        "Give each policy a score from 0 to 100 and a one-sentence rationale.\n\n"
        "Policies:\n{policy_block}\n\n"
        'Respond with JSON only, in the form {{"ratings": [{{"policy": <label>, "score": '
        '<0-100>, "rationale": <text>}}, ...]}} with exactly one entry per policy, '
        "using the labels exactly as shown."
    ),
}


def order_policies(
    policies: Sequence[Policy], order: str, seed: int, persona_id: str, criterion_id: str
) -> list[Policy]:
    items = list(policies)
    if order == "fixed":
        return items
    if order == "reversed":
        return items[::-1]
    if order == "shuffled":
        random.Random(f"{seed}|{persona_id}|{criterion_id}").shuffle(items)
        return items
    raise ValueError(f"unknown order {order!r}")


def make_labels(policies: Sequence[Policy], blinded: bool) -> tuple[str, ...]:
    if blinded:
        if len(policies) > len(LABEL_ALPHABET):
            raise ValueError("too many policies for letter labels")
        return tuple(LABEL_ALPHABET[: len(policies)])
    return tuple(p.id for p in policies)


def render_prompt(
    spec: RunSpec,
    persona: Persona,
    criterion: Criterion,
    policies: Sequence[Policy],
    labels: Sequence[str],
    evidence_text: str,
) -> str:
    template = TEMPLATES.get(spec.paraphrase)
    if template is None:
        raise ValueError(f"unknown paraphrase {spec.paraphrase!r}; known: {sorted(TEMPLATES)}")
    persona_block = (
        f"You are this economist: {persona.description}\n\n" if persona.description else ""
    )
    evidence_block = f"Evidence:\n{evidence_text}\n\n" if evidence_text else ""
    lines = []
    for policy, label in zip(policies, labels, strict=True):
        text = (
            policy.blinded_description if spec.blinded else f"{policy.name}: {policy.description}"
        )
        lines.append(f"[{label}] {text}")
    return template.format(
        persona_block=persona_block,
        evidence_block=evidence_block,
        criterion_name=criterion.name,
        criterion_description=criterion.description,
        policy_block="\n".join(lines),
    )
