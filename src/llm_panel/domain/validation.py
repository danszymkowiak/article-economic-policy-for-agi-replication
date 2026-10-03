"""Validate a raw model response against the schema and the job it answers. Pure."""

from __future__ import annotations

import json
import re

import jsonschema

from llm_panel.domain.models import Rating, RenderedJob
from llm_panel.domain.schema import RESPONSE_SCHEMA

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


class InvalidResponse(ValueError):
    pass


def parse_ratings(job: RenderedJob, text: str) -> list[Rating]:
    match = _FENCE.match(text)
    body = match.group(1) if match else text
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidResponse(f"not valid JSON: {exc}") from exc
    try:
        jsonschema.validate(payload, RESPONSE_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise InvalidResponse(f"schema violation: {exc.message}") from exc

    label_to_policy = dict(zip(job.policy_labels, job.policy_ids, strict=True))
    seen: set[str] = set()
    ratings = []
    for item in payload["ratings"]:
        label = item["policy"]
        if label not in label_to_policy:
            raise InvalidResponse(f"unknown policy label {label!r}")
        if label in seen:
            raise InvalidResponse(f"duplicate policy label {label!r}")
        seen.add(label)
        ratings.append(
            Rating(
                job_id=job.job_id,
                persona_id=job.persona_id,
                criterion_id=job.criterion_id,
                policy_id=label_to_policy[label],
                score=item["score"],
                rationale=item["rationale"],
            )
        )
    if seen != set(label_to_policy):
        raise InvalidResponse(f"missing labels: {sorted(set(label_to_policy) - seen)}")
    return ratings
