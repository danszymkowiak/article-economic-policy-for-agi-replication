"""Process-level exclusive lock so overlapping cron runs cannot both pass the spend check."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class LockHeld(RuntimeError):
    pass


@contextmanager
def exclusive_lock(path: Path | str) -> Iterator[None]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(f"another llm-panel run holds {path}") from None
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
