"""Expand run specs into the jobs still to be run."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from llm_panel.domain.jobs import JobCount, count_jobs, jobs_for_spec
from llm_panel.domain.models import Criterion, Persona, Policy, RenderedJob, RunSpec
from llm_panel.domain.oat_design import Cell, RunOrder
from llm_panel.domain.study_jobs import StudyMaterials, count_cell_calls, jobs_for_cell_repeat
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
class CellSummary:
    """One one-at-a-time cell, all repeats, before dedupe and skipping finished jobs."""

    count: JobCount
    repeats: int
    estimated_cost: float = 0.0


@dataclass(frozen=True)
class BuildResult:
    jobs: list[RenderedJob]  # new jobs to run (deduplicated, not yet in the store)
    total: int  # distinct jobs the specs call for
    skipped: int  # distinct jobs already finished in the store
    duplicates: int  # jobs repeated across specs (identical prompt/model/params)
    per_spec: list[JobCount]  # calls and ratings per configuration, before dedupe/skipping
    per_cell: dict[str, CellSummary] = field(default_factory=dict)  # one-at-a-time designs only


class _Dedupe:
    def __init__(self, store: ResultStore) -> None:
        self.store, self.seen, self.new = store, set(), []
        self.skipped = self.duplicates = 0

    def add(self, job: RenderedJob) -> None:
        jid = job.job_id
        if jid in self.seen:
            self.duplicates += 1
            return
        self.seen.add(jid)
        if self.store.exists(jid):
            self.skipped += 1
            return
        self.new.append(job)


def build_jobs(specs: Sequence[RunSpec], inputs: StudyInputs, store: ResultStore) -> BuildResult:
    d = _Dedupe(store)
    per_spec: list[JobCount] = []
    for spec in specs:
        personas = inputs.personas_for(spec.persona_source)
        per_spec.append(count_jobs(spec, len(personas), len(inputs.criteria), len(inputs.policies)))
        for job in jobs_for_spec(
            spec, personas, inputs.policies, inputs.criteria, inputs.evidence_for(spec.evidence)
        ):
            d.add(job)
    return BuildResult(
        jobs=d.new, total=len(d.seen), skipped=d.skipped, duplicates=d.duplicates,
        per_spec=per_spec,
    )  # fmt: skip


def build_study_jobs(
    cells: Sequence[Cell],
    order: RunOrder,
    materials: StudyMaterials,
    store: ResultStore,
    cost: Callable[[RenderedJob], float] | None = None,
) -> BuildResult:
    """Jobs of one-at-a-time cells, in the design's recorded run order (repeats interleaved,
    B' last). `cost` estimates each job so the plan can show cost per cell."""
    by_id = {c.cell_id: c for c in cells}
    spent = dict.fromkeys(by_id, 0.0)
    d = _Dedupe(store)
    for slot in order.slots:
        cell = by_id[slot.cell_id]
        for job in jobs_for_cell_repeat(cell, slot.repeat, materials):
            if cost is not None:
                spent[cell.cell_id] += cost(job)
            d.add(job)
    per_cell = {
        c.cell_id: CellSummary(count_cell_calls(c, materials), c.repeats, spent[c.cell_id])
        for c in cells
    }
    return BuildResult(
        jobs=d.new, total=len(d.seen), skipped=d.skipped, duplicates=d.duplicates,
        per_spec=[s.count for s in per_cell.values()], per_cell=per_cell,
    )  # fmt: skip
