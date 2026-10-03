"""Study-design expansion: factor levels -> RunSpecs. Pure."""

from __future__ import annotations

import itertools
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from llm_panel.domain.models import RunSpec

CANDIDATE_CAP = 2000  # per greedy step when the full grid is large


def expand_full(factors: Mapping[str, Sequence]) -> list[dict]:
    names = list(factors)
    return [
        dict(zip(names, combo, strict=True))
        for combo in itertools.product(*(factors[n] for n in names))
    ]


def expand_fractional(factors: Mapping[str, Sequence], n_runs: int, seed: int) -> list[dict]:
    """Seeded, balanced subset of the full grid.

    Greedily adds the candidate row that keeps each factor's levels (heavily weighted) and each
    pair of factors' level combinations as evenly used as possible. Main effects are exactly
    balanced when n_runs is a multiple of every factor's level count, and within one otherwise.
    This is an approximate orthogonal array, not a generator-based regular fraction.
    """
    if n_runs < 1:
        raise ValueError("n_runs must be >= 1")
    names = list(factors)
    grid_size = 1
    for n in names:
        grid_size *= len(factors[n])
    if n_runs >= grid_size:
        return expand_full(factors)

    rng = random.Random(seed)
    pairs = list(itertools.combinations(names, 2))
    singles: Counter = Counter()
    doubles: Counter = Counter()
    chosen: list[dict] = []
    chosen_keys: set[tuple] = set()

    def key(row: dict) -> tuple:
        return tuple(row[n] for n in names)

    def cost(row: dict) -> int:
        s = sum(singles[(n, row[n])] for n in names)
        d = sum(doubles[(f, row[f], g, row[g])] for f, g in pairs)
        return 1000 * s + d

    if grid_size <= CANDIDATE_CAP * 10:
        pool = expand_full(factors)
        rng.shuffle(pool)
    else:
        pool = None

    for _ in range(n_runs):
        if pool is not None:
            candidates = [r for r in pool if key(r) not in chosen_keys]
        else:
            candidates = []
            while len(candidates) < CANDIDATE_CAP:
                r = {n: rng.choice(list(factors[n])) for n in names}
                if key(r) not in chosen_keys:
                    candidates.append(r)
        best = min(candidates, key=cost)  # min is stable: ties go to shuffled order
        chosen.append(best)
        chosen_keys.add(key(best))
        for n in names:
            singles[(n, best[n])] += 1
        for f, g in pairs:
            doubles[(f, best[f], g, best[g])] += 1
    return chosen


@dataclass(frozen=True)
class Design:
    models: tuple[Mapping, ...]  # each {provider, snapshot, [temperature]}
    persona_source: tuple[str, ...]
    paraphrase: tuple[str, ...]
    policy_blinding: tuple[str, ...]  # "named" | "blinded"
    evidence_packet: tuple[str, ...]
    presentation_order: tuple[str, ...]
    score_aggregation: tuple[str, ...]
    repeats: int = 1
    mode: str = "full"
    n_runs: int | None = None
    seed: int = 0
    temperature: float = 1.0
    base_seed: int = 0
    prompt_format: str = "all_policies"


def to_run_specs(design: Design) -> list[RunSpec]:
    factors = {
        "model": tuple(range(len(design.models))),  # index keeps rows hashable and ordered
        "persona_source": design.persona_source,
        "paraphrase": design.paraphrase,
        "policy_blinding": design.policy_blinding,
        "evidence_packet": design.evidence_packet,
        "presentation_order": design.presentation_order,
        "score_aggregation": design.score_aggregation,
    }
    if design.mode == "full":
        rows = expand_full(factors)
    elif design.mode == "fractional":
        if not design.n_runs:
            raise ValueError("fractional mode requires n_runs")
        rows = expand_fractional(factors, design.n_runs, design.seed)
    else:
        raise ValueError(f"unknown design mode {design.mode!r}")

    specs = []
    for row in rows:
        model = design.models[row["model"]]
        specs.append(
            RunSpec(
                provider=model["provider"],
                model_snapshot=model["snapshot"],
                persona_source=row["persona_source"],
                paraphrase=row["paraphrase"],
                blinded=row["policy_blinding"] == "blinded",
                evidence=row["evidence_packet"],
                order=row["presentation_order"],
                aggregation=row["score_aggregation"],
                repeats=design.repeats,
                temperature=model.get("temperature", design.temperature),
                base_seed=design.base_seed,
                prompt_format=design.prompt_format,
            )
        )
    return specs
