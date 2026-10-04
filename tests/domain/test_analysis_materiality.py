"""TASK-28: materiality shifts (prereg s6 item 2), planted and null cases."""

import math

import numpy as np
import pytest

from llm_panel.domain.analysis_materiality import (
    MATERIALITY_M,
    SENSITIVITY_M,
    materiality,
)
from llm_panel.domain.analysis_rank import CellArray

N_P, N_J, N_C = 20, 4, 3


def _cell(scores, cell_id, personas=None):
    r, c, j, p = scores.shape
    return CellArray(
        cell_id,
        tuple(personas or (f"p{i:03d}" for i in range(p))),
        tuple(f"pol{i}" for i in range(j)),
        tuple(f"crit{i}" for i in range(c)),
        tuple(range(r)),
        scores,
    )


def _ratings(rng, truth, persona, k, noise=2.0, shift=0.0):
    run = rng.normal(0, 0.5, (k, 1, 1, 1))  # shared run shock
    eps = rng.normal(0, noise, (k, N_C, N_J, N_P))
    shift = np.broadcast_to(shift, (N_C, N_J))[None, :, :, None]
    return truth[None, :, :, None] + persona[None, None, None, :] + shift + run + eps


@pytest.fixture
def cells():
    rng = np.random.default_rng(3)
    truth = rng.normal(50, 10, (N_C, N_J))
    persona = rng.normal(0, 6, N_P)
    planted = np.zeros((N_C, N_J))
    planted[1, 2] = 10.0  # crit1 x pol2 shifted up by 10
    planted[0, 0] = -6.0  # crit0 x pol0 shifted down by 6
    b = _cell(_ratings(rng, truth, persona, 5), "B")
    q = _cell(_ratings(rng, truth, persona, 3, shift=planted), "Q1")
    null = _cell(_ratings(rng, truth, persona, 3), "Q4")
    return b, q, null


def test_m_is_fixed_by_the_prereg():
    assert MATERIALITY_M == 5.0 and SENSITIVITY_M == (3.0, 8.0)


def test_planted_shifts_are_counted_with_sign_size_and_noise_multiple(cells):
    b, q, _ = cells
    m = materiality(b, q)
    assert m.cell_id == "Q1" and m.n_units == N_C * N_J and m.k_b == 5 and m.k_cell == 3
    assert m.pairing == "paired" and m.noise_source == "own"
    assert m.counts[5.0] == 2 and m.counts[8.0] == 1 and m.counts[3.0] >= 2
    units = {(u.policy_id, u.criterion): u for u in m.units}
    up, down = units[("pol2", "crit1")], units[("pol0", "crit0")]
    assert up.shift == pytest.approx(10.0, abs=1.5) and up.beyond(5.0)
    assert down.shift == pytest.approx(-6.0, abs=1.5) and down.beyond(5.0)
    assert up.cell_mean - up.b_mean == pytest.approx(up.shift)
    # the noise SE of a shift is small (noise 2 over 20 personas, 5 and 3 runs), so 10 points is
    # a large multiple of it
    assert 0 < m.noise_se < 1.0
    assert up.noise_multiple == pytest.approx(up.shift / m.noise_se)
    assert up.noise_multiple > 10 and m.m_noise_multiple == pytest.approx(5.0 / m.noise_se)
    others = [u for k, u in units.items() if k not in {("pol2", "crit1"), ("pol0", "crit0")}]
    assert all(abs(u.shift) < 3.0 for u in others)


def test_null_cell_has_no_material_shift_and_sits_in_the_split_band(cells):
    b, _, null = cells
    m = materiality(b, null)
    assert m.counts == {3.0: 0, 5.0: 0, 8.0: 0}
    assert all(abs(u.noise_multiple) < 4 for u in m.units)
    assert len(m.band[5.0]) == math.comb(5, 3) and set(m.band[5.0]) == {0}


def test_split_band_counts_b_against_itself():
    rng = np.random.default_rng(0)
    truth = np.zeros((N_C, N_J))
    scores = _ratings(rng, truth, np.zeros(N_P), 4, noise=0.1)
    scores[0, 0, 0] += 20  # one B run far off on one unit: splits containing it count it
    b = _cell(scores, "B")
    m = materiality(b, _cell(scores[:2], "Q2a"))
    # k_cell = 2 of 4: a split mean of 2 vs 2 differs by 20 / 2 = 10 on that unit
    assert sorted(m.band[5.0]) == [1] * math.comb(4, 2)
    assert set(m.band[8.0]) == {1}


def test_one_repeat_cell_borrows_b_noise_and_band_needs_fewer_repeats(cells):
    b, q, _ = cells
    one = _cell(q.scores[:1], "R-T0")
    m = materiality(b, one)
    assert m.noise_source == "B" and m.k_cell == 1
    assert len(m.band[5.0]) == 5
    many = _cell(np.concatenate([q.scores, q.scores]), "D2")
    assert materiality(b, many).band == {3.0: (), 5.0: (), 8.0: ()}


def test_units_missing_on_either_side_are_left_out(cells):
    b, q, _ = cells
    scores = q.scores.copy()
    scores[:, 2, 3, :] = np.nan  # crit2 x pol3 never rated in the cell
    m = materiality(b, _cell(scores, "Q1"))
    assert m.n_units == N_C * N_J - 1
    assert ("pol3", "crit2") not in {(u.policy_id, u.criterion) for u in m.units}


def test_custom_margins():
    rng = np.random.default_rng(1)
    truth = np.zeros((N_C, N_J))
    b = _cell(_ratings(rng, truth, np.zeros(N_P), 3), "B")
    m = materiality(b, _cell(_ratings(rng, truth, np.zeros(N_P), 2, shift=4.0), "Q4"), ms=(1, 10))
    assert set(m.counts) == {1.0, 10.0}
    assert m.counts[1.0] == N_C * N_J and m.counts[10.0] == 0
