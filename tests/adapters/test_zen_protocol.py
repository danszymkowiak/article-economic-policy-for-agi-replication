import pytest

from llm_panel.adapters.zen.protocol import build_request, is_retryable, parse_completion
from tests.domain.test_models import make_job


def test_build_request_carries_prompt_sampling_and_cap():
    job = make_job(prompt="rate these", temperature=0.7, seed=3)
    body = build_request(job, max_tokens=250)
    assert body["model"] == job.model_snapshot
    assert body["messages"] == [{"role": "user", "content": "rate these"}]
    assert body["temperature"] == 0.7
    assert body["seed"] == 3
    assert body["max_tokens"] == 250


def test_build_request_strips_opencode_prefix_from_model():
    job = make_job(model_snapshot="opencode/big-pickle")
    assert build_request(job, max_tokens=10)["model"] == "big-pickle"


def test_parse_completion_maps_text_usage_and_keeps_reported_model():
    payload = {
        "model": "big-pickle-2026-09",
        "choices": [{"message": {"content": '{"ratings": []}'}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 33},
    }
    resp = parse_completion("job1", 200, payload)
    assert resp.status == "ok" and resp.job_id == "job1"
    assert resp.text == '{"ratings": []}'
    assert resp.usage == {"input_tokens": 120, "output_tokens": 33}
    assert resp.raw["model"] == "big-pickle-2026-09"


def test_parse_completion_http_error_is_error_status():
    resp = parse_completion("job1", 401, {"error": {"message": "bad key"}})
    assert resp.status == "error" and "401" in resp.error and "bad key" in resp.error


@pytest.mark.parametrize(
    "payload",
    [{}, {"choices": []}, {"choices": [{"message": {"content": None}}]}, {"choices": [{}]}],
)
def test_parse_completion_without_text_is_error(payload):
    resp = parse_completion("job1", 200, payload)
    assert resp.status == "error" and resp.text == ""


def test_parse_completion_truncated_output_is_flagged():
    payload = {
        "model": "m",
        "choices": [{"message": {"content": '{"ratings": [{"po'}, "finish_reason": "length"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
    }
    resp = parse_completion("job1", 200, payload)
    assert resp.status == "ok" and resp.raw["finish_reason"] == "length"


@pytest.mark.parametrize(
    "code,expected",
    [(429, True), (500, True), (503, True), (400, False), (401, False), (404, False)],
)
def test_is_retryable(code, expected):
    assert is_retryable(code) is expected


def test_parse_completion_without_usage_reports_none_so_estimate_applies():
    payload = {"model": "m", "choices": [{"message": {"content": "{}"}}]}
    assert parse_completion("job1", 200, payload).usage == {}


def test_empty_text_error_still_reports_the_usage_the_provider_billed():
    # A reasoning model can burn the whole token cap and return no text; it is still billed.
    payload = {
        "model": "m",
        "choices": [{"message": {"content": ""}, "finish_reason": "length"}],
        "usage": {"prompt_tokens": 300, "completion_tokens": 1500},
    }
    resp = parse_completion("job1", 200, payload)
    assert resp.status == "error"
    assert resp.usage == {"input_tokens": 300, "output_tokens": 1500}


def test_parse_completion_keeps_cached_and_reasoning_tokens_from_real_zen_shape():
    # Shape observed in the live smoketest: both are subsets of prompt/completion tokens.
    payload = {
        "model": "glm-5.3-flash",
        "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": 312,
            "completion_tokens": 2323,
            "completion_tokens_details": {"reasoning_tokens": 2084},
            "prompt_tokens_details": {"cached_tokens": 182},
            "total_tokens": 2635,
        },
    }
    assert parse_completion("j", 200, payload).usage == {
        "input_tokens": 312,
        "output_tokens": 2323,
        "cached_input_tokens": 182,
        "reasoning_tokens": 2084,
    }


def test_parse_completion_omits_detail_fields_when_absent_or_empty():
    payload = {
        "choices": [{"message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "prompt_tokens_details": {}},
    }
    assert parse_completion("j", 200, payload).usage == {"input_tokens": 5, "output_tokens": 7}
