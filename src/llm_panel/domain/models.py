"""Pure domain types. No I/O in this package."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields

from llm_panel.domain.hashing import job_id as _job_id

ORDERS = ("fixed", "reversed", "shuffled")
AGGREGATIONS = ("mean", "median", "trimmed_mean")
PROMPT_FORMATS = ("all_policies", "one_policy")


@dataclass(frozen=True)
class Persona:
    id: str
    source: str
    description: str


@dataclass(frozen=True)
class Policy:
    id: str
    name: str
    description: str
    blinded_description: str


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    description: str
    group: str = ""


@dataclass(frozen=True)
class RunSpec:
    """One cell of the study design (all factor levels fixed)."""

    provider: str
    model_snapshot: str
    persona_source: str
    paraphrase: str = "baseline"
    blinded: bool = False
    evidence: str = "reconstructed"
    order: str = "fixed"
    aggregation: str = "mean"
    repeats: int = 1
    temperature: float = 1.0
    base_seed: int = 0
    prompt_format: str = "all_policies"

    def __post_init__(self) -> None:
        if not self.model_snapshot:
            raise ValueError("model_snapshot must be a pinned snapshot id, not empty")
        if self.repeats < 1:
            raise ValueError("repeats must be >= 1")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be within [0, 2]")
        if self.order not in ORDERS:
            raise ValueError(f"order must be one of {ORDERS}")
        if self.aggregation not in AGGREGATIONS:
            raise ValueError(f"aggregation must be one of {AGGREGATIONS}")
        if self.prompt_format not in PROMPT_FORMATS:
            raise ValueError(f"prompt_format must be one of {PROMPT_FORMATS}")

    @property
    def spec_id(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]


@dataclass(frozen=True)
class RenderedJob:
    """A fully rendered request: one model call."""

    prompt: str
    provider: str
    model_snapshot: str
    temperature: float
    seed: int
    persona_id: str
    criterion_id: str
    policy_ids: tuple[str, ...]
    policy_labels: tuple[str, ...]
    spec_id: str
    repeat: int

    def __post_init__(self) -> None:
        if len(self.policy_ids) != len(self.policy_labels):
            raise ValueError("policy_ids and policy_labels must have the same length")

    @property
    def job_id(self) -> str:
        return _job_id(self.prompt, self.model_snapshot, self.temperature, self.seed)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RenderedJob:
        names = {f.name for f in fields(cls)}
        kw = {k: v for k, v in data.items() if k in names}
        kw["policy_ids"] = tuple(kw["policy_ids"])
        kw["policy_labels"] = tuple(kw["policy_labels"])
        return cls(**kw)


@dataclass(frozen=True)
class Rating:
    job_id: str
    persona_id: str
    criterion_id: str
    policy_id: str
    score: float
    rationale: str

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError("score must be within [0, 100]")
