"""TASK-18: baseline B versus the published scores, from synthetic raw-store rows. Offline."""

import csv
import io
import itertools
import json
from pathlib import Path

import pytest

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.baseline_comparison import (
    baseline_observations,
    render_agreement_csv,
    render_markdown,
    render_policy_csv,
    run_baseline_comparison,
)
from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.published_loader import load_published
from llm_panel.domain.analysis_baseline import COMPOSITES, TABLE4_CRITERIA
from llm_panel.domain.models import RenderedJob
from llm_panel.domain.results import StoredRow

REPO = Path(__file__).parents[1]
PUBLISHED = load_published(REPO / "analysis" / "published" / "paper_table4.csv")
ESSAY = load_published(REPO / "analysis" / "published" / "essay_composites.csv")
CRITERIA = (*TABLE4_CRITERIA, "political_support", "admin_capacity_speed")


_SERIAL = itertools.count()


def _row(persona, policy, scores, *, repeat=0, cell="B", status="ok", text=None):
    job = RenderedJob(
        prompt=f"prompt {persona} {policy} {repeat} {cell} {next(_SERIAL)}", provider="fake",
        model_snapshot="fake-1", temperature=None, seed=repeat, persona_id=persona,
        criterion_id="", policy_ids=(policy,), policy_labels=(policy,), spec_id="s",
        repeat=repeat, criterion_ids=CRITERIA, cell_id=cell,
    )  # fmt: skip
    if text is None:
        text = json.dumps(
            {"ratings": [{"criterion": c, "score": scores(c), "rationale": "r"} for c in CRITERIA]}
        )
    return StoredRow(
        job_id=job.job_id, status=status, attempt=1, provider="fake", model_snapshot="fake-1",
        temperature=None, seed=repeat, timestamp="t", request=job.to_dict(),
        response={"text": text} if status == "ok" else None, usage={}, batch_id="b",
    )  # fmt: skip


def _published_scorer(policy, shift=0.0):
    return lambda c: min(100.0, max(0.0, PUBLISHED.scores.get(c, {}).get(policy, 50.0) + shift))


@pytest.fixture
def store(tmp_path):
    s = JsonlResultStore(tmp_path / "rows.jsonl")
    for repeat in (0, 1):
        for persona, shift in (("p1", -2.0), ("p2", 2.0)):
            for policy in PUBLISHED.policy_order:
                s.append(_row(persona, policy, _published_scorer(policy, shift), repeat=repeat))
    # rows that must not count: another cell, a failed job, a malformed ok row
    s.append(_row("p1", "ubc", lambda c: 0.0, cell="Q1"))
    s.append(_row("p1", "ubc", lambda c: 0.0, cell="B'"))
    s.append(_row("p3", "ubc", lambda c: 0.0, status="failed"))
    s.append(_row("p3", "nit", None, text="not json"))
    return s


def test_observations_come_from_ok_cell_b_rows_only(store):
    observations, counts = baseline_observations(store)
    assert {o.persona_id for o in observations} == {"p1", "p2"}
    assert len(observations) == 2 * 2 * 11 * len(CRITERIA)
    assert counts.ok_jobs == 44
    assert counts.not_ok_jobs == 2  # the failed job and the unparseable ok row


def test_published_scores_reproduce_published_ranks(store):
    result = run_baseline_comparison(store, PUBLISHED)
    assert [a.composite for a in result.agreements] == list(COMPOSITES)
    for a in result.agreements:
        assert a.n_policies == 11
        assert a.spearman == pytest.approx(1.0) and a.kendall_tau_b == pytest.approx(1.0)
        assert a.mean_abs_diff == pytest.approx(0.0, abs=1e-9)
    assert result.panel.n_repeats == 2 and result.panel.n_pairs == 22


def test_markdown_states_rank_agreement_and_the_reconstruction_caveat(store):
    text = render_markdown(run_baseline_comparison(store, PUBLISHED), "results/raw/rows.jsonl")
    assert "rank correlation, not exact match" in text
    assert "may come from our reconstruction as well as from instability" in text
    assert "lack the claimed precision, not that the recommendations are wrong" in text
    assert "SSRN abstract 7470000" in text
    assert "Spearman" in text and "Kendall" in text
    assert "NON-INFERENCE" not in text


