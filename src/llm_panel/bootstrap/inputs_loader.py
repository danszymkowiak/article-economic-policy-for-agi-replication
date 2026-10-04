"""Load personas, policies, criteria and evidence from an inputs directory, and the study's
per-policy evidence packets, templates and paraphrases (one-at-a-time design)."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_panel.application.build_jobs import StudyInputs
from llm_panel.bootstrap.config import Config
from llm_panel.bootstrap.prompt_files import load_description_paraphrases, load_templates
from llm_panel.domain.models import Criterion, Persona, Policy
from llm_panel.domain.study_jobs import StudyMaterials


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


def load_packets(directory: Path | str, policy_ids: tuple[str, ...]) -> dict[str, str]:
    """One packet per policy, `<policy id>.md`, read whole (header and attribution included)."""
    packets = {
        f.stem: f.read_text(encoding="utf-8").strip() for f in sorted(Path(directory).glob("*.md"))
    }
    have, want = set(packets), set(policy_ids)
    if have != want:
        raise ValueError(
            f"evidence packets in {directory} differ from the policies: missing "
            f"{sorted(want - have)}, unexpected {sorted(have - want)}"
        )
    return {pid: packets[pid] for pid in policy_ids}


def load_study_materials(config: Config) -> StudyMaterials:
    inputs = load_inputs(config.inputs_dir)
    ids = tuple(p.id for p in inputs.policies)
    paraphrases = config.inputs_dir / "description_paraphrases"
    return StudyMaterials(
        panels=inputs.personas,
        policies=inputs.policies,
        criteria=inputs.criteria,
        packets={lv: load_packets(d, ids) for lv, d in config.evidence_packets.items()},
        templates=load_templates(config.prompts_dir),
        description_paraphrases=(
            load_description_paraphrases(paraphrases, ids) if paraphrases.is_dir() else {}
        ),
    )
