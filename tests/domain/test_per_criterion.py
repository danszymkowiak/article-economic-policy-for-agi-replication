"""TASK-33: persona x policy jobs whose reply holds one score and rationale per criterion
(the paper's Appendix B per-policy profile), and provider-default temperature."""

import json

import pytest

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.zen.protocol import build_request
from llm_panel.domain.hashing import job_id
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.pricing import SpendSettings, estimated_usage
from llm_panel.domain.schema import CRITERION_RESPONSE_SCHEMA, RESPONSE_SCHEMA
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from tests.domain.test_models import make_job

CRITS = ("standards_of_living", "ownership_of_gains", "full_transformation")


def pp_job(**kw):
    base = dict(
        criterion_id="", criterion_ids=CRITS, policy_ids=("ubc",), policy_labels=("ubc",),
        cell_id="B",
    )  # fmt: skip
    base.update(kw)
    return make_job(**base)


def reply(*items):
    return json.dumps(
        {"ratings": [{"criterion": c, "score": s, "rationale": f"why {c}"} for c, s in items]}
    )


def test_per_criterion_job_needs_exactly_one_policy():
    with pytest.raises(ValueError, match="one policy"):
        pp_job(policy_ids=("a", "b"), policy_labels=("a", "b"))


def test_n_ratings_counts_policies_times_criteria():
    assert pp_job().n_ratings == 3
    assert make_job().n_ratings == 2  # policy-keyed: one rating per policy


def test_round_trip_keeps_criterion_ids_and_cell():
    job = pp_job()
    back = RenderedJob.from_dict(json.loads(json.dumps(job.to_dict())))
    assert back == job and back.criterion_ids == CRITS and back.cell_id == "B"


def test_old_ledger_entries_without_new_fields_still_load():
    data = make_job().to_dict()
    del data["criterion_ids"], data["cell_id"]
    assert RenderedJob.from_dict(data).criterion_ids == ()


def test_criterion_schema_mirrors_policy_schema_keyed_by_criterion():
    item = CRITERION_RESPONSE_SCHEMA["properties"]["ratings"]["items"]
    assert item["required"] == ["criterion", "score", "rationale"]
    assert item["properties"]["score"] == {"type": "number", "minimum": 0, "maximum": 100}
    assert RESPONSE_SCHEMA["properties"]["ratings"]["items"]["required"][0] == "policy"


def test_valid_per_criterion_reply_gives_one_rating_per_criterion():
    job = pp_job()
    ratings = parse_ratings(job, reply(*((c, 10 * i) for i, c in enumerate(CRITS))))
    assert {r.criterion_id: r.score for r in ratings} == dict(zip(CRITS, (0, 10, 20), strict=True))
    assert {r.policy_id for r in ratings} == {"ubc"}
    assert {r.job_id for r in ratings} == {job.job_id}
    assert ratings[0].rationale == "why standards_of_living"


@pytest.mark.parametrize(
    "bad",
    [
        reply(("standards_of_living", 1), ("ownership_of_gains", 2)),  # one missing
        reply(*((c, 1) for c in CRITS), ("meaning_human_value", 3)),  # unknown criterion
        reply(*((c, 1) for c in CRITS), ("full_transformation", 3)),  # duplicate
        reply(("standards_of_living", 101), ("ownership_of_gains", 2), ("full_transformation", 3)),
        json.dumps({"ratings": [{"policy": "ubc", "score": 5, "rationale": "r"}]}),  # wrong key
    ],
)
def test_bad_per_criterion_replies_are_rejected(bad):
    with pytest.raises(InvalidResponse):
        parse_ratings(pp_job(), bad)


def test_policy_keyed_jobs_still_use_the_policy_schema():
    with pytest.raises(InvalidResponse):
        parse_ratings(make_job(), reply(("a", 1), ("b", 2)))


def test_estimated_output_scales_with_ratings_per_call():
    s = SpendSettings(max_spend_usd=15, prices={}, est_output_tokens_per_policy=50)
    assert estimated_usage(pp_job(), s)["output_tokens"] == 150
    assert estimated_usage(make_job(), s)["output_tokens"] == 100


def test_provider_default_temperature_is_none_and_hashes_apart_from_any_value():
    assert job_id("p", "m", None, 0) != job_id("p", "m", 0.0, 0)
    assert job_id("p", "m", None, 0) == job_id("p", "m", None, 0)
    assert job_id("p", "m", 1, 0) == job_id("p", "m", 1.0, 0)  # existing ids unchanged


def test_zen_request_omits_temperature_when_provider_default():
    body = build_request(pp_job(temperature=None), max_tokens=10)
    assert "temperature" not in body
    assert build_request(pp_job(temperature=0.0), max_tokens=10)["temperature"] == 0.0


def test_fake_client_answers_per_criterion_jobs_validly():
    client = FakeModelClient()
    job = pp_job()
    result = client.fetch_results(client.submit_batch([job]))
    (resp,) = result.responses
    assert len(parse_ratings(job, resp.text)) == 3
    assert resp.usage["output_tokens"] == 3 * 40
