"""TASK-12 pilot setup: its own config, store and ceiling, and a baseline-only design. Offline."""

import glob
from pathlib import Path

from llm_panel.bootstrap.cli import main
from llm_panel.bootstrap.config import external_spend, load_config

REPO = Path(__file__).parents[1]
PILOT_CONFIG = REPO / "config.pilot.yaml"


def test_pilot_config_has_its_own_store_and_a_small_ceiling():
    pilot, main_cfg = load_config(PILOT_CONFIG), load_config(REPO / "config.yaml")
    assert pilot.spend.max_spend_usd == 0.25
    assert pilot.approved_providers == frozenset({"opencode"})
    pilot_dir = REPO / "results" / "pilot"
    assert pilot.raw_store.parent == pilot_dir and pilot.ledger.parent == pilot_dir
    assert pilot.raw_store != main_cfg.raw_store  # pilot rows never enter results/raw
    assert pilot.spend.est_output_tokens_per_policy == 600
    assert pilot.spend.prices["glm-5.3-flash"] == main_cfg.spend.prices["glm-5.3-flash"]
    assert pilot.inputs_dir == main_cfg.inputs_dir
    assert pilot.prompts_dir == main_cfg.prompts_dir
    assert pilot.evidence_packets == main_cfg.evidence_packets
    assert pilot.counts_spend_from == [REPO / "config*.yaml", REPO / "adversarial/config*.yaml"]


def test_main_config_counts_the_pilot_ledger_toward_the_global_ceiling():
    pattern, _adversarial = load_config(REPO / "config.yaml").counts_spend_from
    assert str(PILOT_CONFIG) in glob.glob(str(pattern))
    external_spend(load_config(REPO / "config.yaml"))  # every matched config is readable
    external_spend(load_config(PILOT_CONFIG))


def test_pilot_plan_selects_20_baseline_jobs_offline(capsys):
    argv = ["--config", str(PILOT_CONFIG), "plan", "--design", str(REPO / "designs/pilot.yaml"),
            "--max-jobs", "20"]  # fmt: skip

    def no_client(provider):
        raise AssertionError("plan must not build a client")

    assert main(argv, client_factory=no_client) == 0
    out = capsys.readouterr().out
    assert "design: one_at_a_time (1 cells)" in out
    assert "  B: 561 calls (561 per repeat x 1)" in out
    assert "jobs to submit: 20" in out
    assert "  opencode: 20 jobs" in out
