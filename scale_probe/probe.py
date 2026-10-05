"""EXPLORATORY reversed-scale probe (TASK-38): application layer. Builds the probe's jobs, reads
ratings from its own store and (read-only) the adversarial arm's baseline and rerun, and plans
submission through the study's guards.

The probe's jobs are the adversarial arm's baseline candidate (B's persona x policy prompt on the
arm's search panel, every policy, the arm's candidate seed) with the template swapped for the
reversed-scale one, so the only difference from the arm's baseline run is the scale sentence.
Rows carry cell id `SCALE:reversed`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from adversarial.arm import BASELINE, ArmSettings, candidate_jobs, search_panel
from adversarial.search import panel_outcome
from llm_panel.application.build_jobs import BuildResult
from llm_panel.application.spend import jobs_in_flight
from llm_panel.application.submit import Plan, plan_from_build
from llm_panel.domain.analysis_baseline import COMPOSITES
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.oat_design import BASELINE_WORDING, PERSONA_POLICY, Cell
from llm_panel.domain.pricing import SpendSettings
from llm_panel.domain.results import STATUS_OK
from llm_panel.domain.study_jobs import StudyMaterials, jobs_for_cell_repeat
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import BatchLedger, ResultStore
from scale_probe.analysis import ProbeResult, Ratings, analyse

CELL_ID = "SCALE:reversed"


def probe_jobs(
    materials: StudyMaterials, settings: ArmSettings, template: str
) -> list[RenderedJob]:
    templates = {k: dict(v) for k, v in materials.templates.items()}
    templates[PERSONA_POLICY][BASELINE_WORDING] = template
    base = settings.baseline
    m = replace(
        materials,
        panels={**materials.panels, base.persona_source: search_panel(materials, settings)},
        templates=templates,
    )
    cell = Cell(CELL_ID, "SCALE", "SCALE", base, (settings.seed,))
    return jobs_for_cell_repeat(cell, 0, m)


@dataclass(frozen=True)
class RunRead:
    ratings: Ratings
    complete: bool  # every job has reached a terminal row
    failed: int  # terminal jobs without a usable reply


def read_run(store: ResultStore, jobs: Sequence[RenderedJob]) -> RunRead:
    wanted = {j.job_id for j in jobs}
    terminal: set[str] = set()
    ratings: dict[tuple[str, str, str], float] = {}
    ok: set[str] = set()
    for row in store.iter_rows():
        if row.job_id not in wanted:
            continue
        if row.is_terminal:
            terminal.add(row.job_id)
        if row.status != STATUS_OK or row.job_id in ok:
            continue
        job = RenderedJob.from_dict(row.request)
        try:
            parsed = parse_ratings(job, (row.response or {}).get("text") or "")
        except InvalidResponse:
            continue
        ok.add(row.job_id)
        for r in parsed:
            ratings[(r.persona_id, r.policy_id, r.criterion_id)] = r.score
    return RunRead(ratings, terminal >= wanted, len(terminal - ok))


@dataclass(frozen=True)
class ProbeState:
    jobs: list[RenderedJob]
    probe: RunRead
    baseline: RunRead
    rerun: RunRead
    panel_size: int
    result: ProbeResult | None  # None until all three runs are complete

    @property
    def status(self) -> str:
        if not (self.baseline.complete and self.rerun.complete):
            return "adversarial baseline pending"
        if not self.probe.complete:
            return "probe pending"
        return "complete"


def _target(ratings: Ratings, policies: Sequence[str], composite: str) -> str:
    """The adversarial arm's target: the top policy on its primary composite in its baseline run
    (adversarial.search.panel_outcome, ties to the first in policy order)."""
    rows = [(n, p, c, s) for (n, p, c), s in ratings.items()]
    outcome = panel_outcome(rows, criteria=COMPOSITES[composite], policies=tuple(policies))
    if outcome is None:
        raise ValueError("the adversarial baseline left a policy without ratings")
    return outcome.top()


def probe_state(
    materials: StudyMaterials,
    settings: ArmSettings,
    template: str,
    store: ResultStore,
    adversarial_store: ResultStore,
) -> ProbeState:
    jobs = probe_jobs(materials, settings, template)
    base = read_run(
        adversarial_store, candidate_jobs(BASELINE, materials, settings, None, settings.seed)
    )
    rerun = read_run(
        adversarial_store, candidate_jobs(BASELINE, materials, settings, None, settings.noise_seed)
    )
    probe = read_run(store, jobs)
    result = None
    if base.complete and rerun.complete and probe.complete and probe.ratings:
        policies = [p.id for p in materials.policies]
        target = _target(base.ratings, policies, settings.primary_composite)
        result = analyse(base.ratings, rerun.ratings, probe.ratings, target=target)
    panel = len(search_panel(materials, settings))
    return ProbeState(jobs, probe, base, rerun, panel, result)


def plan_probe(
    state: ProbeState,
    store: ResultStore,
    ledger: BatchLedger,
    settings: SpendSettings,
    external: float,
) -> Plan:
    """The probe's jobs not yet finished or in flight; the study's submit checks the ceilings."""
    flying = jobs_in_flight(ledger)
    todo = [j for j in state.jobs if j.job_id not in flying and not store.exists(j.job_id)]
    build = BuildResult(jobs=todo, total=len(todo), skipped=0, duplicates=0, per_spec=[])
    return plan_from_build(build, store, ledger, settings, None, external)
