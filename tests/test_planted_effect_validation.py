"""TASK-28: the analysis recovers a planted effect and stays quiet on null factors.

A tiny one-at-a-time design goes plan -> fake submit -> collect -> analyze in a temp project with
its own non-inference store. The fake client answers from a planted ground truth:

    score = truth[policy][criterion] + persona effect (zero mean) + noise (sd 3, from a hash),

and in cell Q1 (policy identifier removed) only, SAWF's Ownership of Gains is shifted by +12, which
lifts it above UBC (the paper's blinding question, clause (b)). No other cell changes anything.
Rank stability, variance decomposition, recommendation clauses and materiality shifts must find
the Q1 shift with the right sign and size and report every other cell as negligible.
Offline; no paid calls; never touches results/raw.
"""

import hashlib
import random
import shutil
from pathlib import Path

import pytest
import yaml

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.materiality import run_materiality
from llm_panel.application.rank_stability import run_rank_stability
from llm_panel.application.recommendations import run_recommendations
from llm_panel.application.variance import run_variance
from llm_panel.bootstrap.cli import main

REPO = Path(__file__).parents[1]
SNAP = "fake-model-2026-01-01"
OWN, FULL = "ownership_of_gains", "full_transformation"
TRUTH = {
    "ubc": {OWN: 65.0, FULL: 72.0},
    "sawf": {OWN: 58.0, FULL: 55.0},
    "nit": {OWN: 40.0, FULL: 45.0},
}
PLANTED = ("Q1", "sawf", OWN, 12.0)  # cell, policy, criterion, shift
EFFECTS = (-5.0, -3.0, -1.0, 1.0, 3.0, 5.0)  # per persona, zero mean in each panel
NOISE_SD = 3.0
K_R, K_Q, D2_REPEATS, N_PERSONAS = 4, 2, 8, 6


def planted_score(job, label) -> float:
    if job.criterion_ids:  # persona x policy job: one entry per criterion
        policy, criterion = job.policy_ids[0], label
    else:  # D1 joint job: one entry per policy label
        policy, criterion = job.policy_ids[job.policy_labels.index(label)], job.criterion_id
    persona = 0.0 if job.persona_id == "none" else EFFECTS[int(job.persona_id.split("_")[1])]
    seed = int.from_bytes(hashlib.sha256(f"{job.job_id}|{label}".encode()).digest()[:8], "big")
    score = TRUTH[policy][criterion] + persona + random.Random(seed).gauss(0, NOISE_SD)
    if (job.cell_id, policy, criterion) == PLANTED[:3]:
        score += PLANTED[3]
    return round(min(100.0, max(0.0, score)), 1)


