"""Read a smoketest expectations file."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_panel.domain.smoketest import Close, Expectations, Greater


def load_expectations(path: Path | str) -> Expectations:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if "min_ok_rate" not in data:
        raise ValueError(f"{path} must set min_ok_rate")
    return Expectations(
        min_ok_rate=float(data["min_ok_rate"]),
        greater=tuple(Greater(**g) for g in data.get("greater") or ()),
        close=tuple(Close(**c) for c in data.get("close") or ()),
    )
