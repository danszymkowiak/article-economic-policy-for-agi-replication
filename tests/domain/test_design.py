import itertools
from collections import Counter

import pytest

from llm_panel.domain.design import Design, expand_fractional, expand_full, to_run_specs

FACTORS = {"a": (0, 1), "b": ("x", "y"), "c": (True, False), "d": (1, 2, 3)}


def test_full_factorial_is_cartesian_product():
    rows = expand_full(FACTORS)
    assert len(rows) == 2 * 2 * 2 * 3
    assert len({tuple(r.items()) for r in rows}) == len(rows)


def test_fractional_is_unique_subset_of_full():
    full = {tuple(r.items()) for r in expand_full(FACTORS)}
    rows = expand_fractional(FACTORS, n_runs=12, seed=1)
    assert len(rows) == 12
    assert {tuple(r.items()) for r in rows} <= full
    assert len({tuple(r.items()) for r in rows}) == 12


def test_fractional_main_effects_balanced():
    rows = expand_fractional(FACTORS, n_runs=12, seed=1)
    for name, levels in FACTORS.items():
        counts = Counter(r[name] for r in rows)
        assert set(counts) == set(levels)
        assert max(counts.values()) - min(counts.values()) == 0


def test_fractional_pairs_nearly_balanced():
    rows = expand_fractional(FACTORS, n_runs=12, seed=1)
    for f, g in itertools.combinations(FACTORS, 2):
        counts = Counter((r[f], r[g]) for r in rows)
        assert len(counts) == len(FACTORS[f]) * len(FACTORS[g])  # every pair appears


def test_fractional_deterministic_per_seed():
    assert expand_fractional(FACTORS, 8, seed=3) == expand_fractional(FACTORS, 8, seed=3)
    assert expand_fractional(FACTORS, 8, seed=3) != expand_fractional(FACTORS, 8, seed=4)


def test_fractional_unbalanced_count_still_near_balanced():
    rows = expand_fractional(FACTORS, n_runs=7, seed=0)
    for name in FACTORS:
        counts = Counter(r[name] for r in rows)
        assert max(counts.values()) - min(counts.values()) <= 1


def test_fractional_n_runs_at_least_full_returns_full():
    assert len(expand_fractional(FACTORS, n_runs=999, seed=0)) == 24


def test_fractional_rejects_nonpositive():
    with pytest.raises(ValueError):
        expand_fractional(FACTORS, n_runs=0, seed=0)


def design(**kw):
    base = dict(
        models=(
            {"provider": "fake", "snapshot": "fake-1"},
            {"provider": "fake", "snapshot": "fake-2", "temperature": 0.0},
        ),
        persona_source=("reconstructed", "none"),
        paraphrase=("baseline",),
        policy_blinding=("named", "blinded"),
        evidence_packet=("reconstructed", "none"),
        presentation_order=("fixed", "reversed"),
        score_aggregation=("mean", "median"),
        repeats=3,
    )
    base.update(kw)
    return Design(**base)


def test_to_run_specs_full_covers_all_factors():
    specs = to_run_specs(design(mode="full"))
    assert len(specs) == 2 * 2 * 1 * 2 * 2 * 2 * 2
    assert {s.order for s in specs} == {"fixed", "reversed"}
    assert {s.aggregation for s in specs} == {"mean", "median"}
    assert {s.blinded for s in specs} == {False, True}
    assert all(s.repeats == 3 for s in specs)
    assert {s.temperature for s in specs} == {1.0, 0.0}  # per-model override
    assert len({s.spec_id for s in specs}) == len(specs)


def test_to_run_specs_fractional():
    specs = to_run_specs(design(mode="fractional", n_runs=10, seed=5))
    assert len(specs) == 10
    assert len({s.spec_id for s in specs}) == 10


def test_fractional_requires_n_runs():
    with pytest.raises(ValueError):
        to_run_specs(design(mode="fractional"))


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        to_run_specs(design(mode="bogus"))
