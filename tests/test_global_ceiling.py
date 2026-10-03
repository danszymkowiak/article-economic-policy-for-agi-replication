"""The 15 USD hard ceiling is global: spend recorded in other ledgers counts against it."""

import pytest
import yaml

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.application.spend import Spend, SpendCeilingError, check_ceiling
from llm_panel.bootstrap.config import load_config
from llm_panel.domain.pricing import HARD_CEILING_USD
from llm_panel.domain.results import StoredRow
from tests.test_cli import SNAP, env  # noqa: F401  (fixture)


def test_check_ceiling_counts_external_spend_against_the_hard_ceiling():
    spend = Spend(actual=0.0, outstanding=0.0, ceiling=15.0, external=14.9)
    with pytest.raises(SpendCeilingError, match="other ledgers"):
        check_ceiling(spend, 0.2)
    check_ceiling(spend, 0.05)


def test_external_spend_counts_even_when_own_ceiling_is_lower():
    # A small smoketest ceiling must not let the global 15 USD be exceeded via other ledgers.
    spend = Spend(actual=0.0, outstanding=0.0, ceiling=0.25, external=14.9)
    with pytest.raises(SpendCeilingError):
        check_ceiling(spend, 0.2)


def test_own_ceiling_still_applies_to_own_spend():
    with pytest.raises(SpendCeilingError):
        check_ceiling(Spend(actual=0.2, outstanding=0.0, ceiling=0.25), 0.1)


def _other_ledger(env, spent_usd):  # noqa: F811
    """A second project config whose store holds `spent_usd` of actual spend at SNAP's price."""
    root = env.root / "other"
    root.mkdir()
    cfg = {
        "max_spend_usd": 1,
        "paths": {"raw_store": "raw.jsonl", "ledger": "ledger.jsonl"},
        "prices": {SNAP: {"input": 1.0, "output": 5.0}},
    }
    (root / "config.yaml").write_text(yaml.safe_dump(cfg))
    JsonlResultStore(root / "raw.jsonl").append(
        StoredRow(
            job_id="x", status="ok", attempt=1, provider="fake", model_snapshot=SNAP,
            temperature=0.0, seed=0, timestamp="t", request={}, response={},
            usage={"input_tokens": int(spent_usd * 1e6), "output_tokens": 0}, batch_id="b",
        )
    )  # fmt: skip
    return root / "config.yaml"


def test_submit_is_refused_when_other_ledgers_exhaust_the_global_ceiling(env, capsys):  # noqa: F811
    other = _other_ledger(env, HARD_CEILING_USD)
    env.set_config(counts_spend_from=[str(other)])
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "other ledgers" in capsys.readouterr().err
    assert not list(env.store().iter_rows())


def test_status_reports_external_spend(env, capsys):  # noqa: F811
    env.set_config(counts_spend_from=[str(_other_ledger(env, 2))])
    assert env.run("status") == 0
    assert "other ledgers $2.0000" in capsys.readouterr().out


def test_counts_spend_from_accepts_globs_relative_to_the_config(env, capsys):  # noqa: F811
    _other_ledger(env, 2)
    env.set_config(counts_spend_from=["other/config*.yaml"])
    assert load_config(env.config_path).counts_spend_from == [env.root / "other/config*.yaml"]
    env.run("status")
    assert "other ledgers $2.0000" in capsys.readouterr().out


def test_unreadable_other_config_fails_closed(env, capsys):  # noqa: F811
    env.set_config(counts_spend_from=["nonexistent.yaml"])
    assert env.run("status") == 2
    assert "nonexistent.yaml" in capsys.readouterr().err


def test_a_config_does_not_double_count_its_own_ledger(env, capsys):  # noqa: F811
    env.set_config(counts_spend_from=[str(env.config_path)])
    assert env.run("status") == 0
    assert "other ledgers $0.0000" in capsys.readouterr().out
