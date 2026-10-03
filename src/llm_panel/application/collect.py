"""collect: fetch finished batches, validate, store every outcome, retry malformed once."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from llm_panel.application.spend import (
    SpendCeilingError,
    check_ceiling,
    compute_spend,
    estimate_jobs,
    job_entry,
    jobs_from_entry,
    pending_batches,
)
from llm_panel.application.submit import ClientFactory
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import SpendSettings
from llm_panel.domain.results import (
    MAX_ATTEMPTS,
    STATUS_FAILED,
    STATUS_INVALID,
    STATUS_OK,
    ModelResponse,
    StoredRow,
)
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import BatchLedger, ResultStore


@dataclass(frozen=True)
class CollectReport:
    batches_collected: int = 0
    batches_pending: int = 0
    ok: int = 0
    invalid: int = 0
    failed: int = 0
    retried: int = 0


def _row(job, attempt, batch_id, status, response, usage, error, now) -> StoredRow:
    return StoredRow(
        job_id=job.job_id,
        status=status,
        attempt=attempt,
        provider=job.provider,
        model_snapshot=job.model_snapshot,
        temperature=job.temperature,
        seed=job.seed,
        timestamp=now(),
        request=job_entry(job),
        response=response,
        usage=usage,
        batch_id=batch_id,
        error=error,
    )


def _judge(job: RenderedJob, resp: ModelResponse | None) -> tuple[str, str | None]:
    """(status, error) for one response: 'ok' or 'bad'."""
    if resp is None:
        return "bad", "job missing from batch results"
    if resp.status != "ok":
        return "bad", resp.error or "provider error"
    try:
        parse_ratings(job, resp.text)
    except InvalidResponse as exc:
        return "bad", str(exc)
    return "ok", None


def collect(
    store: ResultStore,
    ledger: BatchLedger,
    client_factory: ClientFactory,
    settings: SpendSettings,
    now: Callable[[], str],
) -> CollectReport:
    report = CollectReport()
    for entry in pending_batches(ledger):
        client = client_factory(entry["provider"])
        result = client.fetch_results(entry["batch_id"])
        if not result.done:
            report = _bump(report, batches_pending=1)
            continue
        by_id = {r.job_id: r for r in result.responses}
        attempt = entry["attempt"]
        retry: list[RenderedJob] = []
        for job in jobs_from_entry(entry):
            if store.exists(job.job_id):  # e.g. re-collecting after a crash
                continue
            resp = by_id.get(job.job_id)
            verdict, error = _judge(job, resp)
            usage = dict(resp.usage) if resp else {}
            payload = dict(resp.raw) if resp else None
            if verdict == "ok":
                store.append(
                    _row(job, attempt, entry["batch_id"], STATUS_OK, payload, usage, None, now)
                )
                report = _bump(report, ok=1)
            elif attempt >= MAX_ATTEMPTS:
                store.append(
                    _row(job, attempt, entry["batch_id"], STATUS_FAILED, payload, usage, error, now)
                )
                report = _bump(report, failed=1)
            else:
                store.append(
                    _row(
                        job, attempt, entry["batch_id"], STATUS_INVALID, payload, usage, error, now
                    )
                )
                retry.append(job)
                report = _bump(report, invalid=1)
        # Mark collected before retrying so this batch no longer counts as outstanding spend.
        # A crash in between leaves non-terminal rows, which plan/submit simply re-run.
        ledger.record({"event": "collected", "batch_id": entry["batch_id"], "collected_at": now()})
        report = _retry(report, retry, entry, store, ledger, client_factory, settings, now)
        report = _bump(report, batches_collected=1)
    return report


def _retry(report, retry, entry, store, ledger, client_factory, settings, now) -> CollectReport:
    if not retry:
        return report
    try:
        spend = compute_spend(store, ledger, settings)
        estimate = estimate_jobs(retry, settings)
        check_ceiling(spend, sum(estimate.values()))
    except SpendCeilingError as exc:
        for job in retry:
            store.append(
                _row(job, entry["attempt"] + 1, entry["batch_id"], STATUS_FAILED, None, {},
                     f"retry blocked: {exc}", now)
            )  # fmt: skip
        return _bump(report, failed=len(retry), invalid=-len(retry))
    batch_id = client_factory(entry["provider"]).submit_batch(retry)
    ledger.record(
        {
            "event": "submitted",
            "batch_id": batch_id,
            "provider": entry["provider"],
            "attempt": entry["attempt"] + 1,
            "submitted_at": now(),
            "est_cost": sum(estimate.values()),
            "jobs": [job_entry(j) for j in retry],
        }
    )
    return _bump(report, retried=len(retry))


def _bump(report: CollectReport, **delta: int) -> CollectReport:
    values = {k: getattr(report, k) + delta.get(k, 0) for k in report.__dataclass_fields__}
    return CollectReport(**values)
