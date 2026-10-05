"""EXPLORATORY reversed-scale probe (TASK-38): the real template and configs, and the probe end to
end with the fake client in a temp project built on the adversarial arm's test project. Offline;
no paid calls; never touches results/raw or the adversarial arm's store."""

import glob
import shutil
from pathlib import Path

import pytest
import yaml

from adversarial.cli import main as adversarial_main
from llm_panel.adapters.fake_client import FakeModelClient
from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.bootstrap.config import load_config
from llm_panel.bootstrap.prompt_files import file_sha256
from llm_panel.domain.study_prompt import check_template
from scale_probe.cli import load_probe_config, main
from tests.adversarial.test_arm import SNAP, _make_project, planted_score

REPO = Path(__file__).parents[2]
TEMPLATE = REPO / "scale_probe" / "prompts" / "reversed_scale.txt"
OLD = "where a higher score means the policy does better on that criterion."
NEW = (
    "where a lower score means the policy does better on that criterion "
    "(0 is the best score and 100 the worst)."
)
HEADER = "# EXPLORATORY: reversed-scale probe — not pooled with the main analysis"
NOW = "2026-10-05T00:00Z"


# --- the real files --------------------------------------------------------------------------


def test_template_is_the_baseline_with_only_the_scale_sentence_reversed():
    base = (REPO / "prompts" / "persona_policy" / "baseline.txt").read_text(encoding="utf-8")
    assert base.count(OLD) == 1
    assert TEMPLATE.read_text(encoding="utf-8") == base.replace(OLD, NEW)
    check_template("persona_policy", TEMPLATE.read_text(encoding="utf-8"))


def test_template_hash_matches_the_probe_manifest():
    manifest = yaml.safe_load((REPO / "scale_probe" / "manifest.yaml").read_text())
    (entry,) = manifest["files"]
    assert entry["path"] == "scale_probe/prompts/reversed_scale.txt"
    assert file_sha256(TEMPLATE) == entry["sha256"]


def test_real_probe_config_loads_with_its_own_store_and_counts_the_other_ledgers():
    config, probe = load_probe_config(REPO / "scale_probe" / "config.scale_probe.yaml")
    home = (REPO / "scale_probe").resolve()
    assert config.raw_store.resolve().is_relative_to(home)
    assert config.ledger.resolve().is_relative_to(home)
    counted = {Path(m).resolve() for p in config.counts_spend_from for m in glob.glob(str(p))}
    assert (REPO / "config.yaml").resolve() in counted
    assert (REPO / "adversarial" / "config.adversarial.yaml").resolve() in counted
    assert config.spend.max_spend_usd <= 0.30


@pytest.mark.parametrize(
    "path",
    [
        *sorted(glob.glob(str(REPO / "config*.yaml"))),
        str(REPO / "adversarial" / "config.adversarial.yaml"),
    ],  # fmt: skip
)
def test_every_other_config_counts_the_probe_ledger(path):
    config = load_config(path)
    probe = (REPO / "scale_probe" / "config.scale_probe.yaml").resolve()
    counted = {Path(m).resolve() for p in config.counts_spend_from for m in glob.glob(str(p))}
    assert probe in counted


# --- end to end with the fake client ---------------------------------------------------------


def mirror_scorer(job, criterion):
    """Follows the reversed instruction exactly: the mirror image of the planted score."""
    score = planted_score(job, criterion)
    return round(100.0 - score, 1) if "a lower score means" in job.prompt else score


def ignoring_scorer(job, criterion):
    """Ignores the reversed instruction: keeps 100 = best."""
    return planted_score(job, criterion)


