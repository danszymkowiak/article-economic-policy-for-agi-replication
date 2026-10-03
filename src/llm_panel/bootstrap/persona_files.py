"""Write a built persona panel (with provenance) to <inputs_dir>/personas/<source>.yaml."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import yaml

from llm_panel.domain.personas import PersonaPanel


def write_panel(inputs_dir: Path | str, panel: PersonaPanel) -> Path:
    path = Path(inputs_dir) / "personas" / f"{panel.provenance['source']}.yaml"
    if path.exists():
        raise FileExistsError(f"{path} exists; personas are never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "provenance": panel.provenance,
        "personas": [
            {"id": p.id, "description": p.description, "traits": t}
            for p, t in zip(panel.personas, panel.traits, strict=True)
        ],
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), "utf-8")
    return path


def read_records(path: Path | str) -> tuple[list[dict], str]:
    """Anonymous respondent records from a CSV file, plus the file's sha256."""
    raw = Path(path).read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    return rows, hashlib.sha256(raw).hexdigest()
