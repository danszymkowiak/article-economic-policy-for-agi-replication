import shutil
from pathlib import Path

import pytest
import yaml

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.config import load_config
from llm_panel.domain.results import StoredRow

REPO = Path(__file__).parents[1]
SNAP = "fake-model-2026-01-01"


@pytest.fixture
def env(tmp_path):
    """A temp project: config, design, inputs, and a shared in-memory fake client."""
    shutil.copytree(REPO / "designs" / "fake_inputs", tmp_path / "inputs")
    design = {
        "mode": "full",
        "repeats": 1,
        "factors": {
            "model": [{"provider": "fake", "snapshot": SNAP}],
            "persona_source": ["reconstructed"],
            "paraphrase": ["baseline"],
            "policy_blinding": ["named"],
            "evidence_packet": ["none"],
            "presentation_order": ["fixed"],
            "score_aggregation": ["mean"],
        },
    }
    (tmp_path / "design.yaml").write_text(yaml.safe_dump(design))
    cfg = {
        "max_spend_usd": 15,
        "approved_providers": ["fake"],
        "paths": {"raw_store": "raw.jsonl", "ledger": "ledger.jsonl", "inputs_dir": "inputs"},
        "prices": {SNAP: {"input": 1.0, "output": 5.0}},
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg))

    class Env:
        root = tmp_path
        client = FakeModelClient()
        config_path = tmp_path / "config.yaml"

        def set_config(self, **kw):
            data = yaml.safe_load(self.config_path.read_text())
            data.update(kw)
            self.config_path.write_text(yaml.safe_dump(data))

        def run(self, *args, client=None):
            c = client or self.client
            argv = ["--config", str(self.config_path), *args]
            return main(argv, client_factory=lambda provider: c, now=lambda: "2026-10-03T00:00:00Z")

        def design(self):
            return ["--design", str(tmp_path / "design.yaml")]

        def store(self):
            return JsonlResultStore(tmp_path / "raw.jsonl")

        def ledger(self):
            return JsonlBatchLedger(tmp_path / "ledger.jsonl")

    return Env()


# 3 personas x 2 criteria x 1 repeat, all policies in one prompt = 6 jobs
N_JOBS = 6


def test_config_key_max_spend_usd_is_15():
    assert load_config(REPO / "config.yaml").spend.max_spend_usd == 15


def test_config_cannot_raise_ceiling_above_15(env):
    env.set_config(max_spend_usd=15.01)
    with pytest.raises(ValueError, match="max_spend_usd"):
        load_config(env.config_path)
    env.set_config(max_spend_usd=5)
    assert load_config(env.config_path).spend.max_spend_usd == 5


def test_plan_dry_run_prints_counts_and_cost_and_changes_nothing(env, capsys):
    assert env.run("plan", "--dry-run", *env.design()) == 0
    out = capsys.readouterr().out
    assert f"jobs to submit: {N_JOBS}" in out
    assert f"fake: {N_JOBS} jobs, estimated $" in out
    assert "ceiling $15.00" in out
    assert env.client.submitted_batches == []
    assert not (env.root / "ledger.jsonl").exists()
    assert list(env.store().iter_rows()) == []


def test_submit_refuses_without_confirm(env, capsys):
    assert env.run("submit", *env.design()) == 2
    assert "--confirm" in capsys.readouterr().err
    assert env.client.submitted_batches == []
    assert env.ledger().entries() == []


def test_submit_refuses_when_estimate_exceeds_ceiling(env, capsys):
    env.set_config(max_spend_usd=1e-6)
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "exceeds ceiling" in capsys.readouterr().err
    assert env.client.submitted_batches == []


def test_submit_refuses_when_cumulative_actual_spend_plus_estimate_exceeds(env, capsys):
    # prior actual spend: 1M input tokens at $1 = $1.00, leaving less than any job set needs
    env.set_config(max_spend_usd=1.0005)
    env.store().append(
        StoredRow(
            job_id="old", status="ok", attempt=1, provider="fake", model_snapshot=SNAP,
            temperature=1.0, seed=0, timestamp="t", request={}, response={},
            usage={"input_tokens": 1_000_000, "output_tokens": 0}, batch_id="b0",
        )
    )  # fmt: skip
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "exceeds ceiling" in capsys.readouterr().err
    assert env.client.submitted_batches == []