def _probe_project(root: Path) -> tuple[Path, Path]:
    adv_config = _make_project(root)
    probe = root / "scale_probe"
    (probe / "prompts").mkdir(parents=True)
    shutil.copy(TEMPLATE, probe / "prompts" / "reversed_scale.txt")
    entry = {"path": "scale_probe/prompts/reversed_scale.txt", "sha256": file_sha256(TEMPLATE)}
    manifest = {"status": "draft", "files": [entry]}
    (probe / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    cfg = {
        "max_spend_usd": 0.30,
        "approved_providers": ["fake"],
        "counts_spend_from": ["../config*.yaml", "../adversarial/config*.yaml"],
        "paths": {"raw_store": "results/rows.jsonl", "ledger": "results/ledger.jsonl",
                  "inputs_dir": "../inputs", "prompts_dir": "../prompts",
                  "evidence_packets": {"wikipedia": "../packets"}},
        "prices": {SNAP: {"input": 1.0, "output": 5.0}},
        "scale_probe": {"adversarial_config": "../adversarial/config.adversarial.yaml",
                        "template": "prompts/reversed_scale.txt", "manifest": "manifest.yaml"},
    }  # fmt: skip
    path = probe / "config.scale_probe.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return adv_config, path


def _run_adversarial_baseline(adv_config: Path) -> None:
    client = FakeModelClient(job_scorer=planted_score)
    run = lambda *a: adversarial_main(  # noqa: E731
        ["--config", str(adv_config), *a], client_factory=lambda p: client, now=lambda: NOW
    )
    assert run("submit", "--confirm") == 0  # the search needs only the baseline and rerun first
    assert run("collect") == 0


def _probe_runner(config: Path, scorer):
    client = FakeModelClient(job_scorer=scorer)
    return lambda *a: main(
        ["--config", str(config), *a], client_factory=lambda p: client, now=lambda: NOW
    )


def _rows(path: Path) -> int:
    return sum(1 for _ in JsonlResultStore(path).iter_rows()) if path.exists() else 0


@pytest.fixture
def mirrored(tmp_path):
    adv_config, config = _probe_project(tmp_path)
    _run_adversarial_baseline(adv_config)
    adv_rows = _rows(tmp_path / "adversarial" / "results" / "rows.jsonl")
    run = _probe_runner(config, mirror_scorer)
    assert run("submit", "--confirm") == 0
    assert run("collect") == 0
    assert run("report", "--out", str(tmp_path / "scale_probe")) == 0
    return tmp_path, run, adv_rows


def test_probe_runs_one_call_per_search_persona_and_policy(mirrored):
    root, run, _ = mirrored
    assert (
        _rows(root / "scale_probe" / "results" / "rows.jsonl") == 4 * 4
    )  # 4 personas x 4 policies
    assert run("submit", "--confirm") == 0  # nothing left: finished jobs are skipped
    assert _rows(root / "scale_probe" / "results" / "rows.jsonl") == 16


def test_probe_never_writes_the_adversarial_store_or_results_raw(mirrored):
    root, _, adv_rows = mirrored
    assert _rows(root / "adversarial" / "results" / "rows.jsonl") == adv_rows
    assert not (root / "results" / "raw" / "rows.jsonl").exists()


def test_report_of_a_faithful_mirror(mirrored):
    root, _, _ = mirrored
    text = (root / "scale_probe" / "report.md").read_text()
    assert text.startswith(HEADER)
    assert "target policy: ubc" in text
    assert "unconverted | 0" in text
    assert "| reversed, converted (100 - x) | ubc rank 1.0 |" in text


def test_report_when_the_model_ignores_the_reversal(tmp_path):
    adv_config, config = _probe_project(tmp_path)
    _run_adversarial_baseline(adv_config)
    run = _probe_runner(config, ignoring_scorer)
    assert run("submit", "--confirm") == 0
    assert run("collect") == 0
    assert run("report", "--out", str(tmp_path / "scale_probe")) == 0
    text = (tmp_path / "scale_probe" / "report.md").read_text()
    assert "| reversed, converted (100 - x) | ubc rank 4.0 |" in text
    assert "converted | 0" in text


def test_report_waits_for_the_adversarial_baseline(tmp_path):
    _, config = _probe_project(tmp_path)
    run = _probe_runner(config, mirror_scorer)
    assert run("report", "--out", str(tmp_path / "scale_probe")) == 0
    text = (tmp_path / "scale_probe" / "report.md").read_text()
    assert text.startswith(HEADER)
    assert "pending" in text


def test_submit_needs_confirm(tmp_path, capsys):
    _, config = _probe_project(tmp_path)
    assert _probe_runner(config, mirror_scorer)("submit") == 2
    assert "--confirm" in capsys.readouterr().err
    assert _rows(tmp_path / "scale_probe" / "results" / "rows.jsonl") == 0


def test_refuses_a_template_that_does_not_match_its_manifest(tmp_path, capsys):
    _, config = _probe_project(tmp_path)
    t = tmp_path / "scale_probe" / "prompts" / "reversed_scale.txt"
    t.write_text(t.read_text() + " ")
    assert _probe_runner(config, mirror_scorer)("plan") == 2
    assert "manifest" in capsys.readouterr().err


def test_refuses_an_unapproved_provider(tmp_path, capsys):
    _, config = _probe_project(tmp_path)
    cfg = yaml.safe_load(config.read_text())
    cfg["approved_providers"] = ["opencode"]
    config.write_text(yaml.safe_dump(cfg))
    assert _probe_runner(config, mirror_scorer)("submit", "--confirm") == 2
    assert _rows(tmp_path / "scale_probe" / "results" / "rows.jsonl") == 0
