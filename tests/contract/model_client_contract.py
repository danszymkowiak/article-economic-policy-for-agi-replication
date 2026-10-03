"""Behaviour every ModelClient adapter must satisfy.

To test a new provider, subclass `ModelClientContract` in `test_model_clients.py` and implement
`make_client`. The client must be backed by a fake transport: contract tests never spend money.
"""

import pytest

from llm_panel.domain.results import BatchResult, ModelResponse
from llm_panel.ports import ModelClient
from tests.domain.test_models import make_job


class ModelClientContract:
    provider: str  # the provider id jobs are built with

    def make_client(self, tmp_path) -> ModelClient:
        raise NotImplementedError

    def jobs(self, n=3):
        return [make_job(prompt=f"prompt {i}", provider=self.provider, seed=i) for i in range(n)]

    def fetch_when_done(self, client, batch_id, polls=20) -> BatchResult:
        for _ in range(polls):
            result = client.fetch_results(batch_id)
            if result.done:
                return result
        raise AssertionError("batch never finished")

    def test_satisfies_port_and_names_its_provider(self, tmp_path):
        client = self.make_client(tmp_path)
        assert isinstance(client, ModelClient)
        assert client.provider == self.provider

    def test_submit_returns_a_non_empty_batch_id(self, tmp_path):
        client = self.make_client(tmp_path)
        batch_id = client.submit_batch(self.jobs())
        assert isinstance(batch_id, str) and batch_id

    def test_one_response_per_job_keyed_by_job_id(self, tmp_path):
        client = self.make_client(tmp_path)
        jobs = self.jobs()
        result = self.fetch_when_done(client, client.submit_batch(jobs))
        assert all(isinstance(r, ModelResponse) for r in result.responses)
        assert sorted(r.job_id for r in result.responses) == sorted(j.job_id for j in jobs)

    def test_ok_responses_report_token_usage_for_spend_tracking(self, tmp_path):
        client = self.make_client(tmp_path)
        result = self.fetch_when_done(client, client.submit_batch(self.jobs()))
        ok = [r for r in result.responses if r.status == "ok"]
        assert ok
        for r in ok:
            assert {"input_tokens", "output_tokens"} <= set(r.usage)

    def test_failed_responses_carry_an_error_message(self, tmp_path):
        client = self.make_client(tmp_path)
        result = self.fetch_when_done(client, client.submit_batch(self.jobs()))
        for r in result.responses:
            if r.status != "ok":
                assert r.error

    def test_unfinished_batches_expose_no_responses(self, tmp_path):
        client = self.make_client(tmp_path)
        result = client.fetch_results(client.submit_batch(self.jobs()))
        if not result.done:
            assert result.responses == ()

    def test_unknown_batch_raises_key_error(self, tmp_path):
        client = self.make_client(tmp_path)
        with pytest.raises(KeyError):
            client.fetch_results("no-such-batch")

    def test_a_second_client_instance_can_collect_a_submitted_batch(self, tmp_path):
        # submit and collect run as separate cron invocations, so state must outlive the client
        first = self.make_client(tmp_path)
        jobs = self.jobs()
        batch_id = first.submit_batch(jobs)
        second = self.make_client(tmp_path)
        result = self.fetch_when_done(second, batch_id)
        assert len(result.responses) == len(jobs)
