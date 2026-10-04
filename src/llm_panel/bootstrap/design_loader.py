"""Read design files into domain designs: the fractional `Design` (smoketests) and the
one-at-a-time `OatDesign` (the study, prereg section 5)."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_panel.domain.design import Design
from llm_panel.domain.oat_design import D2_REPEATS, DSettings, Factors, ModelRef, OatDesign

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


OAT_REQUIRED = ("baseline", "k_r", "k_q", "rt_temperatures", "order_seed")
BASELINE_KEYS = ("model", "persona_source", "evidence")
D_KEYS = {"persona_source", "model"}  # repeats are k_q for every D cell (prereg s8)


def _model(data: dict) -> ModelRef:
    return ModelRef(provider=data.get("provider", ""), snapshot=data.get("snapshot", ""))


def load_oat_design(path: Path | str) -> OatDesign:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if data.get("design") != "one_at_a_time":
        raise ValueError(f"design file {path} must declare design: one_at_a_time")
    missing = [k for k in OAT_REQUIRED if data.get(k) is None]
    base = data.get("baseline") or {}
    missing += [f"baseline.{k}" for k in BASELINE_KEYS if base and not base.get(k)]
    if missing:
        raise ValueError(f"design file {path} is missing: {', '.join(missing)}")
    if "k_rt" in data:
        raise ValueError(f"design file {path}: k_rt is not allowed; R-T cells get k_q repeats")
    temperature = base.get("temperature")  # absent or null = provider default
    d_cells = {}
    for name, d in (data.get("d_cells") or {}).items():
        unknown = set(d) - D_KEYS
        if unknown:
            raise ValueError(
                f"d_cells.{name}: unknown keys {', '.join(sorted(unknown))}"
                " (repeats are k_q for every D cell)"
            )
        d_cells[name] = DSettings(
            persona_source=d.get("persona_source"),
            model=_model(d["model"]) if d.get("model") else None,
        )
    return OatDesign(
        baseline=Factors(
            model=_model(base["model"]),
            temperature=None if temperature is None else float(temperature),
            persona_source=base["persona_source"],
            evidence=base["evidence"],
        ),
        k_r=int(data["k_r"]),
        k_q=int(data["k_q"]),
        d2_repeats=int(data.get("d2_repeats", D2_REPEATS)),
        rt_temperatures=tuple(float(t) for t in data["rt_temperatures"]),
        d_cells=d_cells,
        base_seed=int(data.get("base_seed", 0)),
        order_seed=int(data["order_seed"]),
        n_personas=int(data.get("n_personas", 51)),
    )