def test_markdown_labels_a_store_outside_results_raw_as_non_inference(store):
    text = render_markdown(run_baseline_comparison(store, PUBLISHED), "results/pilot/rows.jsonl")
    assert "NON-INFERENCE" in text


def test_csvs_hold_every_composite_and_policy(store):
    result = run_baseline_comparison(store, PUBLISHED)
    agreement = list(csv.DictReader(io.StringIO(render_agreement_csv(result))))
    assert [r["composite"] for r in agreement] == list(COMPOSITES)
    assert set(agreement[0]) >= {"n_policies", "spearman", "kendall_tau_b", "mean_abs_diff"}
    policy = list(csv.DictReader(io.StringIO(render_policy_csv(result))))
    assert len(policy) == len(COMPOSITES) * 11
    assert set(policy[0]) == {"composite", "policy_id", "ours", "published", "difference"}


def test_cli_analyze_baseline_writes_report(tmp_path, store, capsys):
    (tmp_path / "config.yaml").write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: rows.jsonl\n  ledger: ledger.jsonl\n"
    )
    out = tmp_path / "analysis"
    published = str(REPO / "analysis/published/paper_table4.csv")
    argv = ["--config", str(tmp_path / "config.yaml"), "analyze", "baseline",
            "--published", published, "--out", str(out)]  # fmt: skip

    def no_client(provider):
        raise AssertionError("analyze must not build a client")

    assert main(argv, client_factory=no_client) == 0
    md = (out / "baseline_comparison.md").read_text()
    assert "NON-INFERENCE" in md  # tmp store is not results/raw
    assert (out / "baseline_agreement.csv").exists()
    assert (out / "baseline_policy_scores.csv").exists()
    assert "baseline_comparison.md" in capsys.readouterr().out


ESSAY_COMPOSITES = ("welfare_resilience", "agency_voice", "scenario_durability")


def test_r8_unweighted_means_of_table4_reproduce_the_essay_composites(store):
    result = run_baseline_comparison(store, PUBLISHED, essay=ESSAY)
    assert [a.composite for a in result.r8_check] == list(ESSAY_COMPOSITES)
    for a in result.r8_check:
        assert a.n_policies == 11
        assert max(abs(d) for d in a.differences.values()) < 0.1  # rounding of the printed values
        assert a.spearman == pytest.approx(1.0)


def test_our_baseline_is_compared_with_the_essay_composites(store):
    result = run_baseline_comparison(store, PUBLISHED, essay=ESSAY)
    assert [a.composite for a in result.essay_agreements] == list(ESSAY_COMPOSITES)
    assert all(a.n_policies == 11 for a in result.essay_agreements)
    text = render_markdown(result, "results/raw/rows.jsonl")
    assert "Essay composite tables" in text and "reconstruction R8" in text
    assert "Feasibility is not compared" in text


def test_without_essay_nothing_extra_is_reported(store):
    result = run_baseline_comparison(store, PUBLISHED)
    assert result.r8_check == [] and result.essay_agreements == []
    assert "Essay composite tables" not in render_markdown(result, "results/raw/rows.jsonl")


def test_counts_split_failed_deferred_and_duplicate(store):
    store.append(_row("p4", "ubc", lambda c: 0.0, status="deferred"))
    store.append(_row("p5", "ubc", lambda c: 0.0, status="duplicate"))
    store.append(_row("p5", "ubc", lambda c: 0.0, status="duplicate"))
    _, counts = baseline_observations(store)
    assert counts.ok_jobs == 44 and counts.not_ok_jobs == 2
    assert counts.failed_jobs == 1  # the failed job; the malformed ok row is not "failed"
    assert counts.deferred_jobs == 1 and counts.duplicate_rows == 2
    text = render_markdown(run_baseline_comparison(store, PUBLISHED), "results/raw/rows.jsonl")
    assert "failed 1" in text and "deferred 1" in text and "duplicate rows 2" in text
