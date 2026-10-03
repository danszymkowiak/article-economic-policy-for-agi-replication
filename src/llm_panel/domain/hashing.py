"""Content-addressed job ids so reruns skip finished jobs."""

from __future__ import annotations

import hashlib
import json


def job_id(prompt: str, model_snapshot: str, temperature: float, seed: int) -> str:
    """sha256 over an unambiguous (JSON, length-delimited) encoding of the four components."""
    blob = json.dumps(
        [prompt, model_snapshot, float(temperature), int(seed)],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
