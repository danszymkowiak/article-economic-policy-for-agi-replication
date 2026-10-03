"""Spend accounting against the hard ceiling, built from stored usage and the batch ledger."""

from __future__ import annotations

import uuid
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import SpendSettings, estimate_job_cost, usage_cost
from llm_panel.domain.results import STATUS_INVALID
from llm_panel.ports import BatchLedger, ModelClient, ResultStore


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


def open_intents(ledger: BatchLedger) -> list[dict]:
    """Batches we meant to send but never saw acknowledged (crash mid-submit). They are
    counted as outstanding spend and in-flight jobs until someone reconciles them."""
    entries = ledger.entries()
    resolved = {e["intent_id"] for e in entries if e["event"] in ("submitted", "submit_failed")}
    return [e for e in entries if e["event"] == "intent" and e["intent_id"] not in resolved]


def attempt_counts(store: ResultStore) -> Counter:
    """Failed attempts so far per job (derived from the store, so it survives crashes)."""
    return Counter(r.job_id for r in store.iter_rows() if r.status == STATUS_INVALID)


def compute_spend(store: ResultStore, ledger: BatchLedger, settings: SpendSettings) -> Spend:
    actual = sum(
        usage_cost(row.usage, settings.price_for(row.model_snapshot), settings.batch_discount)
        for row in store.iter_rows()
    )
    outstanding = sum(e["est_cost"] for e in pending_batches(ledger))
    outstanding += sum(e["est_cost"] for e in open_intents(ledger))
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
    entries = pending_batches(ledger) + open_intents(ledger)
    return {j["job_id"] for e in entries for j in e["jobs"]}


def job_entry(job: RenderedJob, attempt: int = 1) -> dict:
    return {"job_id": job.job_id, "attempt": attempt, **job.to_dict()}


def send_batch(
    ledger: BatchLedger,
    client: ModelClient,
    provider: str,
    jobs: Sequence[RenderedJob],
    attempts: dict[str, int],
    est_cost: float,
    now: Callable[[], str],
) -> str:
    """Record intent, call the provider, record the batch id. The intent makes a crash between
    the provider call and the ledger write visible as outstanding spend instead of losing it."""
    intent_id = uuid.uuid4().hex
    base = {
        "intent_id": intent_id,
        "provider": provider,
        "submitted_at": now(),
        "est_cost": est_cost,
        "jobs": [job_entry(j, attempts.get(j.job_id, 1)) for j in jobs],
    }
    ledger.record({"event": "intent", **base})
    try:
        batch_id = client.submit_batch(jobs)
    except Exception:
        ledger.record({"event": "submit_failed", "intent_id": intent_id})
        raise
    ledger.record({"event": "submitted", "batch_id": batch_id, **base})
    return batch_id


def jobs_from_entry(entry: dict) -> Sequence[RenderedJob]:
    return [RenderedJob.from_dict(j) for j in entry["jobs"]]
