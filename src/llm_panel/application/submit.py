"""plan and submit: turn a design into batches, never exceeding the spend ceiling."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from llm_panel.application.build_jobs import BuildResult, StudyInputs, build_jobs
from llm_panel.application.spend import (
    Spend,
    check_ceiling,
    compute_spend,
    estimate_jobs,
    job_entry,
    jobs_in_flight,
)
from llm_panel.domain.models import RenderedJob, RunSpec
from llm_panel.domain.pricing import SpendSettings
from llm_panel.ports import BatchLedger, ModelClient, ResultStore

ClientFactory = Callable[[str], ModelClient]


class ConfirmationRequired(RuntimeError):
    pass


class ProviderNotApproved(RuntimeError):
    pass


@dataclass(frozen=True)
class Plan:
    build: BuildResult
    jobs: list[RenderedJob]  # to submit now (excludes finished and in-flight jobs)
    in_flight: int
    cost_by_provider: dict[str, float]
    spend: Spend

    @property
    def estimated_cost(self) -> float:
        return sum(self.cost_by_provider.values())


def make_plan(
    specs: Sequence[RunSpec],
    inputs: StudyInputs,
    store: ResultStore,
    ledger: BatchLedger,
    settings: SpendSettings,
    provider: str | None = None,
) -> Plan:
    build = build_jobs(specs, inputs, store)
    flying = jobs_in_flight(ledger)
    jobs = [
        j
        for j in build.jobs
        if j.job_id not in flying and (provider is None or j.provider == provider)
    ]
    return Plan(
        build=build,
        jobs=jobs,
        in_flight=sum(1 for j in build.jobs if j.job_id in flying),
        cost_by_provider=estimate_jobs(jobs, settings),
        spend=compute_spend(store, ledger, settings),
    )


def submit(
    plan: Plan,
    ledger: BatchLedger,
    client_factory: ClientFactory,
    settings: SpendSettings,
    approved_providers: frozenset[str],
    now: Callable[[], str],
    *,
    confirm: bool,
) -> list[str]:
    """Submit the plan's jobs. Every guard runs before the first batch is sent."""
    if not confirm:
        raise ConfirmationRequired("submit needs --confirm")
    unapproved = sorted(set(plan.cost_by_provider) - approved_providers)
    if unapproved:
        raise ProviderNotApproved(f"provider(s) not approved for paid use: {', '.join(unapproved)}")
    check_ceiling(plan.spend, plan.estimated_cost)

    by_provider: dict[str, list[RenderedJob]] = {}
    for job in plan.jobs:
        by_provider.setdefault(job.provider, []).append(job)
    batch_ids = []
    for provider, jobs in by_provider.items():
        batch_id = client_factory(provider).submit_batch(jobs)
        ledger.record(
            {
                "event": "submitted",
                "batch_id": batch_id,
                "provider": provider,
                "attempt": 1,
                "submitted_at": now(),
                "est_cost": plan.cost_by_provider[provider],
                "jobs": [job_entry(j) for j in jobs],
            }
        )
        batch_ids.append(batch_id)
    return batch_ids
