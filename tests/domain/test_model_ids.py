from llm_panel.domain.model_ids import check_model_ids
from llm_panel.domain.results import StoredRow


def row(snapshot="glm-5.3-flash", reported="glm-5.3-flash", ts="2026-10-03T00:00:00Z", job="j"):
    response = {"model": reported} if reported is not None else {}
    return StoredRow(
        job_id=job, status="ok", attempt=1, provider="opencode", model_snapshot=snapshot,
        temperature=0.0, seed=0, timestamp=ts, request={}, response=response, usage={},
        batch_id="b",
    )  # fmt: skip


def test_matching_ids_are_clean():
    report = check_model_ids([row(), row(job="k")])
    assert not report.has_issues and report.checked == 2


def test_reported_id_differing_from_requested_is_flagged():
    report = check_model_ids([row(), row(reported="glm-5.3-flash-2026-11", job="k")])
    assert report.has_issues
    assert report.mismatched == {"glm-5.3-flash": {"glm-5.3-flash-2026-11": 1}}


def test_provider_prefix_on_the_requested_snapshot_is_ignored():
    assert not check_model_ids([row(snapshot="opencode/glm-5.3-flash")]).has_issues


def test_rows_without_a_reported_id_are_counted_not_flagged():
    report = check_model_ids([row(reported=None)])
    assert report.unreported == 1 and not report.has_issues


def test_id_changing_over_the_study_is_reported_in_order_of_first_seen():
    rows = [
        row(ts="2026-10-03T02:00:00Z", reported="b", job="2"),
        row(ts="2026-10-03T01:00:00Z", reported="a", job="1"),
    ]
    report = check_model_ids(rows)
    assert report.has_issues and report.reported_ids["glm-5.3-flash"] == ["a", "b"]


def test_rows_without_response_payload_are_unreported():
    r = row()
    r = StoredRow(**{**r.to_dict(), "response": None})
    assert check_model_ids([r]).unreported == 1
