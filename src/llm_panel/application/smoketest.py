"""Rebuild ratings from the raw store for the smoketest check. Reads only ok rows as ratings."""

from __future__ import annotations

from llm_panel.domain.models import Rating, RenderedJob
from llm_panel.domain.results import STATUS_FAILED, STATUS_INVALID, STATUS_OK
from llm_panel.domain.validation import InvalidResponse, parse_ratings
from llm_panel.ports import ResultStore


def ratings_from_store(store: ResultStore) -> tuple[list[Rating], int, int]:
    """Return (ratings, jobs that ended ok, jobs that produced an outcome).

    A job awaiting its retry counts as not ok. Deferred and duplicate rows are not outcomes.
    """
    ok_jobs: set[str] = set()
    attempted_jobs: set[str] = set()
    ratings: list[Rating] = []
    for row in store.iter_rows():
        if row.status in (STATUS_OK, STATUS_INVALID, STATUS_FAILED):
            attempted_jobs.add(row.job_id)
        if row.status != STATUS_OK or row.job_id in ok_jobs:
            continue
        job = RenderedJob.from_dict(row.request)
        try:
            ratings.extend(parse_ratings(job, (row.response or {}).get("text") or ""))
        except InvalidResponse:
            continue  # stored as ok but no longer parses: count it as not ok
        ok_jobs.add(row.job_id)
    return ratings, len(ok_jobs), len(attempted_jobs)
