"""Spend accounting against the hard ceiling, built from stored usage and the batch ledger."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import SpendSettings, estimate_job_cost, usage_cost
from llm_panel.ports import BatchLedger, ResultStore


class SpendCeilingError(RuntimeError):
    pass


@dataclass(frozen=True)
class Spend:
    actual: float  # from usage fields of every stored row (failures cost money too)
    outstanding: float  # estimated cost of submitted batches not yet collected
    ceiling: float

    @property
    def committed(self) -> float:
        return self.actual + self.outstanding


def pending_batches(ledger: BatchLedger) -> list[dict]:
    entries = ledger.entries()
    collected = {e["batch_id"] for e in entries if e["event"] == "collected"}
    return [e for e in entries if e["event"] == "submitted" and e["batch_id"] not in collected]


def compute_spend(store: ResultStore, ledger: BatchLedger, settings: SpendSettings) -> Spend:
    actual = sum(
        usage_cost(row.usage, settings.price_for(row.model_snapshot), settings.batch_discount)
        for row in store.iter_rows()
    )
    outstanding = sum(e["est_cost"] for e in pending_batches(ledger))
    return Spend(actual=actual, outstanding=outstanding, ceiling=settings.max_spend_usd)


def estimate_jobs(jobs: Iterable[RenderedJob], settings: SpendSettings) -> dict[str, float]:
    """Estimated cost per provider."""
    out: dict[str, float] = {}
    for job in jobs:
        out[job.provider] = out.get(job.provider, 0.0) + estimate_job_cost(job, settings)
    return out


def check_ceiling(spend: Spend, new_estimate: float) -> None:
    total = spend.committed + new_estimate
    if total > spend.ceiling:
        raise SpendCeilingError(
            f"refusing: actual ${spend.actual:.4f} + outstanding ${spend.outstanding:.4f} + "
            f"new estimate ${new_estimate:.4f} = ${total:.4f} exceeds ceiling ${spend.ceiling:.2f}"
        )


def jobs_in_flight(ledger: BatchLedger) -> set[str]:
    return {j["job_id"] for e in pending_batches(ledger) for j in e["jobs"]}


def job_entry(job: RenderedJob) -> dict:
    return {"job_id": job.job_id, **job.to_dict()}


def jobs_from_entry(entry: dict) -> Sequence[RenderedJob]:
    return [RenderedJob.from_dict(j) for j in entry["jobs"]]