def _personas(source):
    return {"personas": [{"id": f"{source}_{i}", "description": f"{source} economist {i}"}
                         for i in range(N_PERSONAS)]}  # fmt: skip


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("planted")
    inputs = root / "inputs"
    (inputs / "personas").mkdir(parents=True)
    for source in ("named", "reconstructed"):
        (inputs / "personas" / f"{source}.yaml").write_text(yaml.safe_dump(_personas(source)))
    policies = [
        {"id": "ubc", "name": "Universal Basic Capital (UBC)", "description": "A stake for all."},
        {"id": "sawf", "name": "Sovereign AI Wealth Fund (SAWF)", "description": "A fund."},
        {"id": "nit", "name": "Negative Income Tax (NIT)", "description": "Cash below a line."},
    ]
    for p in policies:
        p["blinded_description"] = p["description"]
    (inputs / "policies.yaml").write_text(yaml.safe_dump(policies))
    criteria = [{"id": OWN, "name": "Ownership of Gains", "description": "x"},
                {"id": FULL, "name": "Full Transformation", "description": "y"}]  # fmt: skip
    (inputs / "criteria.yaml").write_text(yaml.safe_dump(criteria))
    paras = inputs / "description_paraphrases"
    paras.mkdir()
    for lv in ("para_1", "para_2", "para_3"):
        (paras / f"{lv}.yaml").write_text(yaml.safe_dump({p["id"]: f"{p['id']} {lv}"
                                                          for p in policies}))  # fmt: skip
    packets = root / "packets"
    packets.mkdir()
    for p in policies:
        (packets / f"{p['id']}.md").write_text(
            f"# Evidence packet: {p['name']}\n\nStudies of {p['name']} found effects.\n"
        )
    shutil.copytree(REPO / "prompts", root / "prompts")
    # fixed survey input (net approval) the recommendations analysis reads
    shutil.copytree(REPO / "analysis" / "published", root / "analysis" / "published")
    cfg = {
        "max_spend_usd": 15,
        "approved_providers": ["fake"],
        "paths": {
            # a non-inference store of its own, never results/raw
            "raw_store": "results/smoketest/rows.jsonl", "ledger": "results/smoketest/ledger.jsonl",
            "inputs_dir": "inputs", "prompts_dir": "prompts",
            "evidence_packets": {"wikipedia": "packets"},
        },
        "prices": {SNAP: {"input": 1.0, "output": 5.0}, "fake-2": {"input": 1.0, "output": 5.0}},
    }  # fmt: skip
    (root / "config.validation.yaml").write_text(yaml.safe_dump(cfg))
    study = {**cfg, "paths": {**cfg["paths"], "raw_store": "results/raw/rows.jsonl",
                              "ledger": "results/raw/ledger.jsonl"}}  # fmt: skip
    (root / "config.yaml").write_text(yaml.safe_dump(study))
    design = yaml.safe_load((REPO / "designs" / "one_at_a_time_fake.yaml").read_text())
    design.update(k_r=K_R, k_q=K_Q, d2_repeats=D2_REPEATS, n_personas=N_PERSONAS)
    design["d_cells"]["D3"] = {"model": {"provider": "fake", "snapshot": "fake-2"}}
    (root / "design.yaml").write_text(yaml.safe_dump(design))

    client = FakeModelClient(job_scorer=planted_score)

    def run(*args):
        argv = ["--config", str(root / "config.validation.yaml"), *args]
        return main(argv, client_factory=lambda provider: client, now=lambda: "2026-10-04T00:00Z")

    assert run("plan", "--design", str(root / "design.yaml")) == 0
    assert run("submit", "--confirm", "--design", str(root / "design.yaml")) == 0
    assert run("collect") == 0
    return root


@pytest.fixture(scope="module")
def store(project):
    return JsonlResultStore(project / "results" / "smoketest" / "rows.jsonl")


NULL_CELLS = ("B'", "R-T0", "R-T1", "Q2a", "Q2b", "Q2c", "Q3a", "Q3b", "Q3c", "Q4",
              "D1", "D2", "D2b", "D3")  # fmt: skip


def test_pipeline_stored_every_cell_and_left_results_raw_alone(project, store):
    rows = list(store.iter_rows())
    assert rows and {r.status for r in rows} == {"ok"}
    assert {r.request["cell_id"] for r in rows} == {"B", "Q1", *NULL_CELLS}
    assert not (project / "results" / "raw").exists()


def test_materiality_counts_the_planted_unit_only(store):
    report = {m.cell_id: m for m in run_materiality(store).results}
    q1 = report["Q1"]
    assert q1.counts[5.0] == 1 and q1.counts[8.0] == 1
    (unit,) = [u for u in q1.units if u.beyond(5.0)]
    assert (unit.policy_id, unit.criterion) == ("sawf", OWN)
    assert unit.shift == pytest.approx(PLANTED[3], abs=2.0)  # sign and approximate size
    assert unit.noise_multiple > 5
    assert all(abs(u.shift) < 3 for u in q1.units if u is not unit)
    for cell in NULL_CELLS:  # null factors: nothing material, nothing beyond the noise floor
        m = report[cell]
        assert m.counts[5.0] == 0 and m.counts[8.0] == 0, cell
        assert all(abs(u.noise_multiple) < 4 for u in m.units), cell
    # M = 3 sits near the noise floor at this scale (about 3 SE): noise alone may cross it, which is
    # why it is a descriptive sensitivity and M = 5 is the primary margin
    assert sum(report[c].counts[3.0] for c in NULL_CELLS) <= 2


