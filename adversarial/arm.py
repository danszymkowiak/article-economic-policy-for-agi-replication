"""ADVERSARIAL ARM application layer: candidate jobs, search state from the arm's own store, and
submission through the study's plan/submit guards (--confirm, approved providers, model-id drift,
own ceiling and the global 15 USD cap).

Every candidate is one run (one seed) of the search panel: a small, seeded subset of the baseline
persona panel, every policy, the study's persona x policy prompt. A baseline rerun at a second
seed gives the repeat-noise reference for the target's rank. Rows carry cell id `ADV:<key>`.
"""

from __future__ import annotations

import random
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace

from adversarial.catalogue import (
    CATALOGUE,
    CRITERION_ORDER,
    EVIDENCE,
    PERSONA_SUBSET,
    TEMPERATURE,
    WORDING,
    check_catalogue,
)
from adversarial.search import (
    Candidate,
    EditSize,
    Outcome,
    SearchState,
    depth_one,
    edit_packet,
    edit_size,
    extend,
    panel_outcome,
    search,
)
from llm_panel.application.build_jobs import BuildResult
from llm_panel.application.spend import Spend, compute_spend, estimate_jobs, jobs_in_flight
from llm_panel.application.submit import Plan, plan_from_build
from llm_panel.domain.analysis_baseline import COMPOSITES
from llm_panel.domain.models import Persona, RenderedJob
from llm_panel.domain.oat_design import BASELINE_WORDING, PERSONA_POLICY, Cell, Factors
from llm_panel.domain.pricing import HARD_CEILING_USD, SpendSettings
from llm_panel.domain.results import STATUS_OK
from llm_panel.domain.study_jobs import StudyMaterials, jobs_for_cell_repeat
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import BatchLedger, ResultStore

BASELINE = Candidate(())
BASELINE_KEY, NOISE_KEY = "baseline", "baseline-rerun"
CELL_PREFIX = "ADV:"
BASELINE_PENDING = "baseline pending"
BUDGET_EXHAUSTED = "budget exhausted"
MAX_DEPTH = 2  # prereg s9 draft: combinations up to depth 2
MAX_CANDIDATES = 30


@dataclass(frozen=True)
class ArmSettings:
    baseline: Factors
    search_personas: int  # size of the small fixed search panel
    panel_seed: int  # seeds the draw of the search panel from the baseline panel
    seed: int  # sampling seed of every candidate run
    noise_seed: int  # sampling seed of the baseline rerun
    primary_composite: str
    max_depth: int = MAX_DEPTH
    max_candidates: int = MAX_CANDIDATES

    def __post_init__(self) -> None:
        if not 1 <= self.max_depth <= MAX_DEPTH:
            raise ValueError(f"max_depth must be within [1, {MAX_DEPTH}]")
        if not 1 <= self.max_candidates <= MAX_CANDIDATES:
            raise ValueError(f"max_candidates must be within [1, {MAX_CANDIDATES}]")
        if self.search_personas < 2:
            raise ValueError("search_personas must be >= 2")
        if self.seed == self.noise_seed:
            raise ValueError("the baseline rerun needs a seed of its own")
        if self.primary_composite not in COMPOSITES:
            raise ValueError(f"unknown composite {self.primary_composite!r}")
        if self.baseline.temperature is not None:
            raise ValueError("the baseline uses the provider-default temperature, as study cell B")


def search_panel(materials: StudyMaterials, settings: ArmSettings) -> tuple[Persona, ...]:
    panel = list(materials.personas(settings.baseline.persona_source))
    if settings.search_personas > len(panel):
        raise ValueError(f"search panel of {settings.search_personas} exceeds the panel")
    chosen = set(
        random.Random(settings.panel_seed).sample(range(len(panel)), settings.search_personas)
    )
    return tuple(p for i, p in enumerate(panel) if i in chosen)


def _primary_criteria(settings: ArmSettings) -> tuple[str, ...]:
    return COMPOSITES[settings.primary_composite]


