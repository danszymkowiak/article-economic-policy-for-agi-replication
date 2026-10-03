import yaml

from llm_panel.adapters.jsonl import JsonlResultStore
from llm_panel.domain.results import StoredRow
from tests.test_cli import SNAP, env  # noqa: F401  (fixture)


def _drifted_row(env):  # noqa: F811
    JsonlResultStore(env.root / "raw.jsonl").append(
        StoredRow(
            job_id="x", status="ok", attempt=1, provider="fake", model_snapshot=SNAP,
            temperature=0.0, seed=0, timestamp="t", request={}, response={"model": "other-model"},
            usage={"input_tokens": 1, "output_tokens": 1}, batch_id="b",
        )
    )  # fmt: skip


def test_status_shows_model_id_check(env, capsys):  # noqa: F811
    assert env.run("status") == 0
    assert "model ids: ok" in capsys.readouterr().out
    _drifted_row(env)
    env.run("status")
    out = capsys.readouterr().out
    assert "WARNING" in out and "other-model" in out


def test_submit_refuses_after_model_id_drift(env, capsys):  # noqa: F811
    _drifted_row(env)
    assert env.run("submit", "--confirm", *env.design()) == 2
    assert "model id" in capsys.readouterr().err
    assert yaml.safe_load(env.config_path.read_text())  # config untouched
