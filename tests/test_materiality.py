"""TASK-28: materiality-shift report (prereg s6 item 2) from synthetic raw-store rows. Offline."""

import csv
import io

import numpy as np
import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.materiality import (
    render_counts_csv,
    render_markdown,
    render_units_csv,
    run_materiality,
)
from llm_panel.bootstrap.cli import main
from tests.test_variance import CRITERIA, PERSONAS, POLICIES, _row

UP = (3, 0)  # policy index, criterion index shifted up by 10 in Q1


@pytest.fixture(scope="module")
def store_dir(tmp_path_factory):
    """B (4 repeats); Q1 (2 repeats) with one unit planted +10; Q4 (2 repeats) unchanged."""
    tmp_path = tmp_path_factory.mktemp("materiality")
    rng = np.random.default_rng(5)
    persona = rng.normal(0, 8, len(PERSONAS))
    truth = rng.normal(50, 10, (len(POLICIES), len(CRITERIA)))
    s = JsonlResultStore(tmp_path / "rows.jsonl")
    for cell, k in (("B", 4), ("Q1", 2), ("Q4", 2)):
        for repeat in range(k):
            for n, pid in enumerate(PERSONAS):
                for j, pol in enumerate(POLICIES):
                    base = truth[j] + persona[n]
                    if cell == "Q1" and j == UP[0]:
                        base = base + np.eye(len(CRITERIA))[UP[1]] * 10
                    s.append(_row(cell, pid, pol, base + rng.normal(0, 2, len(CRITERIA)),
                                  repeat=repeat))  # fmt: skip
    s.append(_row("Q1", "p00", "pol00", [0] * len(CRITERIA), status="failed"))
    return tmp_path


@pytest.fixture
def store(store_dir):
    return JsonlResultStore(store_dir / "rows.jsonl")


def test_run_materiality_counts_the_planted_unit_only(store):
    report = run_materiality(store)
    assert report.cell_order == ["B", "Q1", "Q4"]
    by_cell = {m.cell_id: m for m in report.results}
    q1, q4 = by_cell["Q1"], by_cell["Q4"]
    assert q1.n_units == len(POLICIES) * len(CRITERIA)
    assert q1.counts[5.0] == 1 and q4.counts[5.0] == 0
    (unit,) = [u for u in q1.units if u.beyond(5.0)]
    assert (unit.policy_id, unit.criterion) == (POLICIES[UP[0]], CRITERIA[UP[1]])
    assert unit.shift == pytest.approx(10, abs=2) and unit.noise_multiple > 5
    assert set(q4.band[5.0]) == {0}


def test_markdown_states_primary_m_sensitivity_and_wording(store):
    report = run_materiality(store)
    text = render_markdown(report, "results/raw/rows.jsonl")
    assert "NON-INFERENCE" not in text
    assert "M = 5" in text and "primary" in text.lower()
    assert "sensitivity" in text.lower() and "not used to pick M" in text
    assert "lack the claimed precision, not that the recommendations are wrong" in text
    assert f"{POLICIES[UP[0]]} x {CRITERIA[UP[1]]}" in text
    assert "NON-INFERENCE" in render_markdown(report, "results/smoketest/rows.jsonl")


def test_markdown_without_cell_b(tmp_path):
    report = run_materiality(JsonlResultStore(tmp_path / "rows.jsonl"))
    assert "No cell B data" in render_markdown(report, "results/raw/rows.jsonl")


def test_csvs(store):
    report = run_materiality(store)
    counts = list(csv.DictReader(io.StringIO(render_counts_csv(report))))
    assert [(r["cell_id"], r["m"]) for r in counts] == [
        (c, m) for c in ("Q1", "Q4") for m in ("3", "5", "8")
    ]
    primary = {r["cell_id"]: r for r in counts if r["primary"] == "True"}
    assert primary["Q1"]["count"] == "1" and primary["Q4"]["count"] == "0"
    assert {"n_units", "noise_se", "band_min", "band_max", "n_splits"} <= set(counts[0])
    units = list(csv.DictReader(io.StringIO(render_units_csv(report))))
    assert len(units) == 2 * len(POLICIES) * len(CRITERIA)
    assert {"shift", "noise_multiple", "beyond_5"} <= set(units[0])


def test_cli_analyze_materiality_writes_report(store_dir, capsys):
    tmp_path = store_dir
    (tmp_path / "config.yaml").write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: rows.jsonl\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "materiality", "--out", str(out)]

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    assert "NON-INFERENCE" in (out / "materiality.md").read_text()
    assert (out / "materiality_counts.csv").exists() and (out / "materiality_units.csv").exists()
    assert "materiality.md" in capsys.readouterr().out
