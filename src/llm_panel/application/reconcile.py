"""reconcile: resolve an intent that never got a batch id (crash mid-submit)."""

from __future__ import annotations

from collections.abc import Callable, Collection

from llm_panel.application.spend import open_intents
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import SpendSettings, estimate_job_cost
from llm_panel.ports import BatchLedger


class ReconcileError(RuntimeError):
    pass


def reconcile_intent(
    ledger: BatchLedger,
    intent_id: str,
    batch_id: str,
    answered: Collection[str],
    settings: SpendSettings,
    now: Callable[[], str],
    close: Callable[[], None] = lambda: None,
) -> int:
    """Resolve an open intent given the job ids the provider answered before the crash.

    Those jobs become a submitted batch (so collect ingests the paid responses and nothing is
    paid twice); the rest stop counting as in flight and can be planned again. With no answers
    the intent is closed as a failed submit. `close` runs after validation, before the ledger
    write, to finish the provider's batch file. Returns the number of jobs salvaged."""
    intent = next((e for e in open_intents(ledger) if e["intent_id"] == intent_id), None)
    if intent is None:
        raise ReconcileError(f"{intent_id} is not an open intent")
    unknown = set(answered) - {j["job_id"] for j in intent["jobs"]}
    if unknown:
        raise ReconcileError(f"{len(unknown)} answered job(s) are not in the intent")
    if not answered:
        ledger.record({"event": "submit_failed", "intent_id": intent_id})
        return 0
    jobs = [j for j in intent["jobs"] if j["job_id"] in answered]
    est = sum(estimate_job_cost(RenderedJob.from_dict(j), settings) for j in jobs)
    close()
    ledger.record(
        {**intent, "event": "submitted", "batch_id": batch_id, "jobs": jobs, "est_cost": est,
         "reconciled_at": now(), "reconciled_from_jobs": len(intent["jobs"])}
    )  # fmt: skip
    return len(jobs)
