"""CLAUDE SUBAGENT ARM CLI (TASK-35): refuses results/raw, prepares, hands out prompts, ingests."""

import json
import shutil
from pathlib import Path

import pytest

from subagent_arm.cli import load_arm, main

REPO = Path(__file__).parents[2]


@pytest.fixture
def project(tmp_path):
    """A copy of the arm's config in a temp dir, pointing back at the repo's inputs."""
    cfg = (REPO / "subagent_arm/config.subagent.yaml").read_text(encoding="utf-8")
    cfg = cfg.replace("../", f"{REPO}/").replace("k_c: 3", "k_c: 1")
    path = tmp_path / "config.subagent.yaml"
    path.write_text(cfg, encoding="utf-8")
    return path


def test_committed_config_is_the_arms_own_store_and_baseline_from_the_design():
    config, baseline, k_c, ws = load_arm(REPO / "subagent_arm/config.subagent.yaml")
    assert config.spend.max_spend_usd == 0 and not config.approved_providers
    assert config.raw_store == REPO / "subagent_arm/results/rows.jsonl"
    assert (baseline.persona_source, baseline.evidence, k_c) == ("named", "wikipedia", 3)
    assert ws.root == REPO / "subagent_arm/work"


def test_a_store_under_results_raw_is_refused(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text(
        "max_spend_usd: 0\npaths:\n  raw_store: results/raw/rows.jsonl\n"
        "subagent_arm:\n  design: x.yaml\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="results/raw"):
        load_arm(bad)
    assert main(["--config", str(bad), "status"]) == 2


def test_prepare_next_discard_ingest_status_round_trip(project, capsys):
    cfg = ["--config", str(project)]
    assert main([*cfg, "prepare"]) == 0
    work = project.parent / "work"
    assert len(list((work / "tasks").glob("*.txt"))) == 561
    capsys.readouterr()
    assert main([*cfg, "next", "--limit", "2"]) == 0
    first, second = (json.loads(ln) for ln in capsys.readouterr().out.splitlines())
    assert first["attempt"] == 1 and "Read the file" in first["prompt"]
    answers = work / "answers"
    answers.mkdir()
    (answers / f"{first['job_id']}.a1.json").write_text("not json", encoding="utf-8")
    assert main([*cfg, "discard", f"{second['job_id']}:1"]) == 0
    capsys.readouterr()
    assert main([*cfg, "ingest"]) == 0
    assert "invalid (retry pending) 2" in capsys.readouterr().out
    assert main([*cfg, "next", "--limit", "2"]) == 0
    retries = [json.loads(ln) for ln in capsys.readouterr().out.splitlines()]
    assert [(r["job_id"], r["attempt"]) for r in retries] == [
        (first["job_id"], 2),
        (second["job_id"], 2),
    ]
    assert main([*cfg, "status"]) == 0
    assert "still to run 561" in capsys.readouterr().out
    shutil.rmtree(work)
