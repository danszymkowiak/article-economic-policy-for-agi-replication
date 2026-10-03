"""Result-side domain types shared by ports and adapters. No I/O."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields

MAX_ATTEMPTS = 2  # first try plus one retry for malformed responses

STATUS_OK = "ok"
STATUS_INVALID = "invalid"  # malformed or provider error; retryable until MAX_ATTEMPTS
STATUS_FAILED = "failed"  # terminal failure


@dataclass(frozen=True)
class ModelResponse:
    """What a ModelClient hands back for one job. `raw` keeps the full provider payload."""

    job_id: str
    status: str  # "ok" or "error" at the transport level
    text: str
    usage: dict = field(default_factory=dict)  # at least input_tokens / output_tokens
    raw: dict = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class BatchResult:
    done: bool
    responses: tuple[ModelResponse, ...] = ()


@dataclass(frozen=True)
class StoredRow:
    """One line of the append-only raw store."""

    job_id: str
    status: str
    attempt: int
    provider: str
    model_snapshot: str
    temperature: float
    seed: int
    timestamp: str
    request: dict
    response: dict | None
    usage: dict
    batch_id: str
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        return (
            self.status == STATUS_OK
            or self.status == STATUS_FAILED
            or (self.attempt >= MAX_ATTEMPTS)
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StoredRow:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})
