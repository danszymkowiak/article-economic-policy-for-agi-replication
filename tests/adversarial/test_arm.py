"""ADVERSARIAL ARM (TASK-22): end to end with the fake client in a temp project.

The fake client answers from a planted ground truth on the primary composite (Full Transformation):
UBC 80, SAWF 60, NIT 50, UI 40, plus a small persona effect and hash noise (sd 1). Planted
vulnerability, on UBC's prompts only:
- the wording edit "does better" -> "performs better" costs UBC 35 points (rank 3 of 4, not last);
- with it, temperature 0 costs 20 more, and so does keeping only the first half of UBC's packet.
So no single perturbation moves UBC from top to bottom; the greedy search must take the wording
edit at depth 1 and find two successful pairs at depth 2, choosing the smaller (temperature: no
prompt characters). Offline; no paid calls; never touches results/raw.
"""

import csv
import glob
import hashlib
import random
import shutil
from pathlib import Path

import pytest
import yaml

from adversarial.cli import load_arm_config, main
from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.application.spend import compute_spend
from llm_panel.bootstrap.config import external_spend, load_config

REPO = Path(__file__).parents[2]
SNAP = "fake-model-2026-01-01"
FULL, OWN = "full_transformation", "ownership_of_gains"
TRUTH = {"ubc": 80.0, "sawf": 60.0, "nit": 50.0, "ui": 40.0}
EFFECTS = (-2.0, -1.0, 0.0, 0.0, 1.0, 2.0)
SECTIONS = ("alpha", "beta", "gamma", "delta")
HEADER = "# ADVERSARIAL ARM — not pooled with the main analysis"


def planted_score(job, criterion) -> float:
    policy = job.policy_ids[0]
    persona = EFFECTS[int(job.persona_id.split("_")[1])]
    seed = int.from_bytes(hashlib.sha256(f"{job.job_id}|{criterion}".encode()).digest()[:8], "big")
    score = TRUTH[policy] + persona + random.Random(seed).gauss(0, 1.0)
    if criterion == FULL and policy == "ubc" and "performs better" in job.prompt:
        score -= 35
        if job.temperature == 0.0:
            score -= 20
        if "ubc gamma" not in job.prompt:  # only the first half of UBC's packet is left
            score -= 20
    return round(min(100.0, max(0.0, score)), 1)


def _make_project(root: Path, *, ceiling: float = 1.5, **arm) -> Path:
    inputs = root / "inputs"
    (inputs / "personas").mkdir(parents=True)
    personas = [{"id": f"named_{i}", "description": f"economist {i}"} for i in range(6)]
    (inputs / "personas" / "named.yaml").write_text(yaml.safe_dump({"personas": personas}))
    policies = [{"id": p, "name": p.upper(), "description": f"{p} policy", "blinded_description":
                 f"{p} policy"} for p in TRUTH]  # fmt: skip
    (inputs / "policies.yaml").write_text(yaml.safe_dump(policies))
    criteria = [{"id": FULL, "name": "Full Transformation", "description": "x"},
                {"id": OWN, "name": "Ownership of Gains", "description": "y"}]  # fmt: skip
    (inputs / "criteria.yaml").write_text(yaml.safe_dump(criteria))
    packets = root / "packets"
    packets.mkdir()
    for p in TRUTH:
        body = "\n\n".join(f"## {s}\n{p} {s} finding." for s in SECTIONS)
        (packets / f"{p}.md").write_text(f"# Evidence packet: {p}\n\nSource: wiki.\n\n{body}\n")
    shutil.copytree(REPO / "prompts", root / "prompts")
    study = {"max_spend_usd": 15, "approved_providers": ["fake"],
             "paths": {"raw_store": "results/raw/rows.jsonl", "ledger": "results/batches.jsonl"},
             "prices": {SNAP: {"input": 1.0, "output": 5.0}}}  # fmt: skip
    (root / "config.yaml").write_text(yaml.safe_dump(study))
    adv = root / "adversarial"
    adv.mkdir()
    settings = {
        "catalogue_version": "adv-catalogue-v1",
        "baseline": {"model": {"provider": "fake", "snapshot": SNAP}, "temperature": None,
                     "persona_source": "named", "evidence": "wikipedia"},
        "search_personas": 4, "panel_seed": 7, "seed": 0, "noise_seed": 1,
        "primary_composite": FULL, "max_depth": 2, "max_candidates": 30, **arm,
    }  # fmt: skip
    cfg = {
        "max_spend_usd": ceiling,
        "approved_providers": ["fake"],
        "counts_spend_from": ["../config*.yaml"],
        "paths": {"raw_store": "results/rows.jsonl", "ledger": "results/ledger.jsonl",
                  "inputs_dir": "../inputs", "prompts_dir": "../prompts",
                  "evidence_packets": {"wikipedia": "../packets"}},
        "prices": {SNAP: {"input": 1.0, "output": 5.0}},
        "adversarial": settings,
    }  # fmt: skip
    path = adv / "config.adversarial.yaml"
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True))
    return path