def test_outstanding_batches_count_toward_ceiling_and_are_not_resubmitted(env, capsys):
    assert env.run("submit", "--confirm", *env.design()) == 0
    capsys.readouterr()
    env.run("plan", *env.design())
    out = capsys.readouterr().out
    assert "jobs to submit: 0" in out and f"in flight: {N_JOBS}" in out
    assert env.run("status") == 0
    assert "outstanding $0.0" in capsys.readouterr().out  # nonzero, small


def test_submit_refuses_unapproved_provider(env, capsys):
    env.set_config(approved_providers=[])
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "not approved" in capsys.readouterr().err
    assert env.client.submitted_batches == []


def test_submit_refuses_model_without_price(env, capsys):
    env.set_config(prices={})
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "no price configured" in capsys.readouterr().err


def test_end_to_end_submit_collect_status(env, capsys):
    assert env.run("submit", "--confirm", *env.design()) == 0
    assert [e["event"] for e in env.ledger().entries()] == ["intent", "submitted"]
    assert env.run("collect") == 0
    rows = list(env.store().iter_rows())
    assert len(rows) == N_JOBS and {r.status for r in rows} == {"ok"}
    assert all(r.usage["input_tokens"] > 0 and r.request["prompt"] for r in rows)
    capsys.readouterr()
    assert env.run("status") == 0
    out = capsys.readouterr().out
    assert "of ceiling $15.00" in out and "'ok': 6" in out and "pending: 0" in out
    # rerun skips finished jobs
    env.run("plan", *env.design())
    assert "jobs to submit: 0" in capsys.readouterr().out
    assert env.run("submit", "--confirm", *env.design()) == 0
    assert len(env.client.submitted_batches) == 1  # nothing new sent


def test_collect_leaves_unfinished_batches_pending(env, capsys):
    client = FakeModelClient(pending_polls=1)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)
    assert "1 still pending" in capsys.readouterr().out
    env.run("collect", client=client)
    assert len(list(env.store().iter_rows())) == N_JOBS


def malformed_first_job(env, attempts):
    from llm_panel.application.build_jobs import build_jobs
    from llm_panel.bootstrap.design_loader import load_design
    from llm_panel.bootstrap.inputs_loader import load_inputs
    from llm_panel.domain.design import to_run_specs

    specs = to_run_specs(load_design(env.root / "design.yaml"))
    inputs = load_inputs(env.root / "inputs")
    job = build_jobs(specs, inputs, env.store()).jobs[0]
    return job, FakeModelClient(malformed={job.job_id}, malformed_attempts=attempts)


def test_malformed_response_is_retried_once_then_succeeds(env):
    job, client = malformed_first_job(env, attempts=1)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)  # attempt 1 invalid -> retry batch submitted
    assert len(client.submitted_batches) == 2
    env.run("collect", client=client)
    rows = [r for r in env.store().iter_rows() if r.job_id == job.job_id]
    assert [(r.status, r.attempt) for r in rows] == [("invalid", 1), ("ok", 2)]
    assert env.store().exists(job.job_id)


def test_malformed_twice_is_logged_as_failure(env):
    job, client = malformed_first_job(env, attempts=2)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)
    env.run("collect", client=client)
    rows = [r for r in env.store().iter_rows() if r.job_id == job.job_id]
    assert [(r.status, r.attempt) for r in rows] == [("invalid", 1), ("failed", 2)]
    assert rows[-1].error
    assert len(client.submitted_batches) == 2  # no third attempt


def test_retry_blocked_by_ceiling_is_deferred_then_runs_once_budget_allows(env):
    job, client = malformed_first_job(env, attempts=1)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.set_config(max_spend_usd=0.0)  # nothing left to spend: the retry must be withheld
    env.run("collect", client=client)
    rows = [r for r in env.store().iter_rows() if r.job_id == job.job_id]
    assert [r.status for r in rows] == ["invalid", "deferred"]
    assert "retry deferred" in rows[-1].error and not env.store().exists(job.job_id)
    assert len(client.submitted_batches) == 1
    env.set_config(max_spend_usd=15)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)
    rows = [r for r in env.store().iter_rows() if r.job_id == job.job_id]
    assert [(r.status, r.attempt) for r in rows][-1] == ("ok", 2)


