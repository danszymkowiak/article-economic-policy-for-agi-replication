"""One-at-a-time study design (prereg sections 5 and 8): cells, run order, budget plan. Pure.

Baseline B plus variations that each change exactly one factor:
- block R (noise floor): B repeated k_R times; R-T, B at temperature 0 and one higher level;
  B', one more B repeat at the very end as a provider-drift control;
- block Q (small variations, k_Q repeats each): Q1 description-only, Q2a-c description
  paraphrases, Q3a-c instruction paraphrases, Q4 no evidence packet;
- block D (design changes, reported separately): D1 joint scoring, D2 no persona, D2b synthetic
  trait panel, D3 a second model.

This replaces the fractional factorial in `design.py` for the study; that expander stays for the
smoketest designs. Mapping cells to rendered jobs (per-policy calls, paraphrase texts) is the
job builder's concern; here paraphrases are referenced only by level name.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, replace

from llm_panel.domain.models import Persona
from llm_panel.domain.personas import NAMED_PANEL_SIZE

BASELINE_WORDING = "baseline"
PARAPHRASE_LEVELS = ("para_1", "para_2", "para_3")  # frozen paraphrase sets (TASK-16)
NAME_AND_DEFINITION = "name_and_definition"
DEFINITION_ONLY = "definition_only"  # Q1: neutral codes P1..P11, name removed everywhere
PERSONA_POLICY = "persona_policy"  # B: one persona x one policy, all criteria in one JSON
JOINT = "joint"  # D1: all policies in one prompt per persona x criterion
NO_PERSONA = "none"
NO_EVIDENCE = "none"

# Prereg section 8, fixed before data (D2b right after D2, user decision 2026-10-04).
PRIORITY_ORDER = ("R", "Q1", "Q2", "Q4", "Q3", "R-T", "D2", "D2b", "D1", "D3")
# "If too expensive, drop Q3, R-T and D3 first." Read as: when the whole plan does not fit,
# drop these units one at a time in the listed order until the rest fits; only then does the
# priority order cut further.
DROP_FIRST = ("Q3", "R-T", "D3")
UNIT_CELLS = {
    "R": ("B", "B'"),
    "Q1": ("Q1",),
    "Q2": ("Q2a", "Q2b", "Q2c"),
    "Q4": ("Q4",),
    "Q3": ("Q3a", "Q3b", "Q3c"),
    "R-T": ("R-T0", "R-T1"),
    "D2": ("D2",),
    "D2b": ("D2b",),
    "D1": ("D1",),
    "D3": ("D3",),
}
D_CELLS = ("D1", "D2", "D2b", "D3")
DRIFT_CELL = "B'"
D2_REPEATS = 51  # prereg s8: 11 policies x 51 repeats = 561 calls


@dataclass(frozen=True)
class ModelRef:
    provider: str
    snapshot: str

    def __post_init__(self) -> None:
        if not self.provider or not self.snapshot:
            raise ValueError("a model needs provider and snapshot (pinned, not an alias)")


@dataclass(frozen=True)
class Factors:
    """Every factor a cell can vary. A cell's factors differ from B's in at most one field."""

    model: ModelRef
    temperature: float | None  # None = provider default (measured in the pilot)
    persona_source: str
    evidence: str  # evidence packet name; "none" = no packet
    policy_identifier: str = NAME_AND_DEFINITION
    description_wording: str = BASELINE_WORDING
    instruction_wording: str = BASELINE_WORDING
    call_unit: str = PERSONA_POLICY


@dataclass(frozen=True)
class DSettings:
    """Block D cell settings from the design file. Repeats (prereg s8): k_Q, except D2."""

    persona_source: str | None = None  # D2b only
    model: ModelRef | None = None  # D3 only


@dataclass(frozen=True)
class OatDesign:
    baseline: Factors
    k_r: int
    k_q: int
    rt_temperatures: tuple[float, ...]  # temperature 0 and one higher level
    d_cells: Mapping[str, DSettings] = field(default_factory=dict)  # R-T and D cells get k_q
    # D2 (no persona) is 11 calls per repeat; 51 repeats = 561 calls, one B repeat's worth, so it
    # serves as an independent noise estimator (prereg s5, s8).
    d2_repeats: int = D2_REPEATS
    base_seed: int = 0
    order_seed: int = 0
    n_personas: int = NAMED_PANEL_SIZE
    # Optional subset of cell ids to expand (e.g. ("B",) for a baseline-only pilot); None = all.
    # Seeds stay those of the full design, so a subset's job ids match the full design's.
    cells: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Cell:
    cell_id: str
    block: str  # "R" | "Q" | "D"
    unit: str  # priority unit (PRIORITY_ORDER)
    factors: Factors
    seeds: tuple[int, ...]  # one sampling seed per repeat

    @property
    def repeats(self) -> int:
        return len(self.seeds)


def differing_factors(a: Factors, b: Factors) -> tuple[str, ...]:
    return tuple(f.name for f in fields(Factors) if getattr(a, f.name) != getattr(b, f.name))


def _validate(design: OatDesign) -> None:
    base = design.baseline
    if design.k_r < 1 or design.k_q < 1 or design.d2_repeats < 1:
        raise ValueError("k_r, k_q and d2_repeats must be >= 1")
    if base.persona_source == NO_PERSONA or base.evidence == NO_EVIDENCE:
        raise ValueError("baseline needs a persona panel and an evidence packet")
    default = Factors(base.model, base.temperature, base.persona_source, base.evidence)
    if base != default:
        raise ValueError(
            "baseline must use names and definitions, baseline wordings and per-policy calls"
        )
    temps = design.rt_temperatures
    if len(temps) != 2 or len(set(temps)) != 2 or 0.0 not in temps:
        raise ValueError("rt_temperatures must be temperature 0 and one higher level")
    if base.temperature in temps:
        raise ValueError("an R-T temperature equals the baseline temperature")
    for name, d in design.d_cells.items():
        if name not in D_CELLS:
            raise ValueError(f"unknown block D cell {name!r}; expected one of {D_CELLS}")
        wants_persona, wants_model = name == "D2b", name == "D3"
        if (d.persona_source is not None) != wants_persona or (d.model is not None) != wants_model:
            raise ValueError(
                f"{name}: persona_source is for D2b only, model for D3 only (both required)"
            )
        if wants_persona and d.persona_source in (base.persona_source, NO_PERSONA):
            raise ValueError("D2b needs a persona panel other than the baseline's or 'none'")
        if wants_model and d.model == base.model:
            raise ValueError("D3 needs a model other than the baseline's")


def expand_cells(design: OatDesign) -> tuple[Cell, ...]:
    _validate(design)
    base, s0 = design.baseline, design.base_seed

    def seeds(n: int, start: int = 0) -> tuple[int, ...]:
        # Repeat r uses seed base_seed + r in every cell, so variations pair with B's repeats.
        return tuple(s0 + start + r for r in range(n))

    k_q = design.k_q
    cells = [
        Cell("B", "R", "R", base, seeds(design.k_r)),
        # B' gets the next seed so its job ids differ from every B repeat (no dedupe skip).
        Cell(DRIFT_CELL, "R", "R", base, seeds(1, start=design.k_r)),
    ]
    for i, t in enumerate(sorted(design.rt_temperatures)):
        cells.append(Cell(f"R-T{i}", "R", "R-T", replace(base, temperature=t), seeds(k_q)))
    q1 = replace(base, policy_identifier=DEFINITION_ONLY)
    cells.append(Cell("Q1", "Q", "Q1", q1, seeds(k_q)))
    for suffix, level in zip("abc", PARAPHRASE_LEVELS, strict=True):
        f = replace(base, description_wording=level)
        cells.append(Cell(f"Q2{suffix}", "Q", "Q2", f, seeds(k_q)))
    for suffix, level in zip("abc", PARAPHRASE_LEVELS, strict=True):
        f = replace(base, instruction_wording=level)
        cells.append(Cell(f"Q3{suffix}", "Q", "Q3", f, seeds(k_q)))
    cells.append(Cell("Q4", "Q", "Q4", replace(base, evidence=NO_EVIDENCE), seeds(k_q)))
    for name in D_CELLS:
        d = design.d_cells.get(name)
        if d is None:
            continue
        f = {
            "D1": replace(base, call_unit=JOINT),
            "D2": replace(base, persona_source=NO_PERSONA),
            "D2b": replace(base, persona_source=d.persona_source),
            "D3": replace(base, model=d.model),
        }[name]
        cells.append(Cell(name, "D", name, f, seeds(design.d2_repeats if name == "D2" else k_q)))
    if design.cells is None:
        return tuple(cells)
    wanted = set(design.cells)
    unknown = wanted - {c.cell_id for c in cells}
    if not wanted or unknown:
        raise ValueError(
            f"cells must list expanded cell ids (D cells need d_cells); got {sorted(unknown)}"
            if unknown else "cells must not be empty; omit it to run every cell"
        )  # fmt: skip
    return tuple(c for c in cells if c.cell_id in wanted)


def paired_persona_ids(
    cells: Sequence[Cell], panels: Mapping[str, Sequence[Persona]], n: int = NAMED_PANEL_SIZE
) -> tuple[str, ...]:
    """The persona ids every cell outside D2/D2b uses; raises unless they are one panel of n."""
    sources = {c.factors.persona_source for c in cells if c.cell_id not in ("D2", "D2b")}
    if len(sources) != 1:
        raise ValueError(f"paired cells use more than one persona panel: {sorted(sources)}")
    (source,) = sources
    if source not in panels:
        raise ValueError(f"no persona panel loaded for {source!r}")
    ids = tuple(p.id for p in panels[source])
    if len(ids) != n or len(set(ids)) != n:
        raise ValueError(f"panel {source!r} must have {n} distinct personas, got {len(set(ids))}")
    return ids


@dataclass(frozen=True)
class RunSlot:
    cell_id: str
    repeat: int
    seed: int


@dataclass(frozen=True)
class RunOrder:
    seed: int  # recorded so the order can be regenerated
    slots: tuple[RunSlot, ...]


def run_order(cells: Sequence[Cell], seed: int) -> RunOrder:
    """All cells' repeats shuffled together (interleaved), with B' pinned to the very end."""
    slots = [
        RunSlot(c.cell_id, r, s)
        for c in cells
        for r, s in enumerate(c.seeds)
        if c.cell_id != DRIFT_CELL
    ]
    random.Random(seed).shuffle(slots)
    slots += [RunSlot(c.cell_id, r, s) for c in cells if c.cell_id == DRIFT_CELL
              for r, s in enumerate(c.seeds)]  # fmt: skip
    return RunOrder(seed=seed, slots=tuple(slots))


@dataclass(frozen=True)
class NotRun:
    cell_id: str
    unit: str
    reason: str


@dataclass(frozen=True)
class BudgetPlan:
    budget_usd: float
    run: tuple[str, ...]  # cell ids, in priority order
    not_run: tuple[NotRun, ...]  # every prereg cell not run, with the reason
    dropped_first: tuple[str, ...]  # DROP_FIRST units removed
    planned_cost_usd: float


def plan_budget(
    cells: Sequence[Cell], cell_cost_usd: Mapping[str, float], budget_usd: float
) -> BudgetPlan:
    """Prereg section 8 stopping rule over precomputed per-cell costs.

    budget_usd is what remains under the ceiling (ceiling minus actual spend). Units are whole:
    a unit runs only if all its cells fit. The priority pass stops at the first unit that does
    not fit; it does not skip ahead to cheaper lower-priority units.
    """
    present = {c.cell_id: c for c in cells}
    for cid in present:
        cost = cell_cost_usd.get(cid)
        if cost is None or cost < 0:
            raise ValueError(f"cell {cid!r} needs a non-negative precomputed cost")
    unit_cost = {
        u: sum(cell_cost_usd[c] for c in ids if c in present)
        for u, ids in UNIT_CELLS.items()
        if any(c in present for c in ids)
    }
    reasons: dict[str, str] = {
        u: "not in design file" for u in PRIORITY_ORDER if u not in unit_cost
    }
    candidates = [u for u in PRIORITY_ORDER if u in unit_cost]
    dropped: list[str] = []
    for u in DROP_FIRST:
        if sum(unit_cost[x] for x in candidates) <= budget_usd:
            break
        if u in candidates:
            candidates.remove(u)
            dropped.append(u)
            reasons[u] = "dropped first: full plan exceeds budget (prereg s8)"
    chosen: list[str] = []
    spent = 0.0
    for i, u in enumerate(candidates):
        if spent + unit_cost[u] > budget_usd:
            for later in candidates[i:]:
                reasons[later] = "budget: stopped at first unit in priority order that did not fit"
            break
        chosen.append(u)
        spent += unit_cost[u]
    run = tuple(c for u in chosen for c in UNIT_CELLS[u] if c in present)
    not_run = tuple(
        NotRun(c, u, reasons[u]) for u in PRIORITY_ORDER if u in reasons for c in UNIT_CELLS[u]
        if c in present or reasons[u] == "not in design file"
    )  # fmt: skip
    return BudgetPlan(budget_usd, run, not_run, tuple(dropped), spent)
