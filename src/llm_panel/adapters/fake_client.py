"""Deterministic in-memory ModelClient for tests and dry runs. Spends no money."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Collection, Sequence
from pathlib import Path

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import BatchResult, ModelResponse

OUTPUT_TOKENS_PER_POLICY = 40


def fake_score(job_id: str, label: str) -> int:
    digest = hashlib.sha256(f"{job_id}|{label}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % 101


class FakeModelClient:
    def __init__(
        self,
        provider: str = "fake",
        *,
        malformed: Collection[str] = (),
        errors: Collection[str] = (),
        malformed_attempts: int = 1,
        pending_polls: int = 0,
        state_path: Path | str | None = None,
        scorer: Callable[[str, str], int] = fake_score,
    ) -> None:
        """`malformed`/`errors` are job ids that misbehave for their first
        `malformed_attempts` submissions; `pending_polls` makes fetch_results report
        not-done that many times per batch. `state_path` persists submitted batches to a JSON
        file so separate CLI invocations (submit, then collect) can share one fake provider.
        `scorer(job_id, label)` returns the score for a label; the default is a hash, a custom one
        lets a test plant a known ground truth."""
        self.provider = provider
        self._scorer = scorer
        self._malformed = set(malformed)
        self._errors = set(errors)
        self._malformed_attempts = malformed_attempts
        self._pending_polls = pending_polls
        self._batches: dict[str, tuple[RenderedJob, ...]] = {}
        self._polls: dict[str, int] = {}
        self._submissions: dict[str, int] = {}
        self.submitted_batches: list[str] = []
        self._state_path = Path(state_path) if state_path else None
        if self._state_path and self._state_path.exists():
            stored = json.loads(self._state_path.read_text())
            self._batches = {
                k: tuple(RenderedJob.from_dict(j) for j in v) for k, v in stored.items()
            }
            self._polls = dict.fromkeys(self._batches, 0)

    def submit_batch(self, jobs: Sequence[RenderedJob]) -> str:
        batch_id = f"fake-batch-{len(self._batches) + 1}"
        self._batches[batch_id] = tuple(jobs)
        self._polls[batch_id] = 0
        for job in jobs:
            self._submissions[job.job_id] = self._submissions.get(job.job_id, 0) + 1
        self.submitted_batches.append(batch_id)
        if self._state_path:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            dump = {k: [j.to_dict() for j in v] for k, v in self._batches.items()}
            self._state_path.write_text(json.dumps(dump))
        return batch_id

    def fetch_results(self, batch_id: str) -> BatchResult:
        if batch_id not in self._batches:
            raise KeyError(f"unknown batch {batch_id}")
        self._polls[batch_id] += 1
        if self._polls[batch_id] <= self._pending_polls:
            return BatchResult(done=False)
        return BatchResult(
            done=True, responses=tuple(self._respond(j) for j in self._batches[batch_id])
        )

    def _respond(self, job: RenderedJob) -> ModelResponse:
        jid = job.job_id
        usage = {
            "input_tokens": -(-len(job.prompt) // 4),
            "output_tokens": OUTPUT_TOKENS_PER_POLICY * job.n_ratings,
        }
        misbehave = self._submissions.get(jid, 1) <= self._malformed_attempts
        if jid in self._errors and misbehave:
            return ModelResponse(
                jid, "error", "", usage={}, raw={"error": "fake"}, error="fake error"
            )
        if jid in self._malformed and misbehave:
            text = "this is not json"
        else:
            # per-criterion jobs answer one entry per criterion id, others one per policy label
            key = "criterion" if job.criterion_ids else "policy"
            ratings = [
                {
                    key: label,
                    "score": self._scorer(jid, label),
                    "rationale": f"fake rationale for {label}",
                }
                for label in (job.criterion_ids or job.policy_labels)
            ]
            text = json.dumps({"ratings": ratings})
        return ModelResponse(
            jid, "ok", text, usage=usage, raw={"fake": True, "text": text, "usage": usage}
        )