class FlakySubmit(FakeModelClient):
    """Raises on the Nth submit_batch call."""

    def __init__(self, fail_on, **kw):
        super().__init__(**kw)
        self.fail_on, self.calls = fail_on, 0

    def submit_batch(self, jobs):
        self.calls += 1
        if self.calls == self.fail_on:
            raise ConnectionError("boom")
        return super().submit_batch(jobs)


def test_retry_once_holds_even_if_retry_submit_fails(env):
    job = malformed_first_job(env, attempts=99)[0]
    client = FlakySubmit(fail_on=2, malformed={job.job_id}, malformed_attempts=99)
    env.run("submit", "--confirm", *env.design(), client=client)
    with pytest.raises(ConnectionError):
        env.run("collect", client=client)  # retry submit blows up after rows were written
    env.run("submit", "--confirm", *env.design(), client=client)  # picks the job up again
    env.run("collect", client=client)
    rows = [r for r in env.store().iter_rows() if r.job_id == job.job_id]
    assert [(r.status, r.attempt) for r in rows] == [("invalid", 1), ("failed", 2)]
    env.run("submit", "--confirm", *env.design(), client=client)
    assert client.calls == 3  # first batch, failed retry, resubmission - no fourth execution


def test_missing_provider_usage_is_charged_at_estimate(env):
    job, client = malformed_first_job(env, attempts=99)
    client._errors.add(job.job_id)  # provider error row with no usage
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)
    row = next(r for r in env.store().iter_rows() if r.job_id == job.job_id)
    assert row.usage["estimated"] and row.usage["input_tokens"] > 0


def test_recollect_is_idempotent(env):
    job, client = malformed_first_job(env, attempts=1)
    env.run("submit", "--confirm", *env.design(), client=client)
    env.run("collect", client=client)
    n = len(list(env.store().iter_rows()))
    # simulate a crash before the 'collected' event: forget it and collect the batch again
    env.ledger()._path.write_text(
        "".join(
            line
            for line in env.ledger()._path.read_text().splitlines(keepends=True)
            if '"event": "collected"' not in line
        )
    )
    env.run("collect", client=client)
    first_batch_rows = [r for r in env.store().iter_rows() if r.batch_id == "fake-batch-1"]
    assert len(first_batch_rows) == N_JOBS and len(list(env.store().iter_rows())) >= n


def test_intent_without_batch_id_counts_as_outstanding_and_blocks_resubmit(env, capsys):
    client = FlakySubmit(fail_on=0)
    env.run("submit", "--confirm", *env.design(), client=client)
    capsys.readouterr()
    # simulate a crash after the intent was written but before the batch id was recorded
    lines = env.ledger()._path.read_text().splitlines(keepends=True)
    env.ledger()._path.write_text(lines[0])
    env.run("status", client=client)
    out = capsys.readouterr().out
    assert "WARNING: 1 submission(s)" in out and "outstanding $0.0" in out
    env.run("plan", *env.design())
    assert "jobs to submit: 0" in capsys.readouterr().out


def test_failed_submit_call_is_resolved_not_stuck(env):
    client = FlakySubmit(fail_on=1)
    with pytest.raises(ConnectionError):
        env.run("submit", "--confirm", *env.design(), client=client)
    assert env.run("submit", "--confirm", *env.design(), client=client) == 0


@pytest.mark.parametrize(
    "key,value",
    [("batch_discount", 0), ("chars_per_token", 0), ("est_output_tokens_per_policy", 0)],
)
def test_config_rejects_settings_that_would_zero_estimates(env, key, value):
    env.set_config(**{key: value})
    with pytest.raises(ValueError, match=key):
        load_config(env.config_path)


def test_overlapping_run_is_refused_by_lock(env, capsys):
    from llm_panel.adapters.lock import exclusive_lock

    with exclusive_lock(env.root / "ledger.lock"):
        assert env.run("submit", "--confirm", *env.design()) == 2
    assert "holds" in capsys.readouterr().err
    assert env.client.submitted_batches == []


def test_append_after_torn_write_keeps_new_record_on_its_own_line(tmp_path):
    from tests.domain.test_results import row

    store = JsonlResultStore(tmp_path / "r.jsonl")
    store.append(row(job_id="j1"))
    with (tmp_path / "r.jsonl").open("a") as fh:
        fh.write('{"job_id": "torn')  # no newline: crash mid-write
    store.append(row(job_id="j2"))
    lines = (tmp_path / "r.jsonl").read_text().splitlines()
    assert len(lines) == 3 and '"j2"' in lines[2]
