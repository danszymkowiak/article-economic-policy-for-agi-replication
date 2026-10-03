import json

import pytest

from llm_panel.domain.validation import InvalidResponse, parse_ratings
from tests.domain.test_models import make_job


def text(*items):
    return json.dumps({"ratings": [{"policy": p, "score": s, "rationale": "r"} for p, s in items]})


def test_valid_response_maps_labels_to_policy_ids():
    job = make_job(policy_ids=("ubc", "nit"), policy_labels=("B", "A"))
    ratings = parse_ratings(job, text(("A", 10), ("B", 90)))
    by_policy = {r.policy_id: r.score for r in ratings}
    assert by_policy == {"nit": 10, "ubc": 90}
    assert {r.job_id for r in ratings} == {job.job_id}
    assert {r.persona_id for r in ratings} == {job.persona_id}


def test_fenced_json_is_accepted():
    job = make_job()
    assert len(parse_ratings(job, "```json\n" + text(("a", 1), ("b", 2)) + "\n```")) == 2


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        "[]",
        json.dumps({"ratings": []}),
        text(("a", 101), ("b", 5)),
        text(("a", -1), ("b", 5)),
        text(("a", 1)),  # missing b
        text(("a", 1), ("a", 2)),  # duplicate label
        text(("a", 1), ("b", 2), ("c", 3)),  # unknown label
        json.dumps({"ratings": [{"policy": "a", "score": "high", "rationale": "r"}]}),
    ],
)
def test_invalid_responses_rejected(bad):
    with pytest.raises(InvalidResponse):
        parse_ratings(make_job(), bad)
