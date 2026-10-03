from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.build_jobs import StudyInputs, build_jobs
from llm_panel.domain.models import Criterion, Persona, Policy, RunSpec
from tests.domain.test_results import row

INPUTS = StudyInputs(
    personas={"reconstructed": tuple(Persona(f"u{i}", "reconstructed", f"e{i}") for i in range(3))},
    policies=tuple(Policy(f"p{i}", f"N{i}", f"d{i}", f"m{i}") for i in range(4)),
    criteria=(Criterion("c1", "C1", "x"), Criterion("c2", "C2", "y")),
    evidence={"reconstructed": "EVID", "none": ""},
)


def specs(**kw):
    base = dict(provider="fake", model_snapshot="m", persona_source="reconstructed", repeats=2)
    base.update(kw)
    return [RunSpec(**base)]


def test_builds_all_jobs_and_reports_counts(tmp_path):
    store = JsonlResultStore(tmp_path / "r.jsonl")
    res = build_jobs(specs(), INPUTS, store)
    assert len(res.jobs) == 3 * 2 * 2 == res.total
    assert res.skipped == 0 and res.duplicates == 0
    assert res.per_spec[0].calls == 12 and res.per_spec[0].ratings == 12 * 4


def test_skips_jobs_already_in_store_and_resumes(tmp_path):
    store = JsonlResultStore(tmp_path / "r.jsonl")
    first = build_jobs(specs(), INPUTS, store)
    for job in first.jobs[:5]:
        store.append(row(job_id=job.job_id, status="ok"))
    second = build_jobs(specs(), INPUTS, store)
    assert second.skipped == 5 and len(second.jobs) == 7
    assert {j.job_id for j in second.jobs}.isdisjoint({j.job_id for j in first.jobs[:5]})
    for job in second.jobs:
        store.append(row(job_id=job.job_id, status="ok"))
    assert build_jobs(specs(), INPUTS, store).jobs == []


def test_nonterminal_rows_do_not_skip(tmp_path):
    store = JsonlResultStore(tmp_path / "r.jsonl")
    job = build_jobs(specs(), INPUTS, store).jobs[0]
    store.append(row(job_id=job.job_id, status="invalid", attempt=1))
    assert len(build_jobs(specs(), INPUTS, store).jobs) == 12


def test_specs_sharing_a_prompt_are_deduplicated(tmp_path):
    # score_aggregation is analysis-only, so two specs differing only in it render identical jobs
    two = specs(aggregation="mean") + specs(aggregation="median")
    res = build_jobs(two, INPUTS, JsonlResultStore(tmp_path / "r.jsonl"))
    assert len(res.jobs) == 12 and res.duplicates == 12


def test_none_persona_source_gives_single_neutral_persona(tmp_path):
    res = build_jobs(
        specs(persona_source="none", evidence="none"), INPUTS, JsonlResultStore(tmp_path / "r")
    )
    assert len(res.jobs) == 1 * 2 * 2
    assert {j.persona_id for j in res.jobs} == {"none"}
