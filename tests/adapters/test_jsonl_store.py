import pytest

from llm_panel.adapters.jsonl import JsonlBatchLedger, JsonlResultStore
from llm_panel.ports import BatchLedger, ResultStore
from tests.domain.test_results import row


def test_satisfies_ports(tmp_path):
    assert isinstance(JsonlResultStore(tmp_path / "r.jsonl"), ResultStore)
    assert isinstance(JsonlBatchLedger(tmp_path / "l.jsonl"), BatchLedger)


def test_append_exists_iter(tmp_path):
    store = JsonlResultStore(tmp_path / "raw" / "r.jsonl")
    assert not store.exists("j1")
    assert list(store.iter_rows()) == []
    store.append(row(job_id="j1"))
    store.append(row(job_id="j2", status="failed"))
    assert store.exists("j1") and store.exists("j2")
    assert [r.job_id for r in store.iter_rows()] == ["j1", "j2"]


def test_nonterminal_rows_do_not_count_as_existing(tmp_path):
    store = JsonlResultStore(tmp_path / "r.jsonl")
    store.append(row(job_id="j", status="invalid", attempt=1))
    assert not store.exists("j")
    store.append(row(job_id="j", status="ok", attempt=2))
    assert store.exists("j")
    assert len(list(store.iter_rows())) == 2  # both attempts retained


def test_persists_across_instances(tmp_path):
    path = tmp_path / "r.jsonl"
    JsonlResultStore(path).append(row(job_id="j1"))
    reopened = JsonlResultStore(path)
    assert reopened.exists("j1")
    reopened.append(row(job_id="j2"))
    assert [r.job_id for r in JsonlResultStore(path).iter_rows()] == ["j1", "j2"]


def test_never_overwrites_existing_bytes(tmp_path):
    path = tmp_path / "r.jsonl"
    store = JsonlResultStore(path)
    store.append(row(job_id="j1"))
    before = path.read_bytes()
    store.append(row(job_id="j1", status="ok", attempt=1))  # same id appended again
    after = path.read_bytes()
    assert after.startswith(before) and len(after) > len(before)


def test_no_mutation_api():
    for name in ("update", "delete", "remove", "clear", "overwrite", "rewrite"):
        assert not hasattr(JsonlResultStore, name)


def test_full_record_roundtrips(tmp_path):
    full = row(
        job_id="j", status="ok", attempt=1, provider="anthropic", model_snapshot="m-2026-01-01",
        temperature=0.7, seed=42, timestamp="2026-10-03T00:00:00+00:00",
        request={"prompt": "p é ü"}, response={"text": "{}", "id": "x"},
        usage={"input_tokens": 10, "output_tokens": 5}, batch_id="b1", error=None,
    )  # fmt: skip
    store = JsonlResultStore(tmp_path / "r.jsonl")
    store.append(full)
    (got,) = list(store.iter_rows())
    assert got == full


def test_corrupt_line_raises_rather_than_dropping(tmp_path):
    path = tmp_path / "r.jsonl"
    store = JsonlResultStore(path)
    store.append(row(job_id="j1"))
    with path.open("a") as fh:
        fh.write("{not json\n")
    with pytest.raises(ValueError, match="line 2"):
        list(store.iter_rows())


def test_ledger_roundtrip(tmp_path):
    ledger = JsonlBatchLedger(tmp_path / "l.jsonl")
    assert ledger.entries() == []
    ledger.record({"batch_id": "b1", "n": 1})
    ledger.record({"batch_id": "b2", "n": 2})
    assert [e["batch_id"] for e in JsonlBatchLedger(tmp_path / "l.jsonl").entries()] == ["b1", "b2"]
