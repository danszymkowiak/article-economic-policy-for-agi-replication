"""TASK-37: missing-data report (prereg s7) from synthetic raw-store rows. Offline."""

import csv
import io

import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.missing_data import (
    cell_failures,
    render_csv,
    render_markdown,
    run_missing_data,
)
from llm_panel.bootstrap.cli import main
from llm_panel.domain.analysis_missing import Failure
from tests.test_rank_stability import ASC, CRITERIA, PERSONAS, POLICIES, _row

D2_FAILED = {(0, "pol00"), (0, "pol01"), (1, "pol02")}  # 3 of 22 calls: above 10%


@pytest.fixture
def store(tmp_path):
    s = JsonlResultStore(tmp_path / "rows.jsonl")
    for repeat in (0, 1):
        for persona in PERSONAS:
            for i, policy in enumerate(POLICIES):
                s.append(_row("B", persona, policy, ASC[i], repeat=repeat))
                failed = persona == "p1" and policy == "pol05"
                s.append(_row("Q1", persona, policy, ASC[i], repeat=repeat,
                              status="failed" if failed else "ok"))  # fmt: skip
        for i, policy in enumerate(POLICIES):
            failed = (repeat, policy) in D2_FAILED
            s.append(_row("D2", "none", policy, ASC[i], repeat=repeat,
                          status="failed" if failed else "ok"))  # fmt: skip
    return s


def test_cell_failures_lists_the_ratings_each_failed_call_would_have_given(store):
    fails = cell_failures(store)
    assert sorted(fails["Q1"], key=lambda f: f.repeat) == [
        Failure(0, "p1", ("pol05",), CRITERIA), Failure(1, "p1", ("pol05",), CRITERIA),
    ]  # fmt: skip
    assert len(fails["D2"]) == 3 and fails.get("B", []) == []


def _rows(report, cell):
    return {r.view: r for r in report.rows if r.cell_id == cell}


def test_views_bound_the_shift_a_failure_could_cause(store):
    report = run_missing_data(store)
    q1 = _rows(report, "Q1")
    assert set(q1) == {"common_complete", "survivor", "impute_0", "impute_100"}
    assert q1["common_complete"].beyond == 0 and q1["survivor"].beyond == 0
    # pol05 (45): at 0 each repeat's panel is (45 + 45 + 0) / 3 = 30, a shift of -15
    assert q1["impute_0"].beyond == 11 and q1["impute_0"].max_abs_shift == pytest.approx(15.0)
    assert q1["impute_100"].beyond == 11
    d2 = _rows(report, "D2")
    assert d2["common_complete"].n_units == 121  # no policy lost to a failed call
    assert report.failure_rate["D2"] == pytest.approx(3 / 22)
    assert report.flagged == ["D2"]
    assert _rows(report, "B")["survivor"].beyond == 0


def test_markdown_and_csv(store):
    report = run_missing_data(store)
    text = render_markdown(report, "results/raw/rows.jsonl")
    rule = "lack the claimed precision, not that the recommendations are wrong"
    for phrase in ("survivor-only", "imputed at 0", "imputed at 100", "above 10%", rule):
        assert phrase in text
    assert "NON-INFERENCE" in render_markdown(report, "results/pilot/rows.jsonl")
    rows = list(csv.DictReader(io.StringIO(render_csv(report))))
    assert len(rows) == 3 * 4
    assert {"cell_id", "view", "n_units", "beyond_m", "clause_a", "failure_rate"} <= set(rows[0])


def test_cli_analyze_missing_writes_report(tmp_path, store, capsys):
    (tmp_path / "config.yaml").write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: rows.jsonl\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "missing", "--out", str(out)]

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    assert (out / "missing_data.md").exists() and (out / "missing_data.csv").exists()
    assert "missing_data.md" in capsys.readouterr().out


def test_every_cell_report_states_the_no_persona_rule(store):
    from llm_panel.application import materiality, rank_stability, recommendations, variance
    from llm_panel.application.baseline_comparison import NO_PERSONA_NOTE

    texts = [
        materiality.render_markdown(materiality.run_materiality(store), "results/raw/r.jsonl"),
        rank_stability.render_markdown(
            rank_stability.run_rank_stability(store, resamples=10), "results/raw/r.jsonl"
        ),
        variance.render_markdown(variance.run_variance(store), "results/raw/r.jsonl"),
        recommendations.render_markdown(
            recommendations.run_recommendations(store), "results/raw/r.jsonl"
        ),
    ]
    assert "45" not in NO_PERSONA_NOTE  # generic, not tied to this run's counts
    for text in texts:
        assert NO_PERSONA_NOTE in text
