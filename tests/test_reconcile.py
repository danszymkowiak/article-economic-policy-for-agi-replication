"""Reconcile a crashed mid-submit intent against a partial local batch file (no provider calls)."""

import json

import pytest

from llm_panel.adapters.jsonl import JsonlBatchLedger
from llm_panel.adapters.zen import ZenClient
from llm_panel.application.reconcile import ReconcileError, reconcile_intent
from llm_panel.application.spend import job_entry, jobs_in_flight, open_intents, pending_batches
from llm_panel.domain.pricing import Price, SpendSettings
from tests.domain.test_models import make_job

SETTINGS = SpendSettings(15.0, {"fake-1": Price(1.0, 5.0)})
NOW = lambda: "2026-10-04T20:00:00Z"  # noqa: E731


def _intent(ledger, jobs, intent_id="i1"):
    ledger.record(
        {"event": "intent", "intent_id": intent_id, "provider": "fake", "est_cost": 9.0,
         "submitted_at": "t0", "jobs": [job_entry(j) for j in jobs]}
    )  # fmt: skip


@pytest.fixture
def jobs():
    return [make_job(repeat=i) for i in range(4)]


@pytest.fixture
def ledger(tmp_path):
    return JsonlBatchLedger(tmp_path / "ledger.jsonl")


def test_records_submitted_for_answered_jobs_only(ledger, jobs):
    _intent(ledger, jobs)
    answered = {jobs[0].job_id, jobs[2].job_id}
    reconcile_intent(ledger, "i1", "zen-b1", answered, SETTINGS, NOW)
    assert open_intents(ledger) == []
    (batch,) = pending_batches(ledger)
    assert batch["batch_id"] == "zen-b1" and batch["intent_id"] == "i1"
    assert {j["job_id"] for j in batch["jobs"]} == answered
    assert 0 < batch["est_cost"] < 9.0  # estimate for the two answered jobs, not the full intent
    assert jobs_in_flight(ledger) == answered


def test_no_answers_resolves_intent_as_failed_submit(ledger, jobs):
    _intent(ledger, jobs)
    reconcile_intent(ledger, "i1", "zen-b1", set(), SETTINGS, NOW)
    assert open_intents(ledger) == [] and pending_batches(ledger) == []


def test_refuses_resolved_unknown_or_foreign(ledger, jobs):
    _intent(ledger, jobs)
    with pytest.raises(ReconcileError, match="not an open intent"):
        reconcile_intent(ledger, "nope", "zen-b1", set(), SETTINGS, NOW)
    with pytest.raises(ReconcileError, match="not in the intent"):
        reconcile_intent(ledger, "i1", "zen-b1", {"deadbeef"}, SETTINGS, NOW)
    reconcile_intent(ledger, "i1", "zen-b1", {jobs[0].job_id}, SETTINGS, NOW)
    with pytest.raises(ReconcileError, match="not an open intent"):
        reconcile_intent(ledger, "i1", "zen-b1", {jobs[0].job_id}, SETTINGS, NOW)


def _zen(tmp_path):
    return ZenClient(tmp_path / "zen", env={"OPENCODE_API_KEY": "k"})


def _batch_file(tmp_path, lines):
    d = tmp_path / "zen"
    d.mkdir()
    (d / "zen-b1.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))


def test_zen_lists_answered_jobs_and_closes_batch_once(tmp_path):
    _batch_file(
        tmp_path,
        [
            {"job_id": "a", "status": "ok", "text": "x"},
            {"job_id": "b", "status": "error", "text": ""},
        ],
    )
    client = _zen(tmp_path)
    assert client.answered_job_ids("zen-b1") == {"a", "b"}
    assert not client.fetch_results("zen-b1").done
    client.close_batch("zen-b1")
    client.close_batch("zen-b1")  # idempotent: one marker only
    assert client.fetch_results("zen-b1").done
    assert (tmp_path / "zen" / "zen-b1.jsonl").read_text().count("_done") == 1
    assert client.answered_job_ids("zen-b1") == {"a", "b"}


def test_zen_unknown_batch_file_is_refused(tmp_path):
    with pytest.raises(KeyError):
        _zen(tmp_path).answered_job_ids("zen-missing")
