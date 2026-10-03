"""OpenCode Zen chat-completions request/response mapping. Pure: no I/O."""

from __future__ import annotations

from collections.abc import Mapping

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import ModelResponse

MODEL_PREFIX = "opencode/"


def build_request(job: RenderedJob, max_tokens: int) -> dict:
    model = job.model_snapshot.removeprefix(MODEL_PREFIX)
    return {
        "model": model,
        "messages": [{"role": "user", "content": job.prompt}],
        "temperature": job.temperature,
        "seed": job.seed,
        "max_tokens": max_tokens,
    }


def is_retryable(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _error_text(payload: Mapping) -> str:
    err = payload.get("error")
    if isinstance(err, Mapping):
        return str(err.get("message", ""))
    return str(err) if err else ""


def parse_completion(job_id: str, status_code: int, payload: Mapping) -> ModelResponse:
    if status_code != 200:
        detail = _error_text(payload)
        return ModelResponse(
            job_id, "error", "", raw=dict(payload), error=f"HTTP {status_code}: {detail}".strip()
        )
    choices = payload.get("choices") or []
    choice = choices[0] if choices else {}
    text = (choice.get("message") or {}).get("content")
    usage = payload.get("usage") or {}
    raw = {
        "model": payload.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "text": text,
        "usage": dict(usage),
    }
    # Report usage only when the provider gave both counts; otherwise leave it empty so the
    # spend code charges the estimate instead of treating the call as free.
    reported = (
        {"input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"]}
        if usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
        else {}
    )
    if reported:  # subsets of the counts above; recorded so cost covers them explicitly
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        if cached:
            reported["cached_input_tokens"] = cached
        if reasoning:
            reported["reasoning_tokens"] = reasoning
    if not text:
        return ModelResponse(
            job_id, "error", "", usage=reported, raw=raw, error="response had no text content"
        )
    return ModelResponse(job_id, "ok", text, usage=reported, raw=raw)
