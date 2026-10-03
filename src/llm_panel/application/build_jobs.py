"""Expand run specs into the jobs still to be run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from llm_panel.domain.jobs import JobCount, count_jobs, jobs_for_spec
from llm_panel.domain.models import Criterion, Persona, Policy, RenderedJob, RunSpec
from llm_panel.ports import ResultStore

NEUTRAL_PERSONA = Persona(id="none", source="none", description="")


@dataclass(frozen=True)
class StudyInputs:
    personas: Mapping[str, Sequence[Persona]]  # keyed by persona source
    policies: Sequence[Policy]
    criteria: Sequence[Criterion]
    evidence: Mapping[str, str]  # keyed by evidence packet name; "none" -> ""

    def personas_for(self, source: str) -> Sequence[Persona]:
        if source == "none":
            return (NEUTRAL_PERSONA,)
        if source not in self.personas:
            raise ValueError(f"no personas loaded for source {source!r}")
        return self.personas[source]

    def evidence_for(self, name: str) -> str:
        if name == "none":
            return ""
        if name not in self.evidence:
            raise ValueError(f"no evidence packet named {name!r}")
        return self.evidence[name]


@dataclass(frozen=True)
class BuildResult:
    jobs: list[RenderedJob]  # new jobs to run (deduplicated, not yet in the store)
    total: int  # distinct jobs the specs call for
    skipped: int  # distinct jobs already finished in the store
    duplicates: int  # jobs repeated across specs (identical prompt/model/params)
    per_spec: list[JobCount]  # calls and ratings per configuration, before dedupe/skipping


def build_jobs(specs: Sequence[RunSpec], inputs: StudyInputs, store: ResultStore) -> BuildResult:
    seen: set[str] = set()
    new: list[RenderedJob] = []
    skipped = duplicates = 0
    per_spec: list[JobCount] = []
    for spec in specs:
        personas = inputs.personas_for(spec.persona_source)
        per_spec.append(count_jobs(spec, len(personas), len(inputs.criteria), len(inputs.policies)))
        for job in jobs_for_spec(
            spec, personas, inputs.policies, inputs.criteria, inputs.evidence_for(spec.evidence)
        ):
            jid = job.job_id
            if jid in seen:
                duplicates += 1
                continue
            seen.add(jid)
            if store.exists(jid):
                skipped += 1
                continue
            new.append(job)
    return BuildResult(
        jobs=new, total=len(seen), skipped=skipped, duplicates=duplicates, per_spec=per_spec
    )
