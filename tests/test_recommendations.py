"""TASK-21: recommendation robustness report from synthetic raw-store rows. Offline."""

import csv
import io
import itertools
import json
from pathlib import Path

import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.recommendations import (
    render_blinding_csv,
    render_clauses_csv,
    render_consistency_csv,
    render_markdown,
    render_noise_csv,
    run_recommendations,
)
from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.published_loader import NET_APPROVAL, load_published
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import StoredRow

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = load_published(ROOT / "analysis/published/paper_table4.csv")
CRITERIA = (*TABLE4_CRITERIA, "political_support", "admin_capacity_speed")
POLICIES = PUBLISHED.policy_order
PERSONAS = ("p0", "p1", "p2", "p3")
POLITICAL = {p: 40.0 + 3 * i for i, p in enumerate(POLICIES)} | {"nit": 5.0}
_SERIAL = itertools.count()


def _row(cell, persona, policy, scores, *, repeat=0, status="ok"):
    job = RenderedJob(
        prompt=f"{cell} {persona} {policy} {repeat} {next(_SERIAL)}", provider="fake",
        model_snapshot="fake-1", temperature=None, seed=repeat, persona_id=persona,
        criterion_id="", policy_ids=(policy,), policy_labels=(policy,), spec_id="s",
        repeat=repeat, criterion_ids=CRITERIA, cell_id=cell,
    )  # fmt: skip
    text = json.dumps(
        {"ratings": [{"criterion": c, "score": scores[c], "rationale": "r"} for c in CRITERIA]}
    )
    return StoredRow(
        job_id=job.job_id, status=status, attempt=1, provider="fake", model_snapshot="fake-1",
        temperature=None, seed=job.seed, timestamp="t", request=job.to_dict(),
        response={"text": text} if status == "ok" else None, usage={}, batch_id="b",
    )  # fmt: skip


def _scores(policy, edits):
    out = {c: PUBLISHED.scores.get(c, {}).get(policy, 50.0) for c in CRITERIA}
    out["political_support"] = POLITICAL[policy]
    out.update({c: v for (c, p), v in edits.items() if p == policy})
    return out


@pytest.fixture(scope="module")
def store_file(tmp_path_factory):
    """B (3 repeats; UBS tops Full Transformation in repeat 1); Q1 (2 repeats; blinding puts
    SAWF above UBC on Ownership); Q4 (2 repeats, identical to B's typical run)."""
    path = tmp_path_factory.mktemp("store") / "rows.jsonl"
    s = JsonlResultStore(path)
    blind = {("ownership_of_gains", "ubc"): 60.0, ("ownership_of_gains", "sawf"): 70.0}
    plan = {
        "B": [{}, {("full_transformation", "ubs"): 99.0}, {}],
        "Q1": [blind, blind],
        "Q4": [{}, {}],
    }
    for cell, repeats in plan.items():
        for repeat, edits in enumerate(repeats):
            for persona in PERSONAS:
                for policy in POLICIES:
                    s.append(_row(cell, persona, policy, _scores(policy, edits), repeat=repeat))
    s.append(_row("Q4", "p0", "ubc", _scores("ubc", {}), status="failed"))
    return path


@pytest.fixture(scope="module")
def store(store_file):
    return JsonlResultStore(store_file)


@pytest.fixture(scope="module")
def report(store):
    return run_recommendations(store, net_approval=PUBLISHED.scores[NET_APPROVAL])


def test_run_recommendations_per_cell(report):
    assert report.cell_order == ["B", "Q1", "Q4"]
    b, q1, q4 = (report.results[c] for c in report.cell_order)
    assert b.mean.clauses["sequence"].holds and b.flip_count("sequence") == 1
    assert b.flip_count("a") == 1 and b.flip_count("b") == 0
    assert q1.mean_flipped("b") is True and q1.flip_count("b") == 2
    assert q1.mean.clauses["sequence"].holds  # blinding here touches ownership only
    assert q4.mean_flipped("a") is False and q4.flip_count("a") == 0
    assert q1.mean.consistency.nit_despite_low_political is True
    assert sorted(report.noise) == [2]  # B has 3 repeats; cells have 2
    assert report.counts["Q4"].not_ok_jobs == 1


def test_markdown_reports_sequence_consistency_blinding_and_wording(report):
    text = render_markdown(report, "results/raw/rows.jsonl")
    assert "NON-INFERENCE" not in text
    assert "three-stage sequence" in text.lower()
    assert "UBS" in text and "political support" in text.lower()
    assert "Ownership of Gains" in text and "Sovereign AI Fund" in text
    assert "lack the claimed precision, not that the recommendations are wrong" in text
    assert "descriptive" in text.lower() and "exploratory" in text.lower()
    assert "tier" in text.lower()  # tier changes: why not computed
    assert "retraining" in text.lower()  # ALMP exclusion stated
    assert "across all cells" in text.lower()
    for cell in ("| B |", "| Q1 |", "| Q4 |"):
        assert cell in text
    assert "-10.0" in text  # Q1's UBC - SAWF gap
    assert "NON-INFERENCE" in render_markdown(report, "results/pilot/rows.jsonl")


def test_markdown_without_cell_b(tmp_path):
    empty = run_recommendations(JsonlResultStore(tmp_path / "none.jsonl"))
    assert "No cell B data" in render_markdown(empty, "results/raw/rows.jsonl")


def test_csvs(report):
    clauses = list(csv.DictReader(io.StringIO(render_clauses_csv(report))))
    assert {"cell_id", "run", "clause", "holds", "margin", "b_holds", "flipped"} <= set(clauses[0])
    q1b = [r for r in clauses if r["cell_id"] == "Q1" and r["clause"] == "b"]
    assert [r["run"] for r in q1b] == ["reference", "mean", "0", "1"]
    assert q1b[1]["flipped"] == "True"
    cons = list(csv.DictReader(io.StringIO(render_consistency_csv(report))))
    assert {"ubs_leads", "nit_political_rank", "leaders_moderate_disruption"} <= set(cons[0])
    blind = list(csv.DictReader(io.StringIO(render_blinding_csv(report))))
    q1 = next(r for r in blind if r["cell_id"] == "Q1" and r["run"] == "mean")
    assert float(q1["gap"]) == pytest.approx(-10.0) and float(q1["change_vs_b"]) == pytest.approx(
        -50.0
    )
    noise = list(csv.DictReader(io.StringIO(render_noise_csv(report))))
    assert {r["k"] for r in noise} == {"2"} and {"clause", "flip_fraction"} <= set(noise[0])


def test_cli_analyze_recommendations_writes_report(tmp_path, store_file, capsys):
    (tmp_path / "config.yaml").write_text(
        f"max_spend_usd: 0\npaths:\n  raw_store: {store_file}\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "recommendations",
            "--out", str(out), "--published",
            str(ROOT / "analysis/published/paper_table4.csv")]  # fmt: skip

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    assert "NON-INFERENCE" in (out / "recommendations.md").read_text()
    for name in ("recommendation_clauses.csv", "recommendation_consistency.csv",
                 "recommendation_blinding.csv", "recommendation_noise.csv"):  # fmt: skip
        assert (out / name).exists()
    assert "recommendations.md" in capsys.readouterr().out
