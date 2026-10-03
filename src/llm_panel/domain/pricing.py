"""Cost estimation and spend settings. Pure."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from llm_panel.domain.models import RenderedJob

HARD_CEILING_USD = 15.0  # the study's absolute cap; config may lower it, never raise it


class MissingPriceError(ValueError):
    """No price is configured for a model snapshot, so its cost cannot be bounded."""


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float
    # Price of cached input tokens; None = charge them at the full input price (upper bound).
    input_cached_per_mtok: float | None = None


@dataclass(frozen=True)
class SpendSettings:
    max_spend_usd: float
    prices: Mapping[str, Price]  # keyed by pinned model snapshot
    est_output_tokens_per_policy: int = 100
    chars_per_token: float = 4.0
    batch_discount: float = 1.0  # multiplier on list price; 1.0 = assume no discount

    def __post_init__(self) -> None:
        # Guard against settings that would silently zero out estimates and defeat the ceiling.
        if not 0 < self.batch_discount <= 1:
            raise ValueError("batch_discount must be in (0, 1]")
        if self.chars_per_token <= 0:
            raise ValueError("chars_per_token must be > 0")
        if self.est_output_tokens_per_policy < 1:
            raise ValueError("est_output_tokens_per_policy must be >= 1")

    def price_for(self, snapshot: str) -> Price:
        try:
            return self.prices[snapshot]
        except KeyError:
            raise MissingPriceError(
                f"no price configured for model snapshot {snapshot!r}"
            ) from None


def usage_cost(usage: Mapping, price: Price, discount: float) -> float:
    """Cached input tokens are a subset of input tokens; reasoning tokens are a subset of output
    tokens (already billed at the output rate), so they are recorded but not charged again."""
    usage = usage or {}
    tokens_in = usage.get("input_tokens", 0) or 0
    tokens_out = usage.get("output_tokens", 0) or 0
    cached = min(usage.get("cached_input_tokens", 0) or 0, tokens_in)
    cached_rate = (
        price.input_per_mtok
        if price.input_cached_per_mtok is None
        else (price.input_cached_per_mtok)
    )
    total = (tokens_in - cached) * price.input_per_mtok + cached * cached_rate
    return (total + tokens_out * price.output_per_mtok) / 1e6 * discount


def estimated_usage(job: RenderedJob, settings: SpendSettings) -> dict:
    return {
        "input_tokens": math.ceil(len(job.prompt) / settings.chars_per_token),
        "output_tokens": settings.est_output_tokens_per_policy * len(job.policy_ids),
    }


def estimate_job_cost(job: RenderedJob, settings: SpendSettings) -> float:
    price = settings.price_for(job.model_snapshot)
    return usage_cost(estimated_usage(job, settings), price, settings.batch_discount)
