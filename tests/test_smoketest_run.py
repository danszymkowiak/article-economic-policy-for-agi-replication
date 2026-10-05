import shutil
from pathlib import Path

import pytest
import yaml

from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.config import load_config

REPO = Path(__file__).parents[1]
SNAP = "fake-model-2026-01-01"
TRUTH = {
    "sm_led_all": 85, "sm_led_closet": 40, "sm_lights_on": 5,
    "sm_charger_a": 55, "sm_charger_b": 57, "sm_thermostat": 45,
}  # fmt: skip
PERVERSE = {**TRUTH, "sm_led_all": 5, "sm_lights_on": 85}


def truth_scorer(table):
    return lambda job_id, label: table[label]


@pytest.fixture
def smoke(tmp_path):
    """The real smoketest inputs and expectations, rerouted to the fake provider in tmp."""
    shutil.copytree(REPO / "designs" / "smoketest", tmp_path / "smoketest")
    design = yaml.safe_load((tmp_path / "smoketest" / "design.yaml").read_text())
    design["factors"]["model"] = [{"provider": "fake", "snapshot": SNAP}]
    (tmp_path / "smoketest" / "design.yaml").write_text(yaml.safe_dump(design))
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "max_spend_usd": 0,
                "approved_providers": ["fake"],
                "prices": {SNAP: {"input": 0.0, "output": 0.0}},
                "paths": {
                    "raw_store": "out/rows.jsonl",
                    "ledger": "out/ledger.jsonl",
                    "inputs_dir": "smoketest/inputs",
                },
            }
        )
    )

    class Smoke:
        root = tmp_path

        def run(self, *args, client):
            argv = ["--config", str(tmp_path / "config.yaml"), *args]
            return main(argv, client_factory=lambda p: client, now=lambda: "2026-10-03T00:00:00Z")

        design = ["--design", str(tmp_path / "smoketest" / "design.yaml")]
        expect = ["--expectations", str(tmp_path / "smoketest" / "expectations.yaml")]

        def store(self):
            return JsonlResultStore(tmp_path / "out" / "rows.jsonl")

    return Smoke()


def test_smoketest_config_is_isolated_from_the_study_and_cannot_spend():
    study = load_config(REPO / "config.yaml")
    smoke = load_config(REPO / "config.smoketest.yaml")
    assert smoke.spend.max_spend_usd <= 0.25
    assert smoke.raw_store != study.raw_store and smoke.ledger != study.ledger
    assert "smoketest" in smoke.raw_store.parts and "smoketest" in smoke.inputs_dir.parts
    assert "smoketest" not in study.inputs_dir.parts


def test_plan_counts_match_the_smoketest_design(smoke, capsys):
    assert smoke.run("plan", *smoke.design, client=FakeModelClient()) == 0
    out = capsys.readouterr().out
    assert "calls (all configs, before dedupe): 18" in out
    assert "ratings (all configs, before dedupe): 108" in out


def _study_store_state():
    """(size, mtime) of the real study store, or None before the study has run."""
    path = REPO / "results" / "raw" / "rows.jsonl"
    return (path.stat().st_size, path.stat().st_mtime_ns) if path.exists() else None


def test_end_to_end_with_ground_truth_scores_passes_and_is_idempotent(smoke, capsys):
    study_before = _study_store_state()
    client = FakeModelClient(scorer=truth_scorer(TRUTH))
    assert smoke.run("submit", "--confirm", *smoke.design, client=client) == 0
    assert smoke.run("collect", client=client) == 0
    rows = list(smoke.store().iter_rows())
    assert len(rows) == 18 and {r.status for r in rows} == {"ok"}
    capsys.readouterr()
    assert smoke.run("status", client=client) == 0
    assert "'ok': 18" in capsys.readouterr().out
    assert smoke.run("check", *smoke.expect, client=client) == 0
    out = capsys.readouterr().out
    assert out.count("PASS") == 5 and "FAIL" not in out
    # rerun sends nothing new and keeps the store unchanged
    assert smoke.run("submit", "--confirm", *smoke.design, client=client) == 0
    assert len(client.submitted_batches) == 1
    assert len(list(smoke.store().iter_rows())) == 18
    # nothing was written outside the smoketest store (the study store, if any, is untouched)
    assert _study_store_state() == study_before


def test_check_fails_with_exit_1_when_the_system_scores_perversely(smoke, capsys):
    client = FakeModelClient(scorer=truth_scorer(PERVERSE))
    smoke.run("submit", "--confirm", *smoke.design, client=client)
    smoke.run("collect", client=client)
    capsys.readouterr()
    assert smoke.run("check", *smoke.expect, client=client) == 1
    assert "FAIL" in capsys.readouterr().out


def test_check_counts_malformed_failures_against_the_ok_rate(smoke, capsys):
    from llm_panel.application.build_jobs import build_jobs
    from llm_panel.bootstrap.design_loader import load_design
    from llm_panel.bootstrap.inputs_loader import load_inputs
    from llm_panel.domain.design import to_run_specs

    specs = to_run_specs(load_design(smoke.root / "smoketest" / "design.yaml"))
    jobs = build_jobs(specs, load_inputs(smoke.root / "smoketest" / "inputs"), smoke.store()).jobs
    bad = FakeModelClient(
        scorer=truth_scorer(TRUTH),
        malformed={j.job_id for j in jobs[:6]},
        malformed_attempts=2,
    )
    smoke.run("submit", "--confirm", *smoke.design, client=bad)
    smoke.run("collect", client=bad)
    smoke.run("collect", client=bad)  # retry round
    capsys.readouterr()
    assert smoke.run("check", *smoke.expect, client=bad) == 1
    assert "12/18 jobs ok" in capsys.readouterr().out


def test_check_counts_jobs_awaiting_retry_as_not_ok(smoke, capsys):
    from llm_panel.application.build_jobs import build_jobs
    from llm_panel.bootstrap.design_loader import load_design
    from llm_panel.bootstrap.inputs_loader import load_inputs
    from llm_panel.domain.design import to_run_specs

    specs = to_run_specs(load_design(smoke.root / "smoketest" / "design.yaml"))
    jobs = build_jobs(specs, load_inputs(smoke.root / "smoketest" / "inputs"), smoke.store()).jobs
    client = FakeModelClient(
        scorer=truth_scorer(TRUTH), malformed={j.job_id for j in jobs[:6]}, malformed_attempts=2
    )
    smoke.run("submit", "--confirm", *smoke.design, client=client)
    smoke.run("collect", client=client)  # first round only: 6 jobs are invalid, retry pending
    capsys.readouterr()
    assert smoke.run("check", *smoke.expect, client=client) == 1
    assert "12/18 jobs ok" in capsys.readouterr().out
