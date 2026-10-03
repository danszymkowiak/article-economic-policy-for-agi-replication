"""Load personas, policies, criteria and evidence packets from an inputs directory."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_panel.application.build_jobs import StudyInputs
from llm_panel.domain.models import Criterion, Persona, Policy


def _yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def _persona_entries(data) -> list:
    """A persona file is a plain list, or a mapping with `provenance` and `personas`."""
    return data["personas"] if isinstance(data, dict) else data


def load_provenance(inputs_dir: Path | str) -> dict[str, dict]:
    """Provenance record per persona source; sources stored as plain lists have none."""
    out = {}
    for f in sorted((Path(inputs_dir) / "personas").glob("*.yaml")):
        data = _yaml(f)
        if isinstance(data, dict) and "provenance" in data:
            out[f.stem] = data["provenance"]
    return out


def load_inputs(inputs_dir: Path | str) -> StudyInputs:
    root = Path(inputs_dir)
    personas = {
        f.stem: tuple(
            Persona(id=p["id"], source=f.stem, description=p["description"])
            for p in _persona_entries(_yaml(f))
        )
        for f in sorted((root / "personas").glob("*.yaml"))
    }
    evidence = {
        f.stem: f.read_text(encoding="utf-8").strip()
        for f in sorted((root / "evidence").glob("*.txt"))
    }
    return StudyInputs(
        personas=personas,
        policies=tuple(Policy(**p) for p in _yaml(root / "policies.yaml")),
        criteria=tuple(Criterion(**c) for c in _yaml(root / "criteria.yaml")),
        evidence=evidence,
    )
