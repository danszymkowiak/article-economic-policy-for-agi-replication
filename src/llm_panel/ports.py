"""Ports: the interfaces the application depends on. Adapters implement them."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, runtime_checkable

from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import BatchResult, StoredRow


class ProviderConfigError(RuntimeError):
    """A provider cannot be used as configured (missing key, unknown provider, ...).

    Adapters raise subclasses of this; the CLI reports it as a guarded refusal, so a new adapter
    never needs to be named in core code.
    """


@runtime_checkable
class ModelClient(Protocol):
    provider: str

    def submit_batch(self, jobs: Sequence[RenderedJob]) -> str:
        """Submit jobs as one batch and return a provider batch id."""
        ...

    def fetch_results(self, batch_id: str) -> BatchResult:
        """Return the batch state; `done` is False while it is still running."""
        ...


@runtime_checkable
class ResultStore(Protocol):
    """Append-only. There is deliberately no update or delete."""

    def append(self, row: StoredRow) -> None: ...

    def exists(self, job_id: str) -> bool:
        """True if a terminal row (ok, or failed after retries) exists for this job."""
        ...

    def iter_rows(self) -> Iterator[StoredRow]: ...


@runtime_checkable
class BatchLedger(Protocol):
    """Append-only record of submitted batches (the raw store holds results only)."""

    def record(self, entry: dict) -> None: ...

    def entries(self) -> list[dict]: ...
