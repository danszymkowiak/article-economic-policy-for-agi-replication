from llm_panel.domain.results import StoredRow


def row(**kw):
    base = dict(
        job_id="j", status="ok", attempt=1, provider="fake", model_snapshot="m", temperature=1.0,
        seed=0, timestamp="t", request={}, response={}, usage={}, batch_id="b",
    )  # fmt: skip
    base.update(kw)
    return StoredRow(**base)


def test_terminality():
    assert row(status="ok").is_terminal
    assert row(status="failed").is_terminal
    assert not row(status="invalid", attempt=1).is_terminal
    assert row(status="invalid", attempt=2).is_terminal


def test_roundtrip():
    assert StoredRow.from_dict(row().to_dict()) == row()
