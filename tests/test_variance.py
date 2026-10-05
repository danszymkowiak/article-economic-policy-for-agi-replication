"""TASK-20: variance decomposition report from synthetic raw-store rows. Offline."""

import csv
import io
import itertools
import json

import numpy as np
import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.variance import (
    render_agreement_csv,
    render_components_csv,
    render_markdown,
    render_persona_cells_csv,
    render_shifts_csv,
    run_variance,
)
from llm_panel.bootstrap.cli import main
from llm_panel.domain.analysis_baseline import TABLE4_CRITERIA
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import StoredRow

CRITERIA = (*TABLE4_CRITERIA, "political_support", "admin_capacity_speed")
POLICIES = tuple(f"pol{i:02d}" for i in range(11))
PERSONAS = tuple(f"p{i:02d}" for i in range(12))
_SERIAL = itertools.count()


def _row(cell, persona, policy, scores, *, repeat=0, status="ok"):
    job = RenderedJob(
        prompt=f"{cell} {persona} {policy} {repeat} {next(_SERIAL)}", provider="fake",
        model_snapshot="fake-1", temperature=None, seed=repeat, persona_id=persona,
        criterion_id="", policy_ids=(policy,), policy_labels=(policy,), spec_id="s",
        repeat=repeat, criterion_ids=CRITERIA, cell_id=cell,
    )  # fmt: skip
    text = json.dumps(
        {
            "ratings": [
                {"criterion": c, "score": float(s), "rationale": "r"}
                for c, s in zip(CRITERIA, scores, strict=True)
            ]
        }  # fmt: skip
    )
    return StoredRow(
        job_id=job.job_id, status=status, attempt=1, provider="fake", model_snapshot="fake-1",
        temperature=None, seed=job.seed, timestamp="t", request=job.to_dict(),
        response={"text": text} if status == "ok" else None, usage={}, batch_id="b",
    )  # fmt: skip


@pytest.fixture
def store(tmp_path):
    """B (4 repeats) with planted persona effects; Q1 identical in distribution; Q4 shifted."""
    rng = np.random.default_rng(0)
    persona = rng.normal(0, 8, len(PERSONAS))
    truth = rng.normal(50, 10, (len(POLICIES), len(CRITERIA)))
    shift = rng.normal(0, 6, (len(POLICIES), len(CRITERIA)))
    s = JsonlResultStore(tmp_path / "rows.jsonl")
    for cell, k, extra in (("B", 4, 0.0), ("Q1", 2, 0.0), ("Q4", 2, shift)):
        for repeat in range(k):
            for n, pid in enumerate(PERSONAS):
                for j, pol in enumerate(POLICIES):
                    base = truth[j] + persona[n] + (extra[j] if cell == "Q4" else 0)
                    s.append(_row(cell, pid, pol, base + rng.normal(0, 2, len(CRITERIA)),
                                  repeat=repeat))  # fmt: skip
    s.append(_row("Q1", "p00", "pol00", [0] * len(CRITERIA), status="failed"))
    return s


def test_run_variance_decomposes_cells_and_shifts(store):
    report = run_variance(store)
    assert report.cell_order == ["B", "Q1", "Q4"]
    b = report.decompositions["B"]
    assert b.n_personas == 12 and b.n_repeats == 4 and b.n_criteria == len(CRITERIA)
    assert 0.2 < b.persona_main_share < 0.6  # persona var 64 vs policy x criterion ~100
    shifts = {f.cell_id: f for f in report.shifts}
    assert set(shifts) == {"Q1", "Q4"}
    assert shifts["Q4"].ratio_to_noise > max(shifts["Q4"].band)
    assert shifts["Q1"].ratio_to_noise < shifts["Q4"].ratio_to_noise
    assert len(report.persona_cells["B"]) == len(POLICIES) * len(CRITERIA)
    assert len(report.agreement["B"]) == len(CRITERIA)
    assert report.precision.n_runs == 4
    assert report.precision.n_units == len(POLICIES) * len(TABLE4_CRITERIA)
    assert (
        0 < sorted(report.precision.sds)[len(report.precision.sds) // 2] < 2
    )  # noise sd 2 / sqrt(12)


def test_markdown_states_persona_share_neff_identifiability_and_wording(store):
    report = run_variance(store)
    text = render_markdown(report, "results/raw/rows.jsonl")
    assert "NON-INFERENCE" not in text
    assert "persona explains" in text.lower()
    assert "n_eff = n / (1 + (n - 1) icc)" in text
    assert "not identifiable" in text.lower() and "interaction" in text.lower()
    assert "lack the claimed precision, not that the recommendations are wrong" in text
    assert "descriptive" in text.lower()
    assert "Q4" in text and "evidence" in text.lower()
    assert "## Precision of a panel mean" in text
    assert "0.05 points" in text
    assert "NON-INFERENCE" in render_markdown(report, "results/pilot/rows.jsonl")


def test_markdown_without_cell_b(tmp_path):
    report = run_variance(JsonlResultStore(tmp_path / "rows.jsonl"))
    assert "No cell B data" in render_markdown(report, "results/raw/rows.jsonl")


def test_csvs(store):
    report = run_variance(store)
    comps = list(csv.DictReader(io.StringIO(render_components_csv(report))))
    assert {r["cell_id"] for r in comps} == {"B", "Q1", "Q4"}
    assert sum(r["cell_id"] == "B" for r in comps) == 15  # 2^4 - 1 terms
    assert {"term", "df", "mean_square", "estimate", "share"} <= set(comps[0])
    cells = list(csv.DictReader(io.StringIO(render_persona_cells_csv(report))))
    assert {"persona_share", "icc_run", "n_eff_run"} <= set(cells[0])
    agree = list(csv.DictReader(io.StringIO(render_agreement_csv(report))))
    assert {"icc_agree", "n_eff_agree"} <= set(agree[0])
    shifts = list(csv.DictReader(io.StringIO(render_shifts_csv(report))))
    assert [r["cell_id"] for r in shifts] == ["Q1", "Q4"]
    assert shifts[1]["factor"].startswith("evidence")


def test_cli_analyze_variance_writes_report(tmp_path, store, capsys):
    (tmp_path / "config.yaml").write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: rows.jsonl\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "variance", "--out", str(out)]

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    assert "NON-INFERENCE" in (out / "variance.md").read_text()
    for name in ("variance_components.csv", "variance_persona_cells.csv",
                 "variance_agreement.csv", "variance_factor_shifts.csv"):  # fmt: skip
        assert (out / name).exists()
    assert "variance.md" in capsys.readouterr().out