def candidate_jobs(
    candidate: Candidate,
    materials: StudyMaterials,
    settings: ArmSettings,
    target: str | None,
    seed: int,
) -> list[RenderedJob]:
    """The candidate's rendered jobs: the baseline with each perturbation applied to the
    materials (template, target packet, criteria order) or factors (temperature). A persona drop
    changes no job; it is applied when the candidate is evaluated."""
    base = settings.baseline
    templates = {k: dict(v) for k, v in materials.templates.items()}
    template = templates[PERSONA_POLICY][BASELINE_WORDING]
    packets = {k: dict(v) for k, v in materials.packets.items()}
    criteria = list(materials.criteria)
    factors: Factors = base
    for p in candidate.perturbations:
        if p.kind == WORDING:
            template = template.replace(p.old, p.new, 1)
        elif p.kind == EVIDENCE:
            if target is None:
                raise ValueError("evidence edits need the target policy")
            level = packets[base.evidence]
            level[target] = edit_packet(level[target], p.op)
        elif p.kind == TEMPERATURE:
            factors = replace(factors, temperature=p.temperature)
        elif p.kind == CRITERION_ORDER:
            if p.op == "reverse":
                criteria.reverse()
            else:
                primary = set(_primary_criteria(settings))
                criteria.sort(key=lambda c: c.id not in primary)  # stable
    templates[PERSONA_POLICY][BASELINE_WORDING] = template
    m = replace(
        materials,
        panels={**materials.panels, base.persona_source: search_panel(materials, settings)},
        templates=templates, packets=packets, criteria=tuple(criteria),
    )  # fmt: skip
    key = candidate.key or BASELINE_KEY
    cell = Cell(f"{CELL_PREFIX}{key}", "ADV", "ADV", factors, (seed,))
    return jobs_for_cell_repeat(cell, 0, m)


def _prompts(jobs: Sequence[RenderedJob]) -> dict[str, str]:
    return {f"{j.persona_id}|{j.policy_ids[0]}": j.prompt for j in jobs}


class _StoreView:
    """Terminal job ids and parsed ok ratings of the arm's store, read once."""

    def __init__(self, store: ResultStore) -> None:
        self.terminal: set[str] = set()
        self.ratings: dict[str, list[tuple[str, str, str, float]]] = {}
        self.failed: set[str] = set()
        for row in store.iter_rows():
            if row.is_terminal:
                self.terminal.add(row.job_id)
            if row.status != STATUS_OK or row.job_id in self.ratings:
                continue
            job = RenderedJob.from_dict(row.request)
            try:
                parsed = parse_ratings(job, (row.response or {}).get("text") or "")
            except InvalidResponse:
                continue
            self.ratings[row.job_id] = [
                (r.persona_id, r.policy_id, r.criterion_id, r.score) for r in parsed
            ]
        self.failed = self.terminal - set(self.ratings)

    def complete(self, jobs: Sequence[RenderedJob]) -> bool:
        return all(j.job_id in self.terminal for j in jobs)

    def outcome(
        self, jobs: Sequence[RenderedJob], m: StudyMaterials, settings: ArmSettings, drop_for
    ) -> Outcome | None:
        ratings = [r for j in jobs for r in self.ratings.get(j.job_id, ())]
        return panel_outcome(
            ratings, criteria=_primary_criteria(settings),
            policies=tuple(p.id for p in m.policies), drop_top_for=drop_for,
        )  # fmt: skip


@dataclass(frozen=True)
class ArmState:
    status: str
    target: str | None
    baseline: Outcome | None
    noise: Outcome | None
    search: SearchState | None
    jobs: dict[str, list[RenderedJob]]  # candidate key (and baseline keys) -> jobs
    needed: tuple[str, ...]  # keys still to run, in search order
    failed_jobs: dict[str, int]  # key -> jobs that ended without a usable reply
    panel_size: int


