import dataclasses

import pytest

from llm_panel.domain.models import (
    Criterion,
    Persona,
    Policy,
    Rating,
    RenderedJob,
    RunSpec,
)

CLASSES = [Persona, Policy, Criterion, RunSpec, RenderedJob, Rating]


def make_spec(**kw):
    base = dict(provider="fake", model_snapshot="fake-1", persona_source="reconstructed")
    base.update(kw)
    return RunSpec(**base)


def make_job(**kw):
    base = dict(
        prompt="p",
        provider="fake",
        model_snapshot="fake-1",
        temperature=1.0,
        seed=0,
        persona_id="p1",
        criterion_id="c1",
        policy_ids=("a", "b"),
        policy_labels=("a", "b"),
        spec_id="s",
        repeat=0,
    )
    base.update(kw)
    return RenderedJob(**base)


@pytest.mark.parametrize("cls", CLASSES)
def test_all_domain_types_are_frozen_dataclasses(cls):
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen


def test_persona_policy_criterion_fields():
    persona = Persona(id="p1", source="reconstructed", description="a centrist economist")
    policy = Policy(id="ubc", name="UBC", description="d", blinded_description="b")
    crit = Criterion(id="c1", name="Ownership of Gains", description="d", group="agency")
    assert (persona.id, policy.name, crit.group) == ("p1", "UBC", "agency")
    with pytest.raises(dataclasses.FrozenInstanceError):
        persona.id = "x"


def test_runspec_defaults_and_hashable():
    spec = make_spec()
    assert spec.prompt_format == "all_policies"
    assert spec.repeats == 1
    assert hash(spec) == hash(make_spec())


def test_runspec_spec_id_is_stable_and_sensitive():
    assert make_spec().spec_id == make_spec().spec_id
    assert make_spec().spec_id != make_spec(order="reversed").spec_id


@pytest.mark.parametrize(
    "kw",
    [
        dict(repeats=0),
        dict(temperature=-0.1),
        dict(temperature=2.5),
        dict(order="sideways"),
        dict(prompt_format="bogus"),
        dict(model_snapshot=""),
    ],
)
def test_runspec_rejects_invalid(kw):
    with pytest.raises(ValueError):
        make_spec(**kw)


def test_rating_score_range():
    Rating(job_id="j", persona_id="p", criterion_id="c", policy_id="a", score=0, rationale="r")
    Rating(job_id="j", persona_id="p", criterion_id="c", policy_id="a", score=100, rationale="r")
    for bad in (-1, 100.5):
        with pytest.raises(ValueError):
            Rating(
                job_id="j", persona_id="p", criterion_id="c", policy_id="a", score=bad, rationale=""
            )


def test_rendered_job_label_policy_lengths_must_match():
    with pytest.raises(ValueError):
        make_job(policy_labels=("a",))


def test_rendered_job_roundtrips_dict():
    job = make_job()
    assert RenderedJob.from_dict(job.to_dict()) == job
