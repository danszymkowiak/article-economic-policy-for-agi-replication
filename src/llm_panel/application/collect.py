"""collect: fetch finished batches, validate, store every outcome, retry malformed once."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from llm_panel.application.spend import (
    SpendCeilingError,
    check_ceiling,
    compute_spend,
    estimate_jobs,
    job_entry,
    pending_batches,
    send_batch,
)
from llm_panel.application.submit import ClientFactory
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import MissingPriceError, SpendSettings, estimated_usage
from llm_panel.domain.results import (
    MAX_ATTEMPTS,
    STATUS_DEFERRED,
    STATUS_DUPLICATE,
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
    deferred: int = 0


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
        request=job_entry(job, attempt),
        response=response,
        usage=usage,
        batch_id=batch_id,
        error=error,
    )


def _judge(job: RenderedJob, resp: ModelResponse | None) -> str | None:
    """None if the response is good, else the reason it is not."""
    if resp is None:
        return "job missing from batch results"
    if resp.status != "ok":
        return resp.error or "provider error"
    try:
        parse_ratings(job, resp.text)
    except InvalidResponse as exc:
        return str(exc)
    return None


def _usage(job: RenderedJob, resp: ModelResponse | None, settings: SpendSettings) -> dict:
    """Reported usage, or the estimate when the provider reported none: a job we sent may have
    been billed even if it came back missing or errored, so never count it as free."""
    usage = dict(resp.usage) if resp and resp.usage else {}
    if "input_tokens" in usage and "output_tokens" in usage:
        return usage
    return {**estimated_usage(job, settings), "estimated": True}


def collect(
    store: ResultStore,
    ledger: BatchLedger,
    client_factory: ClientFactory,
    settings: SpendSettings,
    now: Callable[[], str],
    external: float = 0.0,
) -> CollectReport:
    report = CollectReport()
    seen = {(r.job_id, r.batch_id) for r in store.iter_rows()}  # makes re-collect idempotent
    for entry in pending_batches(ledger):
        result = client_factory(entry["provider"]).fetch_results(entry["batch_id"])
        if not result.done:
            report = _bump(report, batches_pending=1)
            continue
        by_id = {r.job_id: r for r in result.responses}
        retry: list[tuple[RenderedJob, int]] = []
        for jd in entry["jobs"]:
            job, attempt = RenderedJob.from_dict(jd), jd.get("attempt", 1)
            if (job.job_id, entry["batch_id"]) in seen:
                continue
            resp = by_id.get(job.job_id)
            error = _judge(job, resp)
            usage = _usage(job, resp, settings)
            payload = dict(resp.raw) if resp else None
            bid = entry["batch_id"]
            if store.exists(job.job_id):  # finished via another batch: keep only its usage
                store.append(_row(job, attempt, bid, STATUS_DUPLICATE, payload, usage, error, now))
            elif error is None:
                store.append(_row(job, attempt, bid, STATUS_OK, payload, usage, None, now))
                report = _bump(report, ok=1)
            elif attempt >= MAX_ATTEMPTS:
                store.append(_row(job, attempt, bid, STATUS_FAILED, payload, usage, error, now))
                report = _bump(report, failed=1)
            else:
                store.append(_row(job, attempt, bid, STATUS_INVALID, payload, usage, error, now))
                retry.append((job, attempt))
                report = _bump(report, invalid=1)
        # Mark collected before retrying so this batch no longer counts as outstanding spend.
        # If the retry submit then fails, the job keeps a non-terminal 'invalid' row and no
        # in-flight batch; the next submit re-runs it with its attempt derived from the store.
        ledger.record({"event": "collected", "batch_id": entry["batch_id"], "collected_at": now()})
        report = _bump(report, batches_collected=1)
        report = _retry(
            report, retry, entry, store, ledger, client_factory, settings, now, external
        )
    return report


def _retry(
    report, retry, entry, store, ledger, client_factory, settings, now, external=0.0
) -> CollectReport:
    if not retry:
        return report
    jobs = [j for j, _ in retry]
    try:
        estimate = estimate_jobs(jobs, settings)
        check_ceiling(compute_spend(store, ledger, settings, external), sum(estimate.values()))
    except (SpendCeilingError, MissingPriceError) as exc:
        # Deferred, not failed: non-terminal, so a later submit can run it once budget allows.
        for job, attempt in retry:
            store.append(
                _row(job, attempt, entry["batch_id"], STATUS_DEFERRED, None, {},
                     f"retry deferred: {exc}", now)
            )  # fmt: skip
        return _bump(report, deferred=len(retry))
    attempts = {j.job_id: a + 1 for j, a in retry}
    client = client_factory(entry["provider"])
    send_batch(ledger, client, entry["provider"], jobs, attempts, sum(estimate.values()), now)
    return _bump(report, retried=len(retry))


def _bump(report: CollectReport, **delta: int) -> CollectReport:
    return replace(report, **{k: getattr(report, k) + v for k, v in delta.items()})
