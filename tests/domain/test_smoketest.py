from llm_panel.domain.models import Rating
from llm_panel.domain.smoketest import Close, Expectations, Greater, evaluate, mean_scores


def rating(policy, score, criterion="c", persona="p", job="j"):
    return Rating(job, persona, criterion, policy, score, "r")


EXP = Expectations(
    min_ok_rate=0.9,
    greater=(Greater("c", "good", "bad", margin=10),),
    close=(Close("c", "a", "b", tolerance=5),),
)


def ratings(good=80, bad=20, a=50, b=52):
    return [rating("good", good), rating("bad", bad), rating("a", a), rating("b", b)]


def test_mean_scores_average_over_personas_and_repeats():
    got = mean_scores([rating("x", 10, persona="p1"), rating("x", 30, persona="p2")])
    assert got == {("c", "x"): 20.0}


def test_all_expectations_met():
    checks = evaluate(EXP, ratings(), ok=10, total=10)
    assert all(c.passed for c in checks) and len(checks) == 3


def test_greater_fails_when_margin_not_reached():
    checks = evaluate(EXP, ratings(good=25, bad=20), ok=10, total=10)
    failed = [c for c in checks if not c.passed]
    assert len(failed) == 1 and "good" in failed[0].description and "5.0" in failed[0].detail


def test_greater_fails_when_order_is_reversed():
    assert not all(c.passed for c in evaluate(EXP, ratings(good=20, bad=80), 10, 10))


def test_close_fails_when_paraphrases_diverge():
    failed = [c for c in evaluate(EXP, ratings(a=30, b=60), ok=10, total=10) if not c.passed]
    assert len(failed) == 1 and "close to" in failed[0].description


def test_low_ok_rate_fails():
    checks = evaluate(EXP, ratings(), ok=8, total=10)
    assert any(not c.passed and "ok rate" in c.description for c in checks)


def test_missing_scores_fail_instead_of_crashing():
    checks = evaluate(EXP, [rating("good", 80)], ok=10, total=10)
    assert any(not c.passed and "no scores" in c.detail for c in checks)


def test_no_jobs_fails_ok_rate():
    assert any(not c.passed for c in evaluate(EXP, [], ok=0, total=0))