def _runner(config: Path):
    client = FakeModelClient(job_scorer=planted_score)

    def run(*args):
        argv = ["--config", str(config), *args]
        return main(argv, client_factory=lambda provider: client, now=lambda: "2026-10-04T00:00Z")

    return run


def _search_to_the_end(run, rounds=8):
    for _ in range(rounds):
        assert run("submit", "--confirm") == 0
        assert run("collect") == 0


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("adv")
    config = _make_project(root)
    run = _runner(config)
    _search_to_the_end(run)
    assert run("report", "--out", str(root / "adversarial")) == 0
    return root


def _candidates(root):
    with (root / "adversarial" / "candidates.csv").open() as fh:
        return list(csv.DictReader(fh))


def test_search_finds_the_planted_pair_and_reports_the_smallest(project):
    report = (project / "adversarial" / "report.md").read_text()
    assert report.splitlines()[0] == HEADER
    assert "Status: **found**" in report
    assert "`w_higher_better+t_0`" in report
    assert "Target policy: `ubc`" in report
    rows = {r["candidate"]: r for r in _candidates(project)}
    wins = {k for k, r in rows.items() if r["top_to_bottom"] == "yes"}
    assert wins == {"w_higher_better+t_0", "w_higher_better+e_keep_first_half"}
    assert rows["w_higher_better+t_0"]["winner"] == "yes"
    assert rows["w_higher_better"]["target_rank"] == "3.0"
    assert int(rows["w_higher_better+t_0"]["prompt_chars"]) < int(
        rows["w_higher_better+e_keep_first_half"]["prompt_chars"]
    )


def test_every_candidate_tried_is_logged_with_the_count(project):
    rows = _candidates(project)
    assert len(rows) == 14 + 13  # every depth-1 entry, then the chosen one with each other slot
    assert len({r["candidate"] for r in rows}) == len(rows)
    assert {r["depth"] for r in rows} == {"1", "2"}
    report = (project / "adversarial" / "report.md").read_text()
    assert "Candidates tried: **27**" in report
    assert "baseline rerun" in report.lower()  # repeat-noise reference for the target's rank


def test_adversarial_rows_stay_in_their_own_store_never_results_raw(project):
    # counting the study ledger toward the global cap opens the study store read-only (the JSONL
    # adapter creates its empty folder); nothing is ever written there
    assert not [p for p in (project / "results").rglob("*") if p.is_file()]
    rows = list(JsonlResultStore(project / "adversarial" / "results" / "rows.jsonl").iter_rows())
    assert rows and all(r.request["cell_id"].startswith("ADV:") for r in rows)
    assert {r.status for r in rows} == {"ok"}


def test_rerunning_after_the_search_stopped_submits_nothing(project, capsys):
    run = _runner(project / "adversarial" / "config.adversarial.yaml")
    ledger = JsonlBatchLedger(project / "adversarial" / "results" / "ledger.jsonl")
    before = len(ledger.entries())
    assert run("submit", "--confirm") == 0
    assert len(ledger.entries()) == before
    assert "nothing to submit" in capsys.readouterr().out


def test_submit_needs_confirm(tmp_path, capsys):
    run = _runner(_make_project(tmp_path))
    assert run("submit") == 2
    assert "--confirm" in capsys.readouterr().err
    assert not (tmp_path / "adversarial" / "results" / "ledger.jsonl").exists()


