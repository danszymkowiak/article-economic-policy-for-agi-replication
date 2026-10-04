"""ADVERSARIAL ARM: edit size, packet edits, panel outcome and the greedy, bounded search. Pure.

Search (prereg s9 draft): depth 1 runs every catalogue entry alone. If any moves the target (the
policy ranked first in the search-panel baseline) to strictly last place on the primary
composite, the smallest of those wins and the search stops. Otherwise the entry with the largest
rank drop is kept and depth 2 runs it combined with every entry of another slot; again the
smallest success wins. The search also stops when no entry lowers the target, at the depth cap
or at the candidate cap. Every candidate run is returned, not only the winner: their number is
the multiple-comparisons denominator.

"Smallest" is the edit size, compared in order: number of perturbations; the largest number of
characters changed in any one rendered prompt (per perturbation, the changed span after stripping
the common prefix and suffix, which is exact for one contiguous edit and an upper bound otherwise;
summed over the perturbations of a combination); the number of prompts changed. Non-text
perturbations (temperature, persona drop) change no characters; the report shows each component
so a reader can weigh them differently. Ties go to catalogue order.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from adversarial.catalogue import Perturbation
from llm_panel.domain.analysis_baseline import average_ranks

RUNNING = "running"
FOUND = "found"
NO_IMPROVEMENT = "no improvement"
DEPTH_EXHAUSTED = "depth exhausted"
CANDIDATE_CAP = "candidate cap"
SECTION_MARK = "\n\n## "


def changed_span(a: str, b: str) -> int:
    n = min(len(a), len(b))
    p = 0
    while p < n and a[p] == b[p]:
        p += 1
    s = 0
    while s < n - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]:
        s += 1
    return max(len(a) - p - s, len(b) - p - s)


@dataclass(frozen=True, order=True)
class EditSize:
    n_edits: int
    max_prompt_chars: int  # largest changed span in one rendered prompt
    prompts_changed: int


def edit_size(base: Mapping[str, str], singles: Sequence[Mapping[str, str]]) -> EditSize:
    """Edit size of a combination of perturbations. `base` maps each prompt slot (persona x
    policy) to its baseline prompt, each of `singles` to the prompt with one of the perturbations
    alone. Each perturbation's changed span counts separately, so two small edits far apart add
    up rather than spanning the text between them."""
    totals = [sum(changed_span(text, single[slot]) for single in singles)
              for slot, text in base.items()]  # fmt: skip
    return EditSize(len(singles), max(totals, default=0), sum(1 for t in totals if t))


def edit_packet(text: str, op: str) -> str:
    """Edit a packet's excerpt sections (`## ` headings after the metadata header)."""
    if op not in ("drop_last", "drop_first", "reverse", "keep_first_half"):
        raise ValueError(f"unknown evidence operation {op!r}")
    if not text:
        return text
    head, *sections = text.rstrip().split(SECTION_MARK)
    if op == "drop_last":
        sections = sections[:-1]
    elif op == "drop_first":
        sections = sections[1:]
    elif op == "reverse":
        sections = sections[::-1]
    else:
        sections = sections[: -(-len(sections) // 2)]
    return SECTION_MARK.join([head, *sections])


@dataclass(frozen=True)
class Outcome:
    """Panel means of the primary composite on the search panel and their ranks (1 = highest,
    ties share their average rank)."""

    means: dict[str, float]
    ranks: dict[str, float]
    n_personas: int
    policy_order: tuple[str, ...]

    @property
    def n_policies(self) -> int:
        return len(self.means)

    def top(self) -> str:
        best = max(self.means.values())
        return next(p for p in self.policy_order if self.means[p] == best)


def panel_outcome(
    ratings: Iterable[tuple[str, str, str, float]],
    *,
    criteria: Sequence[str],
    policies: Sequence[str],
    drop_top_for: str | None = None,
) -> Outcome | None:
    """ratings: (persona, policy, criterion, score). A persona's composite is the mean of the
    composite's criteria when it rated all of them; the panel mean is the unweighted mean over
    personas. `drop_top_for` drops the persona with the highest composite for that policy (ties:
    the first persona id). None when a policy is left without any persona."""
    cells: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for persona, policy, criterion, score in ratings:
        if criterion in criteria and policy in policies:
            cells[(persona, policy)][criterion] = score
    composite = {
        key: sum(v[c] for c in criteria) / len(criteria)
        for key, v in cells.items()
        if all(c in v for c in criteria)
    }
    personas = sorted({n for n, _ in composite})
    if drop_top_for is not None:
        favour = {
            n: composite[(n, drop_top_for)] for n in personas if (n, drop_top_for) in composite
        }
        if favour:
            top = max(favour.values())
            personas.remove(next(n for n in personas if favour.get(n) == top))
    means = {}
    for policy in policies:
        values = [composite[(n, policy)] for n in personas if (n, policy) in composite]
        if not values:
            return None
        means[policy] = sum(values) / len(values)
    ranks = average_ranks([-means[p] for p in policies])
    return Outcome(means, dict(zip(policies, ranks, strict=True)), len(personas), tuple(policies))


@dataclass(frozen=True)
class Candidate:
    perturbations: tuple[Perturbation, ...]

    @property
    def key(self) -> str:
        return "+".join(p.id for p in self.perturbations)

    @property
    def depth(self) -> int:
        return len(self.perturbations)

    @property
    def slots(self) -> frozenset[str]:
        return frozenset(p.slot for p in self.perturbations)


def depth_one(catalogue: Sequence[Perturbation]) -> list[Candidate]:
    return [Candidate((p,)) for p in catalogue]


def extend(best: Candidate, catalogue: Sequence[Perturbation]) -> list[Candidate]:
    return [Candidate((*best.perturbations, p)) for p in catalogue if p.slot not in best.slots]


@dataclass(frozen=True)
class Tried:
    candidate: Candidate
    outcome: Outcome | None  # None: run but not evaluable (a policy without ratings)
    size: EditSize
    target_rank: float | None
    rank_drop: float | None  # target rank minus its baseline rank (positive = lower)
    top_to_bottom: bool


@dataclass(frozen=True)
class SearchState:
    status: str
    needed: tuple[Candidate, ...]  # candidates still to run at the current depth
    tried: tuple[Tried, ...]  # every candidate run so far, in search order
    path: tuple[str, ...]  # the candidate kept at each completed depth
    winner: Tried | None
    capped: int  # candidates the candidate cap left out


def _tried(c: Candidate, outcome, size: EditSize, target: str, base_rank: float) -> Tried:
    if outcome is None:
        return Tried(c, None, size, None, None, False)
    rank = outcome.ranks[target]
    return Tried(c, outcome, size, rank, rank - base_rank, rank == outcome.n_policies)


def search(
    catalogue: Sequence[Perturbation],
    outcomes: Mapping[str, Outcome | None],
    size_of: Callable[[Candidate], EditSize],
    *,
    target: str,
    base_rank: float,
    max_depth: int,
    max_candidates: int,
) -> SearchState:
    """Replay the greedy search over the outcomes known so far (keyed by candidate key; a missing
    key is a candidate not yet complete). Deterministic, so state lives in the store only."""
    left, capped, depth = max_candidates, 0, 1
    level = depth_one(catalogue)
    tried: list[Tried] = []
    path: list[str] = []

    def state(status, needed=(), winner=None):
        return SearchState(status, tuple(needed), tuple(tried), tuple(path), winner, capped)

    while True:
        truncated = len(level) > left
        if truncated:
            capped += len(level) - left
            level = level[:left]
        left -= len(level)
        order = {c.key: i for i, c in enumerate(level)}
        done = [_tried(c, outcomes[c.key], size_of(c), target, base_rank)
                for c in level if c.key in outcomes]  # fmt: skip
        tried.extend(done)
        missing = [c for c in level if c.key not in outcomes]
        if missing:
            return state(RUNNING, missing)
        rank = [t for t in done if t.outcome is not None]
        wins = [t for t in rank if t.top_to_bottom]
        if wins:
            return state(FOUND, winner=min(wins, key=lambda t: (t.size, order[t.candidate.key])))
        if truncated:
            return state(CANDIDATE_CAP)
        best = min(rank, key=lambda t: (-t.rank_drop, t.size, order[t.candidate.key]), default=None)
        if best is None or best.rank_drop <= 0:
            return state(NO_IMPROVEMENT)
        path.append(best.candidate.key)
        if depth >= max_depth:
            return state(DEPTH_EXHAUSTED)
        level = extend(best.candidate, catalogue)
        depth += 1
        if not level:
            return state(DEPTH_EXHAUSTED)
        if left == 0:
            capped += len(level)
            return state(CANDIDATE_CAP)
