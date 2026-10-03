import hashlib
import json

from hypothesis import given
from hypothesis import strategies as st

from llm_panel.domain.hashing import job_id
from tests.domain.test_models import make_job

prompts = st.text(max_size=200)
snapshots = st.text(min_size=1, max_size=40)
temps = st.floats(min_value=0, max_value=2, allow_nan=False)
seeds = st.integers(min_value=0, max_value=2**31)


@given(prompts, snapshots, temps, seeds)
def test_identical_inputs_give_same_id(p, m, t, s):
    assert job_id(p, m, t, s) == job_id(p, m, t, s)


@given(prompts, prompts, snapshots, temps, seeds)
def test_changing_prompt_changes_id(p1, p2, m, t, s):
    if p1 != p2:
        assert job_id(p1, m, t, s) != job_id(p2, m, t, s)


@given(prompts, snapshots, snapshots, temps, seeds)
def test_changing_snapshot_changes_id(p, m1, m2, t, s):
    if m1 != m2:
        assert job_id(p, m1, t, s) != job_id(p, m2, t, s)


@given(prompts, snapshots, temps, temps, seeds)
def test_changing_temperature_changes_id(p, m, t1, t2, s):
    if t1 != t2:
        assert job_id(p, m, t1, s) != job_id(p, m, t2, s)


@given(prompts, snapshots, temps, seeds, seeds)
def test_changing_seed_changes_id(p, m, t, s1, s2):
    if s1 != s2:
        assert job_id(p, m, t, s1) != job_id(p, m, t, s2)


def test_no_concatenation_ambiguity():
    assert job_id("ab", "c", 1.0, 0) != job_id("a", "bc", 1.0, 0)


def test_int_and_float_temperature_agree():
    assert job_id("p", "m", 1, 0) == job_id("p", "m", 1.0, 0)


def test_is_sha256_hex_of_canonical_encoding():
    blob = json.dumps(["p", "m", 0.5, 3], separators=(",", ":"), ensure_ascii=False)
    assert job_id("p", "m", 0.5, 3) == hashlib.sha256(blob.encode()).hexdigest()


def test_rendered_job_exposes_job_id():
    job = make_job(prompt="hello", model_snapshot="m", temperature=0.5, seed=3)
    assert job.job_id == job_id("hello", "m", 0.5, 3)
