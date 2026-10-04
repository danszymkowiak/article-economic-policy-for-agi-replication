"""One-at-a-time cells -> rendered study jobs, and their call counts (prereg s4, s5). Pure.

- persona x policy (B and every cell but D1): one call per persona x policy x repeat, all
  criteria in one reply, with that policy's own evidence packet. Q1 shows the neutral code and
  the de-named packet; Q2 swaps in a description paraphrase, Q3 an instruction paraphrase; the
  "none" evidence level (Q4) leaves the evidence block out; D2 has no persona.
- joint (D1): one call per persona x criterion x repeat, all policies under their codes. Its
  evidence is all packets concatenated in Table 3 (input) order, so every policy keeps its own
  packet and the evidence is the same text B shows, only in one prompt.

The rendered prompt holds the evidence, so job_id (a hash of the prompt) covers it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from llm_panel.domain.denaming import denamed_packet
from llm_panel.domain.jobs import JobCount
from llm_panel.domain.models import Criterion, Persona, Policy, RenderedJob
from llm_panel.domain.oat_design import (
    BASELINE_WORDING,
    DEFINITION_ONLY,
    JOINT,
    NO_EVIDENCE,
    NO_PERSONA,
    PERSONA_POLICY,
    Cell,
    Factors,
)
from llm_panel.domain.study_prompt import (
    neutral_codes,
    render_joint,
    render_persona_policy,
    select_template,
)

JOINT_EVIDENCE_SEPARATOR = "\n\n"


@dataclass(frozen=True)
class StudyMaterials:
    panels: Mapping[str, Sequence[Persona]]  # keyed by persona source
    policies: Sequence[Policy]  # Table 3 order; fixes the codes P1..P11
    criteria: Sequence[Criterion]
    packets: Mapping[str, Mapping[str, str]]  # evidence level -> policy id -> packet text
    templates: Mapping[str, Mapping[str, str]]  # call unit -> wording -> template text
    description_paraphrases: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    def personas(self, source: str) -> Sequence[Persona | None]:
        if source == NO_PERSONA:
            return (None,)
        if source not in self.panels:
            raise ValueError(f"no personas loaded for source {source!r}")
        return self.panels[source]

    def packet(self, level: str, policy_id: str) -> str:
        if level == NO_EVIDENCE:
            return ""
        text = self.packets.get(level, {}).get(policy_id)
        if text is None:
            raise ValueError(f"no evidence packet {level!r} for policy {policy_id!r}")
        return text


def factors_id(factors: Factors) -> str:
    blob = json.dumps(asdict(factors), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def count_cell_calls(cell: Cell, m: StudyMaterials) -> JobCount:
    n_personas = len(m.personas(cell.factors.persona_source))
    n_pol, n_crit = len(m.policies), len(m.criteria)
    per_repeat = n_personas * (n_crit if cell.factors.call_unit == JOINT else n_pol)
    calls = per_repeat * cell.repeats
    return JobCount(
        calls=calls, ratings=calls * (n_pol if cell.factors.call_unit == JOINT else n_crit)
    )


def _evidence(f: Factors, policy: Policy, m: StudyMaterials, codes: Mapping[str, str]) -> str:
    text = m.packet(f.evidence, policy.id)
    if text and f.policy_identifier == DEFINITION_ONLY:
        text = denamed_packet(text, policy.id, m.policies, codes)
    return text


def _definition(f: Factors, policy: Policy, m: StudyMaterials) -> str | None:
    if f.description_wording == BASELINE_WORDING:
        return None
    level = m.description_paraphrases.get(f.description_wording)
    if level is None or policy.id not in level:
        raise ValueError(f"no description paraphrase {f.description_wording!r} for {policy.id!r}")
    return level[policy.id]


def jobs_for_cell_repeat(cell: Cell, repeat: int, m: StudyMaterials) -> list[RenderedJob]:
    f = cell.factors
    seed = cell.seeds[repeat]
    codes = neutral_codes(m.policies)
    template = select_template(m.templates.get(f.call_unit, {}), f.instruction_wording)
    common = dict(
        provider=f.model.provider, model_snapshot=f.model.snapshot, temperature=f.temperature,
        seed=seed, spec_id=factors_id(f), repeat=repeat, cell_id=cell.cell_id,
    )  # fmt: skip
    jobs: list[RenderedJob] = []
    if f.call_unit == PERSONA_POLICY:
        criterion_ids = tuple(c.id for c in m.criteria)
        evidence = {p.id: _evidence(f, p, m, codes) for p in m.policies}
        for persona in m.personas(f.persona_source):
            for policy in m.policies:
                prompt = render_persona_policy(
                    template, persona, policy, codes[policy.id], m.criteria,
                    evidence[policy.id], f.policy_identifier, _definition(f, policy, m),
                )  # fmt: skip
                label = codes[policy.id] if f.policy_identifier == DEFINITION_ONLY else policy.id
                jobs.append(
                    RenderedJob(
                        prompt=prompt,
                        persona_id=persona.id if persona else NO_PERSONA,
                        criterion_id="",
                        criterion_ids=criterion_ids,
                        policy_ids=(policy.id,),
                        policy_labels=(label,),
                        **common,
                    )  # fmt: skip
                )
        return jobs
    if f.call_unit != JOINT:
        raise ValueError(f"unknown call unit {f.call_unit!r}")
    if f.description_wording != BASELINE_WORDING:
        raise ValueError("joint scoring has no description paraphrases")
    evidence = JOINT_EVIDENCE_SEPARATOR.join(
        t for t in (_evidence(f, p, m, codes) for p in m.policies) if t
    )
    for persona in m.personas(f.persona_source):
        for criterion in m.criteria:
            prompt = render_joint(
                template, persona, criterion, m.policies, codes, evidence, f.policy_identifier
            )
            jobs.append(
                RenderedJob(
                    prompt=prompt,
                    persona_id=persona.id if persona else NO_PERSONA,
                    criterion_id=criterion.id,
                    policy_ids=tuple(p.id for p in m.policies),
                    policy_labels=tuple(codes[p.id] for p in m.policies),
                    **common,
                )  # fmt: skip
            )
    return jobs


def jobs_for_cell(cell: Cell, m: StudyMaterials) -> list[RenderedJob]:
    return [j for r in range(cell.repeats) for j in jobs_for_cell_repeat(cell, r, m)]
