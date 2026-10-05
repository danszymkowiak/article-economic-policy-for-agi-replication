"""TASK-19: rank stability between cells, from synthetic raw-store rows. Offline."""

import csv
import dataclasses
import io
import itertools
import json

import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.baseline_comparison import cell_observations
from llm_panel.application.rank_stability import (
    render_aggregation_csv,
    render_markdown,
    render_noise_csv,
    render_shifts_csv,
    render_tau_csv,
    run_rank_stability,
)
from llm_panel.bootstrap.cli import main
from llm_panel.domain.analysis_baseline import COMPOSITES, TABLE4_CRITERIA
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import StoredRow

CRITERIA = (*TABLE4_CRITERIA, "political_support", "admin_capacity_speed")
POLICIES = tuple(f"pol{i:02d}" for i in range(11))
PERSONAS = ("p1", "p2", "p3")
_SERIAL = itertools.count()


def _stored(job, text, status="ok"):
    return StoredRow(
        job_id=job.job_id, status=status, attempt=1, provider="fake", model_snapshot="fake-1",
        temperature=None, seed=job.seed, timestamp="t", request=job.to_dict(),
        response={"text": text} if status == "ok" else None, usage={}, batch_id="b",
    )  # fmt: skip


def _row(cell, persona, policy, score, *, repeat=0, status="ok"):
    job = RenderedJob(
        prompt=f"{cell} {persona} {policy} {repeat} {next(_SERIAL)}", provider="fake",
        model_snapshot="fake-1", temperature=None, seed=repeat, persona_id=persona,
        criterion_id="", policy_ids=(policy,), policy_labels=(policy,), spec_id="s",
        repeat=repeat, criterion_ids=CRITERIA, cell_id=cell,
    )  # fmt: skip
    text = json.dumps(
        {"ratings": [{"criterion": c, "score": score, "rationale": "r"} for c in CRITERIA]}
    )
    return _stored(job, text, status)


def _joint_row(cell, persona, criterion, scores, *, repeat=0):
    """D1: one persona x criterion call rating every policy under its label."""
    labels = tuple(f"P{i + 1}" for i in range(len(POLICIES)))
    job = RenderedJob(
        prompt=f"{cell} {persona} {criterion} {repeat} {next(_SERIAL)}", provider="fake",
        model_snapshot="fake-1", temperature=None, seed=repeat, persona_id=persona,
        criterion_id=criterion, policy_ids=POLICIES, policy_labels=labels, spec_id="s",
        repeat=repeat, cell_id=cell,
    )  # fmt: skip
    ratings = [
        {"policy": lab, "score": s, "rationale": "r"} for lab, s in zip(labels, scores, strict=True)
    ]
    return _stored(job, json.dumps({"ratings": ratings}))


ASC = [10.0 + 7 * i for i in range(11)]


@pytest.fixture
def store(tmp_path):
    s = JsonlResultStore(tmp_path / "rows.jsonl")
    for repeat in (0, 1, 2):
        for persona in PERSONAS:
            for i, policy in enumerate(POLICIES):
                s.append(_row("B", persona, policy, ASC[i], repeat=repeat))
    for repeat in (0, 1):
        for persona in PERSONAS:
            for i, policy in enumerate(POLICIES):
                s.append(_row("Q1", persona, policy, ASC[i], repeat=repeat))
                s.append(_row("Q4", persona, policy, ASC[10 - i], repeat=repeat))
            for c in CRITERIA:
                s.append(_joint_row("D1", persona, c, ASC, repeat=repeat))
    s.append(_row("Q1", "p1", "pol00", 0.0, status="failed"))
    return s


def test_cell_observations_cover_every_cell_including_joint_jobs(store):
    cells = cell_observations(store)
    assert set(cells) == {"B", "Q1", "Q4", "D1"}
    obs, counts = cells["D1"]
    assert counts.ok_jobs == 2 * 3 * len(CRITERIA)
    assert len(obs) == 2 * 3 * len(CRITERIA) * 11
    assert cells["Q1"][1].not_ok_jobs == 1


def test_identical_and_reversed_cells(store):
    report = run_rank_stability(store, resamples=20, seed=0)
    mean = {
        (c.cell_id, c.composite): c for c in report.result.comparisons if c.aggregation == "mean"
    }
    for name in COMPOSITES:
        assert mean[("Q1", name)].tau == pytest.approx(1.0)
        assert mean[("D1", name)].tau == pytest.approx(1.0)
        assert mean[("Q4", name)].tau == pytest.approx(-1.0)
    assert [c for c in report.cell_order] == ["B", "Q1", "Q4", "D1"]


def test_markdown_carries_wording_rule_resample_basis_and_label(store):
    report = run_rank_stability(store, resamples=1000, seed=0)
    text = render_markdown(report, "results/raw/rows.jsonl")
    assert "lack the claimed precision, not that the recommendations are wrong" in text
    assert "placeholder" not in text.lower() and "still open" not in text  # set 2026-10-04
    assert "not the prereg's 2000" in text
    standard = render_markdown(dataclasses.replace(report, result=dataclasses.replace(
        report.result, resamples=2000)), "results/raw/rows.jsonl")  # fmt: skip
    assert "2000 resamples" in standard and "prereg s12 item 6" in standard
    assert "not the prereg's" not in standard
    assert "exploratory" in text.lower()  # median / trimmed mean are not in prereg s6
    assert "NON-INFERENCE" not in text
    assert "Kendall tau" in text and "Q4" in text
    assert "NON-INFERENCE" in render_markdown(report, "results/pilot/rows.jsonl")


def test_markdown_without_cell_b(tmp_path):
    report = run_rank_stability(JsonlResultStore(tmp_path / "rows.jsonl"), resamples=5, seed=0)
    assert "No cell B data" in render_markdown(report, "results/raw/rows.jsonl")


def test_csvs_hold_every_cell_composite_and_aggregation(store):
    report = run_rank_stability(store, resamples=10, seed=0)
    tau = list(csv.DictReader(io.StringIO(render_tau_csv(report))))
    assert len(tau) == 3 * 3 * len(COMPOSITES)  # cells x aggregations x composites
    assert {"cell_id", "aggregation", "composite", "tau", "ci_low", "ci_high", "band_min",
            "single_run_min", "top3_entered", "bottom3_left", "max_abs_rank_shift",
            "prereg"} <= set(tau[0])  # fmt: skip
    shifts = list(csv.DictReader(io.StringIO(render_shifts_csv(report))))
    assert len(shifts) == 3 * 3 * len(COMPOSITES) * 11
    noise = list(csv.DictReader(io.StringIO(render_noise_csv(report))))
    assert {r["kind"] for r in noise} == {"pairwise", "split_k2"}
    agree = list(csv.DictReader(io.StringIO(render_aggregation_csv(report))))
    assert len(agree) == 4 * 3 * len(COMPOSITES)  # B and three cells x three pairs


def test_cli_analyze_ranks_writes_report(tmp_path, store, capsys):
    (tmp_path / "config.yaml").write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: rows.jsonl\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "ranks",
            "--out", str(out), "--resamples", "20", "--seed", "3"]  # fmt: skip

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    md = (out / "rank_stability.md").read_text()
    assert "NON-INFERENCE" in md and "20 resamples" in md
    for name in ("rank_tau.csv", "rank_shifts.csv", "rank_repeat_noise.csv",
                 "rank_aggregation_agreement.csv"):  # fmt: skip
        assert (out / name).exists()
    assert "rank_stability.md" in capsys.readouterr().out
