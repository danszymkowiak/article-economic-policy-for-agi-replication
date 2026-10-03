"""Check that the model id a provider reports matches the one requested. Pure.

Some providers serve aliases, so the response-reported id is the only evidence of
what actually ran. A reported id that differs from the requested one, or changes during the study,
means rows may not be comparable.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from llm_panel.domain.results import StoredRow


@dataclass(frozen=True)
class ModelIdReport:
    checked: int = 0  # rows that reported a model id
    unreported: int = 0  # rows with no reported id (errors, fake client)
    mismatched: dict[str, dict[str, int]] = field(default_factory=dict)  # requested -> id -> rows
    reported_ids: dict[str, list[str]] = field(default_factory=dict)  # requested -> ids, first seen

    @property
    def has_issues(self) -> bool:
        return bool(self.mismatched) or any(len(ids) > 1 for ids in self.reported_ids.values())

    def describe(self) -> str:
        parts = [
            f"{requested!r} reported as {', '.join(repr(i) for i in ids)}"
            for requested, ids in self.reported_ids.items()
            if len(ids) > 1 or requested in self.mismatched
        ]
        return "; ".join(parts)


def _bare(model: str) -> str:
    return model.split("/", 1)[-1]  # drop a provider prefix such as "vendor/"


def check_model_ids(rows: Iterable[StoredRow]) -> ModelIdReport:
    checked = unreported = 0
    mismatched: dict[str, dict[str, int]] = {}
    seen: dict[str, dict[str, str]] = {}  # requested -> {reported id: first timestamp}
    for row in rows:
        reported = (row.response or {}).get("model")
        if not reported:
            unreported += 1
            continue
        checked += 1
        first = seen.setdefault(row.model_snapshot, {})
        first[reported] = min(first.get(reported, row.timestamp), row.timestamp)
        if reported != _bare(row.model_snapshot):
            counts = mismatched.setdefault(row.model_snapshot, {})
            counts[reported] = counts.get(reported, 0) + 1
    ids = {req: sorted(m, key=m.__getitem__) for req, m in seen.items()}
    return ModelIdReport(checked, unreported, mismatched, ids)
