"""Minimal .env loader. Values go into the environment and are never printed or returned."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path


def load_dotenv(path: Path | str, environ: MutableMapping[str, str]) -> list[str]:
    """Set variables from `path` that are not already set; return the names it set."""
    path = Path(path)
    if not path.is_file():
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.removeprefix("export ").partition("=")
        name, value = name.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if name and name not in environ:
            environ[name] = value
            names.append(name)
    return names
