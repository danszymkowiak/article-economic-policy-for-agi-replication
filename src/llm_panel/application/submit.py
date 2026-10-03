"""plan and submit: turn a design into batches, never exceeding the spend ceiling."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from llm_panel.application.build_jobs import BuildResult, StudyInputs, build_jobs
from llm_panel.application.spend import (
    Spend,
    attempt_counts,
    check_ceiling,
    compute_spend,
    estimate_jobs,
    jobs_in_flight,
    send_batch,
)
from llm_panel.domain.model_ids import ModelIdReport, check_model_ids
from llm_panel.domain.models import RenderedJob, RunSpec
from llm_panel.domain.pricing import SpendSettings
from llm_panel.ports import BatchLedger, ModelClient, ResultStore

ClientFactory = Callable[[str], ModelClient]


class ConfirmationRequired(RuntimeError):
    pass


class ProviderNotApproved(RuntimeError):
    pass


class ModelIdDrift(RuntimeError):
    pass


@dataclass(frozen=True)
class Plan:
    build: BuildResult
    jobs: list[RenderedJob]  # to submit now (excludes finished and in-flight jobs)
    in_flight: int
    cost_by_provider: dict[str, float]
    spend: Spend
    attempts: dict[str, int]  # job_id -> attempt number this submission would be
    model_ids: ModelIdReport = ModelIdReport()

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
    external: float = 0.0,
) -> Plan:
    build = build_jobs(specs, inputs, store)
    flying = jobs_in_flight(ledger)
    jobs = [
        j
        for j in build.jobs
        if j.job_id not in flying and (provider is None or j.provider == provider)
    ]
    counts = attempt_counts(store)
    return Plan(
        attempts={j.job_id: counts[j.job_id] + 1 for j in jobs},
        build=build,
        jobs=jobs,
        in_flight=sum(1 for j in build.jobs if j.job_id in flying),
        cost_by_provider=estimate_jobs(jobs, settings),
        spend=compute_spend(store, ledger, settings, external),
        model_ids=check_model_ids(store.iter_rows()),
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
    if plan.model_ids.has_issues:
        raise ModelIdDrift(
            f"model id drift in stored rows ({plan.model_ids.describe()}); rows may not be "
            "comparable. Inspect results/raw before spending more"
        )
    check_ceiling(plan.spend, plan.estimated_cost)

    by_provider: dict[str, list[RenderedJob]] = {}
    for job in plan.jobs:
        by_provider.setdefault(job.provider, []).append(job)
    batch_ids = []
    for provider, jobs in by_provider.items():
        client = client_factory(provider)
        batch_ids.append(
            send_batch(
                ledger, client, provider, jobs, plan.attempts, plan.cost_by_provider[provider], now
            )
        )
    return batch_ids
