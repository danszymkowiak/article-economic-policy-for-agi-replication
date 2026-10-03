import pytest

from llm_panel.domain.jobs import count_jobs, jobs_for_spec
from llm_panel.domain.models import Criterion, Persona, Policy
from llm_panel.domain.models import RunSpec as Spec

POLICIES = tuple(
    Policy(f"p{i}", f"Policy Name {i}", f"desc {i}", f"mechanics {i}") for i in range(11)
)
CRITERIA = tuple(Criterion(f"c{i}", f"Crit {i}", f"what {i}") for i in range(3))
PERSONAS = tuple(Persona(f"u{i}", "reconstructed", f"economist {i}") for i in range(2))


def spec(**kw):
    base = dict(provider="fake", model_snapshot="m", persona_source="reconstructed", repeats=2)
    base.update(kw)
    return Spec(**base)


def build(s, evidence="EVIDENCE TEXT"):
    return jobs_for_spec(s, PERSONAS, POLICIES, CRITERIA, evidence)


def test_all_policies_default_one_job_per_persona_criterion_repeat():
    jobs = build(spec())
    assert len(jobs) == 2 * 3 * 2
    assert all(len(j.policy_ids) == 11 for j in jobs)
    assert len({j.job_id for j in jobs}) == len(jobs)


def test_one_policy_mode():
    jobs = build(spec(prompt_format="one_policy"))
    assert len(jobs) == 2 * 3 * 2 * 11
    assert all(len(j.policy_ids) == 1 for j in jobs)
    assert len({j.job_id for j in jobs}) == len(jobs)


def test_repeats_get_distinct_seeds():
    seeds = {j.seed for j in build(spec(base_seed=10))}
    assert seeds == {10, 11}


def test_job_carries_run_parameters():
    j = build(spec(temperature=0.3))[0]
    assert (j.provider, j.model_snapshot, j.temperature) == ("fake", "m", 0.3)
    assert j.spec_id == spec(temperature=0.3).spec_id


def test_blinding_hides_names_and_uses_neutral_labels():
    j = build(spec(blinded=True))[0]
    assert "Policy Name" not in j.prompt and "mechanics 3" in j.prompt
    assert j.policy_labels == tuple("ABCDEFGHIJK")
    assert j.policy_ids == tuple(p.id for p in POLICIES) or set(j.policy_ids) == {
        p.id for p in POLICIES
    }


def test_named_prompt_contains_names_and_evidence():
    j = build(spec())[0]
    assert "Policy Name 3" in j.prompt and "EVIDENCE TEXT" in j.prompt
    assert "economist" in j.prompt and "Crit" in j.prompt


def test_no_evidence_omits_block():
    j = build(spec(evidence="none"), evidence="")[0]
    assert "EVIDENCE" not in j.prompt


def test_reversed_order():
    fixed = build(spec(order="fixed"))[0]
    rev = build(spec(order="reversed"))[0]
    assert rev.policy_ids == tuple(reversed(fixed.policy_ids))
    assert rev.job_id != fixed.job_id


def test_shuffled_order_is_deterministic_and_permutes():
    a = build(spec(order="shuffled"))
    b = build(spec(order="shuffled"))
    assert [j.policy_ids for j in a] == [j.policy_ids for j in b]
    assert all(set(j.policy_ids) == {p.id for p in POLICIES} for j in a)
    assert any(j.policy_ids != tuple(p.id for p in POLICIES) for j in a)


def test_unknown_paraphrase_rejected():
    with pytest.raises(ValueError, match="paraphrase"):
        build(spec(paraphrase="nope"))


def test_count_jobs_baseline_numbers():
    c = count_jobs(spec(repeats=1), n_personas=51, n_criteria=15, n_policies=11)
    assert c.calls == 15 * 51  # all 11 policies in one prompt
    assert c.ratings == 15 * 11 * 51
    c1 = count_jobs(
        spec(repeats=1, prompt_format="one_policy"), n_personas=51, n_criteria=15, n_policies=11
    )
    assert c1.calls == 8415 and c1.ratings == 8415


def test_count_matches_built_jobs():
    for fmt in ("all_policies", "one_policy"):
        s = spec(prompt_format=fmt)
        assert count_jobs(s, 2, 3, 11).calls == len(build(s))
