"""Load the study's prompt templates and description paraphrases, and check their hash manifest.

Layout: `prompts/<call unit>/<wording>.txt` (call units `persona_policy` and `joint`),
`designs/inputs/description_paraphrases/<level>.yaml` (policy id -> definition text), and
`prompts/manifest.yaml` recording the sha256 of each file so an edit after freezing is caught.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from llm_panel.domain.study_prompt import PLACEHOLDERS, check_template


def load_templates(prompts_dir: Path | str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for unit_dir in sorted(p for p in Path(prompts_dir).iterdir() if p.is_dir()):
        if unit_dir.name not in PLACEHOLDERS:
            raise ValueError(f"unknown call unit {unit_dir.name!r} under {prompts_dir}")
        texts = {}
        for f in sorted(unit_dir.glob("*.txt")):
            text = f.read_text(encoding="utf-8")
            check_template(unit_dir.name, text)
            texts[f.stem] = text
        out[unit_dir.name] = texts
    return out


def load_description_paraphrases(
    directory: Path | str, policy_ids: tuple[str, ...]
) -> dict[str, dict[str, str]]:
    out = {}
    for f in sorted(Path(directory).glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        have, want = set(data), set(policy_ids)
        if have != want:
            raise ValueError(
                f"{f.name}: policy ids differ from the inputs: missing {sorted(want - have)}, "
                f"unexpected {sorted(have - want)}"
            )
        out[f.stem] = {pid: str(data[pid]).strip() for pid in policy_ids}
    return out


def file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest_mismatches(manifest_path: Path | str, root: Path | str) -> list[str]:
    """Paths whose current sha256 differs from the one recorded in the manifest."""
    manifest = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8"))
    return [
        e["path"]
        for e in manifest["files"]
        if not (Path(root) / e["path"]).is_file()
        or file_sha256(Path(root) / e["path"]) != e["sha256"]
    ]
