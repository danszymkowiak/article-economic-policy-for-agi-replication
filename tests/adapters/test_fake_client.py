import json

import jsonschema

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.domain.schema import RESPONSE_SCHEMA
from llm_panel.ports import ModelClient
from tests.domain.test_models import make_job


def jobs():
    return [make_job(prompt="x" * 40, seed=s) for s in range(3)]


def test_satisfies_port():
    assert isinstance(FakeModelClient(), ModelClient)


def test_schema_itself_is_valid():
    jsonschema.Draft202012Validator.check_schema(RESPONSE_SCHEMA)


def test_deterministic_scores_valid_against_schema():
    a, b = FakeModelClient(), FakeModelClient()
    ra = a.fetch_results(a.submit_batch(jobs()))
    rb = b.fetch_results(b.submit_batch(jobs()))
    assert ra.done and [r.text for r in ra.responses] == [r.text for r in rb.responses]
    for r in ra.responses:
        payload = json.loads(r.text)
        jsonschema.validate(payload, RESPONSE_SCHEMA)
        assert [x["policy"] for x in payload["ratings"]] == ["a", "b"]


def test_scores_differ_between_jobs():
    c = FakeModelClient()
    texts = {r.text for r in c.fetch_results(c.submit_batch(jobs())).responses}
    assert len(texts) == 3


def test_usage_fields_synthetic_and_stable():
    c = FakeModelClient()
    (r, *_) = c.fetch_results(c.submit_batch(jobs())).responses
    assert r.usage == {"input_tokens": 10, "output_tokens": 80}
    assert r.raw["usage"] == r.usage


def test_malformed_then_clean_on_retry():
    job = jobs()[0]
    c = FakeModelClient(malformed={job.job_id})
    first = c.fetch_results(c.submit_batch([job])).responses[0]
    assert first.text == "this is not json"
    second = c.fetch_results(c.submit_batch([job])).responses[0]
    jsonschema.validate(json.loads(second.text), RESPONSE_SCHEMA)


def test_errors_and_pending():
    job = jobs()[0]
    c = FakeModelClient(errors={job.job_id}, pending_polls=1)
    bid = c.submit_batch([job])
    assert not c.fetch_results(bid).done
    r = c.fetch_results(bid).responses[0]
    assert r.status == "error" and r.error


def test_job_scorer_plants_scores_from_the_job_and_label():
    seen = []

    def planted(job, label):
        seen.append((job.seed, label))
        return 10 * job.seed + (1 if label == "b" else 0)

    c = FakeModelClient(job_scorer=planted)
    responses = c.fetch_results(c.submit_batch(jobs())).responses
    scores = [[x["score"] for x in json.loads(r.text)["ratings"]] for r in responses]
    assert scores == [[0, 1], [10, 11], [20, 21]]
    assert seen[:2] == [(0, "a"), (0, "b")]
