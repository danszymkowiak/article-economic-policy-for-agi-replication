"""The Claude arm's harness (rater agent definition and the driver code holding the agent prompt
wrapper and the line-to-JSON conversion) is pinned by hash in the frozen prereg s9a."""

from pathlib import Path

import yaml

from llm_panel.bootstrap.prompt_files import manifest_mismatches

REPO = Path(__file__).parents[2]
MANIFEST = REPO / "subagent_arm/manifest.yaml"


def test_harness_files_match_the_manifest():
    assert manifest_mismatches(MANIFEST, REPO) == []


def test_manifest_covers_the_rater_agent_and_the_driver_and_the_prereg_quotes_the_hashes():
    manifest = yaml.safe_load(MANIFEST.read_text())
    assert {e["path"] for e in manifest["files"]} == {
        ".claude/agents/rater.md",
        "subagent_arm/arm.py",
    }
    prereg = (REPO / "prereg/prereg.md").read_text()
    for e in manifest["files"]:
        assert e["sha256"] in prereg, e["path"]
