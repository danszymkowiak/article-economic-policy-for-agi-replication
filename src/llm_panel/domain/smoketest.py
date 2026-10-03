"""Smoketest expectations: stated before a run, checked against the ratings it produced. Pure."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from llm_panel.domain.models import Rating


@dataclass(frozen=True)
class Greater:
    criterion: str
    better: str
    worse: str
    margin: float


@dataclass(frozen=True)
class Close:
    criterion: str
    a: str
    b: str
    tolerance: float


@dataclass(frozen=True)
class Expectations:
    min_ok_rate: float
    greater: tuple[Greater, ...] = ()
    close: tuple[Close, ...] = ()


@dataclass(frozen=True)
class Check:
    description: str
    passed: bool
    detail: str


def mean_scores(ratings: Sequence[Rating]) -> dict[tuple[str, str], float]:
    """Mean score per (criterion, policy), over personas and repeats."""
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in ratings:
        groups[(r.criterion_id, r.policy_id)].append(r.score)
    return {key: sum(v) / len(v) for key, v in groups.items()}


def evaluate(exp: Expectations, ratings: Sequence[Rating], ok: int, total: int) -> list[Check]:
    means = mean_scores(ratings)
    rate = ok / total if total else 0.0
    checks = [
        Check(
            f"ok rate >= {exp.min_ok_rate}",
            rate >= exp.min_ok_rate,
            f"{ok}/{total} jobs ok ({rate:.2f})",
        )
    ]

    def pair(criterion: str, x: str, y: str):
        return means.get((criterion, x)), means.get((criterion, y))

    for g in exp.greater:
        desc = f"{g.better} beats {g.worse} on {g.criterion} by >= {g.margin:g}"
        hi, lo = pair(g.criterion, g.better, g.worse)
        if hi is None or lo is None:
            checks.append(Check(desc, False, "no scores for one of the policies"))
        else:
            checks.append(
                Check(desc, hi - lo >= g.margin, f"{hi:.1f} vs {lo:.1f}, gap {hi - lo:.1f}")
            )
    for c in exp.close:
        desc = f"{c.a} close to {c.b} on {c.criterion} (within {c.tolerance:g})"
        a, b = pair(c.criterion, c.a, c.b)
        if a is None or b is None:
            checks.append(Check(desc, False, "no scores for one of the policies"))
        else:
            checks.append(
                Check(desc, abs(a - b) <= c.tolerance, f"{a:.1f} vs {b:.1f}, gap {abs(a - b):.1f}")
            )
    return checks