def test_variance_shift_stands_out_for_q1_only(store):
    shifts = {f.cell_id: f for f in run_variance(store).shifts}
    q1 = shifts["Q1"]
    # 12 points on one of 6 units: level shift 2, unit-specific shift variance about 24
    assert q1.level_shift == pytest.approx(PLANTED[3] / 6, abs=0.75)
    assert q1.level_shift > 3 * q1.level_se
    assert q1.shift_sd == pytest.approx(PLANTED[3] / 6**0.5, rel=0.25)
    assert q1.ratio_to_noise > 5 and q1.ratio_to_noise > max(q1.band)
    for cell in NULL_CELLS:
        f = shifts[cell]
        assert abs(f.ratio_to_noise) < 3, cell
        assert abs(f.level_shift) < 4 * f.level_se, cell


def test_rank_metrics_move_on_the_planted_criterion_only(store):
    report = run_rank_stability(store, resamples=50, seed=0)
    taus = {(c.cell_id, c.composite): c for c in report.result.comparisons
            if c.aggregation == "mean"}  # fmt: skip
    own = taus[("Q1", OWN)]
    assert own.tau == pytest.approx(1 / 3)  # SAWF and UBC swap; NIT stays last
    assert own.rank_shifts["sawf"] == (2.0, 1.0) and own.rank_shifts["ubc"] == (1.0, 2.0)
    assert taus[("Q1", FULL)].tau == pytest.approx(1.0)
    for cell in NULL_CELLS:
        for criterion in (OWN, FULL):
            assert taus[(cell, criterion)].tau == pytest.approx(1.0), (cell, criterion)


def test_recommendation_clause_b_flips_in_q1_only(store):
    report = run_recommendations(store)
    q1 = report.results["Q1"]
    assert q1.reference.clauses["b"].holds is True
    assert q1.mean.clauses["b"].holds is False and q1.flip_count("b") == K_Q
    assert q1.mean.gap - q1.reference.gap == pytest.approx(-PLANTED[3], abs=2.0)
    assert q1.mean.clauses["a"].holds is True
    for cell in NULL_CELLS:
        r = report.results[cell]
        assert r.mean.clauses["b"].holds is True and r.mean.clauses["a"].holds is True, cell
        if cell != "D2":
            assert r.flip_count("b") == 0, cell
    # D2's single runs are one rating each (noise sd 3 on a 7-point gap), so single-run flips there
    # are repeat noise, the case the prereg's single-run flip count exists for; its mean holds
    assert report.results["D2"].flip_count("b") < D2_REPEATS / 2


def test_cli_reports_label_the_validation_store_non_inference(project):
    config = str(project / "config.validation.yaml")
    for name, extra in (("ranks", ["--resamples", "20"]), ("variance", []),
                        ("materiality", []), ("recommendations", [])):  # fmt: skip
        out = project / "analysis-validation" / name
        assert main(["--config", config, "analyze", name, "--out", str(out), *extra]) == 0
        report = next(out.glob("*.md")).read_text()
        assert "NON-INFERENCE" in report and "No cell B data" not in report


def test_study_analysis_reads_only_results_raw_and_ignores_the_smoketest_store(project):
    """The study config points at results/raw; the planted rows in results/smoketest next to it
    must not enter (TASK-26 AC2 part deferred to here)."""
    config = str(project / "config.yaml")
    for name in ("ranks", "variance", "materiality", "recommendations"):
        out = project / "analysis-study" / name
        assert main(["--config", config, "analyze", name, "--out", str(out)]) == 0
        report = next(out.glob("*.md")).read_text()
        assert "NON-INFERENCE" not in report, name
        assert "No cell B data" in report, name