def test_search_respects_the_depth_cap(tmp_path):
    config = _make_project(tmp_path, max_depth=1)
    run = _runner(config)
    _search_to_the_end(run)
    assert run("report", "--out", str(tmp_path / "out")) == 0
    report = (tmp_path / "out" / "report.md").read_text()
    assert "Status: **depth exhausted**" in report
    with (tmp_path / "out" / "candidates.csv").open() as fh:
        assert {r["depth"] for r in csv.DictReader(fh)} == {"1"}


def test_search_respects_the_budget_and_stops_inside_the_ceiling(tmp_path):
    ceiling = 0.08
    config = _make_project(tmp_path, ceiling=ceiling)
    run = _runner(config)
    _search_to_the_end(run, rounds=12)
    cfg = load_config(config)
    spend = compute_spend(JsonlResultStore(cfg.raw_store), JsonlBatchLedger(cfg.ledger), cfg.spend)
    assert spend.outstanding == 0 and 0 < spend.actual <= ceiling
    assert run("report", "--out", str(tmp_path / "out")) == 0
    report = (tmp_path / "out" / "report.md").read_text()
    assert "Status: **budget exhausted**" in report
    with (tmp_path / "out" / "candidates.csv").open() as fh:
        tried = list(csv.DictReader(fh))
    assert 0 < len(tried) < 14  # stopped inside depth 1, and what ran is still logged


def test_plan_is_read_only(tmp_path, capsys):
    config = _make_project(tmp_path)

    def no_client(provider):
        raise AssertionError("plan must not build a client")

    assert main(["--config", str(config), "plan"], client_factory=no_client) == 0
    out = capsys.readouterr().out
    assert "baseline" in out and "jobs to submit: 32" in out  # 4 personas x 4 policies, twice
    assert not (tmp_path / "adversarial" / "results" / "ledger.jsonl").exists()


def test_config_refuses_the_study_store(tmp_path):
    config = _make_project(tmp_path)
    data = yaml.safe_load(config.read_text())
    data["paths"]["raw_store"] = "../results/raw/rows.jsonl"
    config.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="results/raw"):
        load_arm_config(config)


def test_config_refuses_a_deeper_search_or_another_catalogue(tmp_path):
    bad_settings = ({"max_depth": 3}, {"catalogue_version": "adv-catalogue-v0"},
                    {"max_candidates": 31})  # fmt: skip
    for i, bad in enumerate(bad_settings):
        with pytest.raises(ValueError):
            load_arm_config(_make_project(tmp_path / f"p{i}", **bad))


# --- the committed adversarial config and directory ---

ADV_CONFIG = REPO / "adversarial" / "config.adversarial.yaml"


def test_committed_config_has_its_own_store_ceiling_and_counts_global_spend():
    cfg, settings = load_arm_config(ADV_CONFIG)
    assert cfg.spend.max_spend_usd == 1.5
    assert cfg.raw_store.resolve().is_relative_to((REPO / "adversarial" / "results").resolve())
    assert cfg.ledger.resolve().is_relative_to((REPO / "adversarial" / "results").resolve())
    matched = {Path(p).resolve() for pat in cfg.counts_spend_from for p in glob.glob(str(pat))}
    assert (REPO / "config.yaml").resolve() in matched
    external_spend(cfg)  # every counted ledger is readable (fails closed otherwise)
    assert settings.max_depth == 2 and settings.primary_composite == FULL
    # and the study config counts the adversarial ledger toward the global 15 USD
    main_cfg = load_config(REPO / "config.yaml")
    counted = {Path(p).resolve() for pat in main_cfg.counts_spend_from for p in glob.glob(str(pat))}
    assert ADV_CONFIG.resolve() in counted


def test_committed_config_plans_offline_against_the_study_materials(capsys):
    def no_client(provider):
        raise AssertionError("plan must not build a client")

    assert main(["--config", str(ADV_CONFIG), "plan"], client_factory=no_client) == 0
    assert "ADVERSARIAL" in capsys.readouterr().out


def test_directory_is_labeled_adversarial():
    readme = (REPO / "adversarial" / "README.md").read_text()
    assert readme.startswith("# ADVERSARIAL ARM")
    assert "not pooled" in readme
