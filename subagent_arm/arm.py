"""CLAUDE SUBAGENT ARM (prereg s9a; TASK-35): not pooled with the main analysis.

The baseline B repeated on Claude Haiku 4.5 run as Claude Code subagents, one fresh agent per
persona x policy call. This module is the functional core: build the jobs (the main arm's exact B
prompts on the Claude model), write one task file per job, tell the driver what to run next, and
fold the agents' answer files into the arm's own append-only store (schema check, one retry,
discards for tool use). The agents themselves are launched by the Claude Code session, not here.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.oat_design import Cell, Factors, ModelRef
from llm_panel.domain.results import (
    MAX_ATTEMPTS,
    STATUS_FAILED,
    STATUS_INVALID,
    STATUS_OK,
    StoredRow,
)
from llm_panel.domain.study_jobs import StudyMaterials, jobs_for_cell_repeat
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import ResultStore

PROVIDER = "claude-code"
SNAPSHOT = "claude-haiku-4-5"  # alias of claude-haiku-4-5-20251001; the snapshot is not reported
CELL_ID = "B"  # the arm's own store holds the baseline cell only
EXPECTED_TOOL_USES = 2  # Read the task file, Write the answer file; anything else is a discard
BATCH_ID = "subagent"


@dataclass(frozen=True)
class Workspace:
    """Where tasks, answers and discards live (subagent_arm/work/)."""

    root: Path

    def task_path(self, job_id: str) -> Path:
        return self.root / "tasks" / f"{job_id}.txt"

    def answer_path(self, job_id: str, attempt: int) -> Path:
        return self.root / "answers" / f"{job_id}.a{attempt}.json"

    @property
    def discards_path(self) -> Path:
        return self.root / "discards.txt"

    def discard(self, job_id: str, attempt: int) -> None:
        """Record that the agent for this attempt used tools beyond the one Read and one Write."""
        self.root.mkdir(parents=True, exist_ok=True)
        with self.discards_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{job_id} {attempt}\n")

    def discarded(self) -> set[tuple[str, int]]:
        if not self.discards_path.exists():
            return set()
        pairs = (ln.split() for ln in self.discards_path.read_text().splitlines() if ln.strip())
        return {(job, int(attempt)) for job, attempt in pairs}


def build_jobs(materials: StudyMaterials, baseline: Factors, k_c: int) -> list[RenderedJob]:
    """B's prompts on the Claude model: k_c repeats, repeat r carries seed r (not controllable
    on the model; it only keeps repeats' job ids apart)."""
    factors = replace(baseline, model=ModelRef(PROVIDER, SNAPSHOT), temperature=None)
    cell = Cell(CELL_ID, "R", CELL_ID, factors, tuple(range(k_c)))
    return [j for r in range(k_c) for j in jobs_for_cell_repeat(cell, r, materials)]


def write_tasks(ws: Workspace, jobs: Sequence[RenderedJob]) -> None:
    """One file per job holding exactly the rendered prompt; existing files are left alone."""
    (ws.root / "tasks").mkdir(parents=True, exist_ok=True)
    for job in jobs:
        path = ws.task_path(job.job_id)
        if not path.exists():
            path.write_text(job.prompt, encoding="utf-8")


def agent_prompt(ws: Workspace, job: RenderedJob, attempt: int) -> str:
    """The whole prompt the driver gives a subagent: where to read and where to write, nothing
    about the job itself."""
    return (
        f"Read the file {ws.task_path(job.job_id)}. It is a self-contained task: do exactly what "
        "it says. Then write your reply, the JSON object only and nothing else, to the file "
        f"{ws.answer_path(job.job_id, attempt)} using the Write tool. Do not read any other file, "
        "do not run commands, do not search, and do not use any other tool. When the file is "
        "written, reply with the single word: done"
    )


def _rows_by_job(store: ResultStore) -> dict[str, StoredRow]:
    latest: dict[str, StoredRow] = {}
    for row in store.iter_rows():
        if row.job_id not in latest or row.attempt >= latest[row.job_id].attempt:
            latest[row.job_id] = row
    return latest


def _next_attempt(row: StoredRow | None) -> int | None:
    if row is None:
        return 1
    return None if row.is_terminal else row.attempt + 1


def pending(store: ResultStore, jobs: Sequence[RenderedJob]) -> list[tuple[RenderedJob, int]]:
    """Jobs that still need an agent, with the attempt number it should write."""
    rows = _rows_by_job(store)
    out = []
    for job in jobs:
        attempt = _next_attempt(rows.get(job.job_id))
        if attempt is not None:
            out.append((job, attempt))
    return out


@dataclass(frozen=True)
class IngestResult:
    ok: int
    invalid: int  # retryable: a second attempt is pending
    failed: int  # terminal failures
    waiting: int  # no answer file yet


def _row(job, attempt, status, now, *, text=None, error=None) -> StoredRow:
    return StoredRow(
        job_id=job.job_id, status=status, attempt=attempt, provider=PROVIDER,
        model_snapshot=SNAPSHOT, temperature=None, seed=job.seed, timestamp=now(),
        request=job.to_dict(), response=None if text is None else {"text": text}, usage={},
        batch_id=f"{BATCH_ID}-{attempt}", error=error,
    )  # fmt: skip


def ingest(
    store: ResultStore, ws: Workspace, jobs: Sequence[RenderedJob], now: Callable[[], str]
) -> IngestResult:
    """Fold finished answer files into the store. A discarded or malformed answer is an invalid
    row (retryable once); a second one is a terminal failure."""
    discarded = ws.discarded()
    counts = {"ok": 0, "invalid": 0, "failed": 0, "waiting": 0}
    for job, attempt in pending(store, jobs):
        path = ws.answer_path(job.job_id, attempt)
        if (job.job_id, attempt) in discarded:
            text, error = None, "discarded: the agent used tools beyond one Read and one Write"
        elif path.exists():
            text, error = path.read_text(encoding="utf-8"), None
            try:
                parse_ratings(job, text)
            except InvalidResponse as exc:
                error = str(exc)
        else:
            counts["waiting"] += 1
            continue
        if error is None:
            store.append(_row(job, attempt, STATUS_OK, now, text=text))
            counts["ok"] += 1
            continue
        terminal = attempt >= MAX_ATTEMPTS
        status = STATUS_FAILED if terminal else STATUS_INVALID
        kept = None if error.startswith("discarded") else text
        store.append(_row(job, attempt, status, now, text=kept, error=error))
        counts["failed" if terminal else "invalid"] += 1
    return IngestResult(**counts)
