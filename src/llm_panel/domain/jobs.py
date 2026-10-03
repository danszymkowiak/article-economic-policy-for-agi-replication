"""Expand one RunSpec into rendered jobs, and count them. Pure."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from llm_panel.domain.models import Criterion, Persona, Policy, RenderedJob, RunSpec
from llm_panel.domain.rendering import make_labels, order_policies, render_prompt


@dataclass(frozen=True)
class JobCount:
    calls: int  # model calls (jobs)
    ratings: int  # individual policy ratings those calls yield


def count_jobs(spec: RunSpec, n_personas: int, n_criteria: int, n_policies: int) -> JobCount:
    cells = n_personas * n_criteria * spec.repeats
    ratings = cells * n_policies
    calls = cells if spec.prompt_format == "all_policies" else ratings
    return JobCount(calls=calls, ratings=ratings)


def jobs_for_spec(
    spec: RunSpec,
    personas: Sequence[Persona],
    policies: Sequence[Policy],
    criteria: Sequence[Criterion],
    evidence_text: str,
) -> list[RenderedJob]:
    jobs: list[RenderedJob] = []
    for persona in personas:
        for criterion in criteria:
            for repeat in range(spec.repeats):
                seed = spec.base_seed + repeat
                if spec.prompt_format == "all_policies":
                    groups = [order_policies(policies, spec.order, seed, persona.id, criterion.id)]
                else:
                    groups = [[p] for p in policies]
                for group in groups:
                    labels = make_labels(group, spec.blinded)
                    prompt = render_prompt(spec, persona, criterion, group, labels, evidence_text)
                    jobs.append(
                        RenderedJob(
                            prompt=prompt,
                            provider=spec.provider,
                            model_snapshot=spec.model_snapshot,
                            temperature=spec.temperature,
                            seed=seed,
                            persona_id=persona.id,
                            criterion_id=criterion.id,
                            policy_ids=tuple(p.id for p in group),
                            policy_labels=labels,
                            spec_id=spec.spec_id,
                            repeat=repeat,
                        )
                    )
    return jobs
