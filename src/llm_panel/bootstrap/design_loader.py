"""Read design.yaml into a domain Design."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_panel.domain.design import Design

REQUIRED_FACTORS = (
    "model",
    "persona_source",
    "paraphrase",
    "policy_blinding",
    "evidence_packet",
    "presentation_order",
    "score_aggregation",
)


def load_design(path: Path | str) -> Design:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    factors = data.get("factors") or {}
    missing = [f for f in REQUIRED_FACTORS if not factors.get(f)]
    if missing:
        raise ValueError(f"design file {path} is missing factors: {', '.join(missing)}")
    for model in factors["model"]:
        if not model.get("provider") or not model.get("snapshot"):
            raise ValueError("each model needs provider and snapshot (pinned, not an alias)")
    sampling = data.get("sampling") or {}
    return Design(
        models=tuple(dict(m) for m in factors["model"]),
        persona_source=tuple(factors["persona_source"]),
        paraphrase=tuple(factors["paraphrase"]),
        policy_blinding=tuple(factors["policy_blinding"]),
        evidence_packet=tuple(factors["evidence_packet"]),
        presentation_order=tuple(factors["presentation_order"]),
        score_aggregation=tuple(factors["score_aggregation"]),
        repeats=int(data.get("repeats", 1)),
        mode=data.get("mode", "full"),
        n_runs=data.get("n_runs"),
        seed=int(data.get("design_seed", 0)),
        temperature=float(sampling.get("temperature", 1.0)),
        base_seed=int(sampling.get("base_seed", 0)),
        prompt_format=data.get("prompt_format", "all_policies"),
    )
