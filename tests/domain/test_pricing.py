import pytest

from llm_panel.domain.pricing import (
    MissingPriceError,
    Price,
    SpendSettings,
    estimate_job_cost,
    usage_cost,
)
from tests.domain.test_models import make_job


def settings(**kw):
    base = dict(
        max_spend_usd=15,
        prices={"fake-1": Price(input_per_mtok=2.0, output_per_mtok=10.0)},
        est_output_tokens_per_policy=100,
        chars_per_token=4.0,
        batch_discount=1.0,
    )
    base.update(kw)
    return SpendSettings(**base)


def test_usage_cost():
    p = Price(2.0, 10.0)
    assert usage_cost({"input_tokens": 1_000_000, "output_tokens": 500_000}, p, 1.0) == 7.0
    assert usage_cost({"input_tokens": 1_000_000, "output_tokens": 500_000}, p, 0.5) == 3.5
    assert usage_cost({}, p, 1.0) == 0.0


def test_estimate_job_cost_uses_prompt_length_and_policy_count():
    job = make_job(prompt="x" * 400)  # 100 input tokens, 2 policies -> 200 output tokens
    expected = (100 * 2.0 + 200 * 10.0) / 1e6
    assert estimate_job_cost(job, settings()) == pytest.approx(expected)


def test_missing_price_refuses():
    with pytest.raises(MissingPriceError, match="fake-1"):
        estimate_job_cost(make_job(), settings(prices={}))


def test_discount_applies_to_estimates():
    job = make_job(prompt="x" * 400)
    full = estimate_job_cost(job, settings())
    assert estimate_job_cost(job, settings(batch_discount=0.5)) == pytest.approx(full / 2)
