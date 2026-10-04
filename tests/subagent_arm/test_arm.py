"""CLAUDE SUBAGENT ARM (TASK-35, prereg s9a): job building, task files, ingest with discards and
one retry. Offline; never touches results/raw."""

import json
from pathlib import Path

import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.bootstrap.config import load_config
from llm_panel.bootstrap.inputs_loader import load_study_materials
from llm_panel.domain.oat_design import Factors, ModelRef
from llm_panel.domain.results import STATUS_FAILED, STATUS_INVALID, STATUS_OK
from subagent_arm.arm import (
    EXPECTED_TOOL_USES,
    PROVIDER,
    SNAPSHOT,
    Workspace,
    agent_prompt,
    build_jobs,
    ingest,
    pending,
    write_tasks,
)

REPO = Path(__file__).parents[2]
BASELINE = Factors(ModelRef("opencode", "glm-5.3-flash"), None, "named", "wikipedia")


@pytest.fixture(scope="module")
def materials():
    return load_study_materials(load_config(REPO / "config.yaml"))


@pytest.fixture(scope="module")
def jobs(materials):
    return build_jobs(materials, BASELINE, k_c=2)


def answer_text(job, score=50.0):
    ratings = [{"criterion": c, "score": score, "rationale": "r"} for c in job.criterion_ids]
    return json.dumps({"ratings": ratings})


def test_jobs_are_b_on_the_claude_model_one_per_persona_policy_repeat(jobs):
    assert len(jobs) == 2 * 51 * 11
    assert {j.cell_id for j in jobs} == {"B"}
    assert {(j.provider, j.model_snapshot, j.temperature) for j in jobs} == {
        (PROVIDER, SNAPSHOT, None)
    }
    assert {j.repeat for j in jobs} == {0, 1}
    assert len({j.job_id for j in jobs}) == len(jobs)
    assert all(len(j.criterion_ids) == 13 for j in jobs)


def test_prompts_equal_the_main_arm_b_prompts(jobs, materials):
    from llm_panel.domain.oat_design import Cell
    from llm_panel.domain.study_jobs import jobs_for_cell_repeat

    main = jobs_for_cell_repeat(Cell("B", "R", "B", BASELINE, (0,)), 0, materials)
    assert [j.prompt for j in jobs if j.repeat == 0] == [j.prompt for j in main]


def test_task_file_holds_exactly_the_rendered_prompt(tmp_path, jobs):
    ws = Workspace(tmp_path)
    write_tasks(ws, jobs[:3])
    for j in jobs[:3]:
        assert ws.task_path(j.job_id).read_text(encoding="utf-8") == j.prompt


def test_agent_prompt_names_one_task_file_one_answer_file_and_forbids_the_rest(tmp_path, jobs):
    ws = Workspace(tmp_path)
    text = agent_prompt(ws, jobs[0], attempt=1)
    assert str(ws.task_path(jobs[0].job_id)) in text
    assert str(ws.answer_path(jobs[0].job_id, 1)) in text
    assert "do not read any other file" in text.lower()
    assert jobs[0].persona_id not in text and "ubc" not in text.lower()  # nothing about the job
    assert EXPECTED_TOOL_USES == 2


def test_ingest_stores_valid_answers_and_leaves_missing_ones_pending(tmp_path, jobs):
    ws, store = Workspace(tmp_path), JsonlResultStore(tmp_path / "rows.jsonl")
    sample = jobs[:3]
    ws.answer_path(sample[0].job_id, 1).parent.mkdir(parents=True)
    ws.answer_path(sample[0].job_id, 1).write_text(answer_text(sample[0]), encoding="utf-8")
    result = ingest(store, ws, sample, now=lambda: "t")
    assert (result.ok, result.invalid, result.failed, result.waiting) == (1, 0, 0, 2)
    (row,) = list(store.iter_rows())
    assert row.status == STATUS_OK and row.attempt == 1 and row.request["cell_id"] == "B"
    assert row.temperature is None and row.provider == PROVIDER
    assert [(j.job_id, a) for j, a in pending(store, sample)] == [
        (sample[1].job_id, 1),
        (sample[2].job_id, 1),
    ]


def test_malformed_answer_is_retried_once_then_failed(tmp_path, jobs):
    ws, store = Workspace(tmp_path), JsonlResultStore(tmp_path / "rows.jsonl")
    job = jobs[0]
    ws.answer_path(job.job_id, 1).parent.mkdir(parents=True)
    ws.answer_path(job.job_id, 1).write_text("not json", encoding="utf-8")
    ingest(store, ws, [job], now=lambda: "t")
    assert [r.status for r in store.iter_rows()] == [STATUS_INVALID]
    assert [(j.job_id, a) for j, a in pending(store, [job])] == [(job.job_id, 2)]
    ws.answer_path(job.job_id, 2).write_text("still not json", encoding="utf-8")
    ingest(store, ws, [job], now=lambda: "t")
    rows = list(store.iter_rows())
    assert [(r.status, r.attempt) for r in rows] == [(STATUS_INVALID, 1), (STATUS_FAILED, 2)]
    assert pending(store, [job]) == []
    ingest(store, ws, [job], now=lambda: "t")  # rerun is a no-op
    assert len(list(store.iter_rows())) == 2


def test_discarded_run_counts_as_an_attempt_even_with_a_valid_answer(tmp_path, jobs):
    ws, store = Workspace(tmp_path), JsonlResultStore(tmp_path / "rows.jsonl")
    job = jobs[0]
    ws.answer_path(job.job_id, 1).parent.mkdir(parents=True)
    ws.answer_path(job.job_id, 1).write_text(answer_text(job), encoding="utf-8")
    ws.discard(job.job_id, 1)
    ingest(store, ws, [job], now=lambda: "t")
    (row,) = list(store.iter_rows())
    assert row.status == STATUS_INVALID and "discarded" in row.error
    assert row.response is None  # the discarded text is not stored as a response
    assert [(j.job_id, a) for j, a in pending(store, [job])] == [(job.job_id, 2)]


def test_ingest_never_duplicates_finished_jobs(tmp_path, jobs):
    ws, store = Workspace(tmp_path), JsonlResultStore(tmp_path / "rows.jsonl")
    job = jobs[0]
    ws.answer_path(job.job_id, 1).parent.mkdir(parents=True)
    ws.answer_path(job.job_id, 1).write_text(answer_text(job), encoding="utf-8")
    ingest(store, ws, [job], now=lambda: "t")
    ingest(store, ws, [job], now=lambda: "t")
    assert len(list(store.iter_rows())) == 1
