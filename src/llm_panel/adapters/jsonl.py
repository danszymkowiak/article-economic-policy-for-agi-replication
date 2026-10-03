"""Append-only JSONL adapters for the result store and the batch ledger."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

from llm_panel.domain.results import StoredRow


class _AppendOnlyJsonl:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        if self._path.exists() and self._path.stat().st_size:
            with self._path.open("rb") as fh:
                fh.seek(-1, os.SEEK_END)
                if fh.read(1) != b"\n":  # torn write: keep our record on its own line
                    line = "\n" + line
        # "a" mode opens with O_APPEND; one write call per line keeps lines intact.
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

    def _iter(self) -> Iterator[dict]:
        if not self._path.exists():
            return
        with self._path.open(encoding="utf-8") as fh:
            for n, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"corrupt record at {self._path} line {n}") from exc


class JsonlResultStore(_AppendOnlyJsonl):
    """Raw result store. Offers append, exists and iter_rows only: no update or delete."""

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        self._terminal: set[str] | None = None

    def append(self, row: StoredRow) -> None:
        self._append(row.to_dict())
        if self._terminal is not None and row.is_terminal:
            self._terminal.add(row.job_id)

    def exists(self, job_id: str) -> bool:
        if self._terminal is None:
            self._terminal = {r.job_id for r in self.iter_rows() if r.is_terminal}
        return job_id in self._terminal

    def iter_rows(self) -> Iterator[StoredRow]:
        for record in self._iter():
            yield StoredRow.from_dict(record)


class JsonlBatchLedger(_AppendOnlyJsonl):
    def record(self, entry: dict) -> None:
        self._append(entry)

    def entries(self) -> list[dict]:
        return list(self._iter())