def arm_state(materials: StudyMaterials, settings: ArmSettings, store: ResultStore) -> ArmState:
    check_catalogue(CATALOGUE, materials.templates[PERSONA_POLICY][BASELINE_WORDING])
    view = _StoreView(store)
    panel = len(search_panel(materials, settings))
    base_jobs = candidate_jobs(BASELINE, materials, settings, None, settings.seed)
    noise_jobs = candidate_jobs(BASELINE, materials, settings, None, settings.noise_seed)
    jobs = {BASELINE_KEY: base_jobs, NOISE_KEY: noise_jobs}
    failed = {k: sum(1 for j in v if j.job_id in view.failed) for k, v in jobs.items()}
    if not (view.complete(base_jobs) and view.complete(noise_jobs)):
        needed = (BASELINE_KEY, NOISE_KEY)
        return ArmState(BASELINE_PENDING, None, None, None, None, jobs, needed, failed, panel)
    baseline = view.outcome(base_jobs, materials, settings, None)
    noise = view.outcome(noise_jobs, materials, settings, None)
    if baseline is None:
        raise ValueError("the baseline run left a policy without ratings; the search cannot start")
    target = baseline.top()

    def jobs_of(c: Candidate) -> list[RenderedJob]:
        if c.key not in jobs:
            jobs[c.key] = candidate_jobs(c, materials, settings, target, settings.seed)
        return jobs[c.key]

    def drop_for(c: Candidate) -> str | None:
        return target if any(p.kind == PERSONA_SUBSET for p in c.perturbations) else None

    def outcome_of(c: Candidate) -> Outcome | None:
        return view.outcome(jobs_of(c), materials, settings, drop_for(c))

    def size_of(c: Candidate) -> EditSize:
        singles = [_prompts(jobs_of(Candidate((p,)))) for p in c.perturbations]
        return edit_size(_prompts(base_jobs), singles)

    outcomes = _LazyOutcomes(lambda c: view.complete(jobs_of(c)), outcome_of)
    state = search(
        CATALOGUE, outcomes, size_of, target=target,
        base_rank=baseline.ranks[target], max_depth=settings.max_depth,
        max_candidates=settings.max_candidates,
    )  # fmt: skip
    for t in state.tried:
        failed[t.candidate.key] = sum(1 for j in jobs_of(t.candidate) if j.job_id in view.failed)
    for c in state.needed:
        jobs_of(c)
    needed = tuple(c.key for c in state.needed)
    return ArmState(state.status, target, baseline, noise, state, jobs, needed, failed, panel)


class _LazyOutcomes(Mapping[str, Outcome | None]):
    """Outcomes of complete candidates, keyed by candidate key, rendered and read only when the
    search asks (it asks about a few dozen of the possible depth-1 and depth-2 candidates)."""

    def __init__(self, complete, outcome) -> None:
        first = depth_one(CATALOGUE)
        self._index = {c.key: c for c in first + [x for d in first for x in extend(d, CATALOGUE)]}
        self._complete, self._outcome = complete, outcome
        self._cache: dict[str, Outcome | None] = {}

    def __contains__(self, key) -> bool:
        return key in self._index and self._complete(self._index[key])

    def __getitem__(self, key: str) -> Outcome | None:
        if key not in self:
            raise KeyError(key)
        if key not in self._cache:
            self._cache[key] = self._outcome(self._index[key])
        return self._cache[key]

    def __iter__(self) -> Iterator[str]:
        return (k for k in self._index if k in self)

    def __len__(self) -> int:
        return sum(1 for _ in self)


@dataclass(frozen=True)
class Submission:
    state: ArmState
    plan: Plan
    keys: tuple[str, ...]  # candidates whose remaining jobs are in this submission
    waiting: tuple[str, ...]  # needed candidates whose jobs are all in flight
    unaffordable: tuple[str, ...]  # needed candidates that do not fit under the ceilings
    spend: Spend

    @property
    def status(self) -> str:
        if self.state.needed and not self.keys and not self.waiting and self.unaffordable:
            return BUDGET_EXHAUSTED
        return self.state.status


def plan_submission(
    state: ArmState,
    store: ResultStore,
    ledger: BatchLedger,
    settings: SpendSettings,
    external: float,
) -> Submission:
    """Whole candidates in search order while their estimated cost fits under both the arm's own
    ceiling and the global cap; the first that does not fit stops the selection (no skipping
    ahead to cheaper ones). The study's submit re-checks the ceiling on the result."""
    spend = compute_spend(store, ledger, settings, external)
    room = min(spend.ceiling - spend.committed, HARD_CEILING_USD - spend.committed - external)
    flying = jobs_in_flight(ledger)
    chosen: list[RenderedJob] = []
    seen: set[str] = set()
    keys, waiting, unaffordable = [], [], []
    for key in state.needed:
        new = []
        for j in state.jobs[key]:
            if j.job_id in seen or j.job_id in flying or store.exists(j.job_id):
                continue
            new.append(j)
            seen.add(j.job_id)
        if not new:
            if any(j.job_id in flying for j in state.jobs[key]):
                waiting.append(key)
            continue
        if unaffordable:
            unaffordable.append(key)
            continue
        cost = sum(estimate_jobs(new, settings).values())
        if cost > room:
            unaffordable.append(key)
            continue
        room -= cost
        chosen += new
        keys.append(key)
    build = BuildResult(jobs=chosen, total=len(chosen), skipped=0, duplicates=0, per_spec=[])
    plan = plan_from_build(build, store, ledger, settings, None, external)
    return Submission(state, plan, tuple(keys), tuple(waiting), tuple(unaffordable), spend)
