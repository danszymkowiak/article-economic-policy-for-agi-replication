"""ADVERSARIAL ARM (TASK-22): the pure parts. Catalogue, edit size, packet edits, panel outcome and
the greedy, bounded search. No I/O, no calls."""

import ast
import pathlib

import pytest

import adversarial
from adversarial.catalogue import CATALOGUE, CATALOGUE_VERSION, Perturbation, check_catalogue
from adversarial.search import (
    CANDIDATE_CAP,
    DEPTH_EXHAUSTED,
    FOUND,
    NO_IMPROVEMENT,
    RUNNING,
    Candidate,
    EditSize,
    changed_span,
    depth_one,
    edit_packet,
    edit_size,
    extend,
    panel_outcome,
    search,
)
from tests.domain.test_no_io import FORBIDDEN_CALLS, FORBIDDEN_IMPORTS

REPO = pathlib.Path(__file__).parents[2]
TEMPLATE = (REPO / "prompts" / "persona_policy" / "baseline.txt").read_text()


def test_pure_modules_do_no_io():
    root = pathlib.Path(adversarial.__file__).parent
    for name in ("catalogue.py", "search.py"):
        tree = ast.parse((root / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".")[0]} if node.level == 0 else set()
            else:
                roots = set()
            assert not roots & FORBIDDEN_IMPORTS, name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALLS, name


# --- catalogue ---


def test_catalogue_is_versioned_and_valid_against_the_study_template():
    assert CATALOGUE_VERSION == "adv-catalogue-v1"
    check_catalogue(CATALOGUE, TEMPLATE)  # every wording fragment occurs exactly once
    kinds = {p.kind for p in CATALOGUE}
    assert kinds == {"wording", "evidence", "persona_subset", "temperature", "criterion_order"}
    assert len({p.id for p in CATALOGUE}) == len(CATALOGUE)


def test_check_catalogue_rejects_a_fragment_not_in_the_template():
    bad = Perturbation("w_x", "wording", "wording:x", "x", old="not in the template", new="y")
    with pytest.raises(ValueError, match="exactly once"):
        check_catalogue((bad,), TEMPLATE)


def test_check_catalogue_rejects_duplicate_ids():
    p = CATALOGUE[0]
    with pytest.raises(ValueError, match="duplicate"):
        check_catalogue((p, p), TEMPLATE)


# --- edit size and packet edits ---


def test_changed_span_is_exact_for_one_contiguous_edit():
    assert changed_span("abc", "abc") == 0
    assert changed_span("the cat sat", "the dog sat") == 3
    assert changed_span("abcdef", "abef") == 2  # deletion
    assert changed_span("ab", "abXYZ") == 3  # insertion


def test_edit_size_adds_each_perturbations_own_span():
    base = {"n1|a": "aaaa XX bbbb YY cccc", "n1|b": "same"}
    one = {"n1|a": "aaaa ZZ bbbb YY cccc", "n1|b": "same"}
    two = {"n1|a": "aaaa XX bbbb QQ cccc", "n1|b": "same"}
    assert edit_size(base, [one, two]) == EditSize(2, 4, 1)  # not the 10-character span between
    assert edit_size(base, [one]) == EditSize(1, 2, 1)


def test_edit_size_orders_by_edits_then_characters_then_prompts():
    assert EditSize(1, 50, 5) < EditSize(2, 0, 0)
    assert EditSize(1, 0, 0) < EditSize(1, 3, 1)
    assert EditSize(1, 3, 1) < EditSize(1, 3, 2)


PACKET = "# Evidence packet: X\n\nSource: wiki.\n\n## A\nalpha.\n\n## B\nbeta.\n\n## C\ngamma."


def test_edit_packet_operations_keep_the_header():
    head = "# Evidence packet: X\n\nSource: wiki."
    assert edit_packet(PACKET, "drop_last") == f"{head}\n\n## A\nalpha.\n\n## B\nbeta."
    assert edit_packet(PACKET, "drop_first") == f"{head}\n\n## B\nbeta.\n\n## C\ngamma."
    assert (
        edit_packet(PACKET, "reverse") == f"{head}\n\n## C\ngamma.\n\n## B\nbeta.\n\n## A\nalpha."
    )
    assert edit_packet(PACKET, "keep_first_half") == f"{head}\n\n## A\nalpha.\n\n## B\nbeta."
    assert edit_packet("", "drop_last") == ""
    with pytest.raises(ValueError):
        edit_packet(PACKET, "shuffle")


# --- panel outcome ---


def _ratings(table):
    """table: persona -> policy -> score on one criterion 'c'."""
    return [(n, p, "c", s) for n, row in table.items() for p, s in row.items()]


def test_panel_outcome_ranks_by_mean_with_rank_one_highest():
    out = panel_outcome(
        _ratings({"n1": {"a": 90, "b": 50, "c2": 10}, "n2": {"a": 70, "b": 60, "c2": 20}}),
        criteria=("c",), policies=("a", "b", "c2"),
    )  # fmt: skip
    assert out.means == {"a": 80.0, "b": 55.0, "c2": 15.0}
    assert out.ranks == {"a": 1.0, "b": 2.0, "c2": 3.0}
    assert out.top() == "a" and out.n_personas == 2


def test_panel_outcome_drops_the_persona_most_favourable_to_the_target():
    table = {"n1": {"a": 99, "b": 50}, "n2": {"a": 40, "b": 60}, "n3": {"a": 45, "b": 55}}
    out = panel_outcome(_ratings(table), criteria=("c",), policies=("a", "b"), drop_top_for="a")
    assert out.n_personas == 2 and out.means["a"] == pytest.approx(42.5)
    assert out.ranks["a"] == 2.0


def test_panel_outcome_is_none_when_a_policy_has_no_rating():
    assert panel_outcome(_ratings({"n1": {"a": 1}}), criteria=("c",), policies=("a", "b")) is None


# --- search ---

CAT = (
    Perturbation("w1", "wording", "wording:1", "w1", old="x", new="y"),
    Perturbation("w2", "wording", "wording:2", "w2", old="x2", new="y2"),
    Perturbation("t0", "temperature", "temperature", "t0", temperature=0.0),
    Perturbation("t1", "temperature", "temperature", "t1", temperature=1.0),
)
N = 4  # policies


class FakeOutcome:
    def __init__(self, rank):
        self.ranks, self.n_policies = {"tgt": float(rank)}, N


def sizes(c: Candidate) -> EditSize:
    chars = sum(5 if p.kind == "wording" else 0 for p in c.perturbations)
    return EditSize(len(c.perturbations), chars, 1)


def run(ranks, **kw):
    outcomes = {k: (None if r is None else FakeOutcome(r)) for k, r in ranks.items()}
    kw.setdefault("max_depth", 2)
    kw.setdefault("max_candidates", 30)
    return search(CAT, outcomes, sizes, target="tgt", base_rank=1.0, **kw)


def test_extend_skips_perturbations_in_the_same_slot():
    (t0,) = [c for c in depth_one(CAT) if c.key == "t0"]
    assert [c.key for c in extend(t0, CAT)] == ["t0+w1", "t0+w2"]


def test_search_asks_for_every_depth_one_candidate_first():
    s = run({})
    assert s.status == RUNNING and [c.key for c in s.needed] == ["w1", "w2", "t0", "t1"]
    s = run({"w1": 2, "t0": 1})
    assert [c.key for c in s.needed] == ["w2", "t1"]
    assert [t.candidate.key for t in s.tried] == ["w1", "t0"]  # partial results are logged


def test_search_stops_at_depth_one_with_the_smallest_successful_candidate():
    s = run({"w1": N, "w2": 2, "t0": N, "t1": 1})
    assert s.status == FOUND and s.winner.candidate.key == "t0"  # zero characters beats w1
    assert s.winner.top_to_bottom and s.winner.rank_drop == N - 1
    assert len(s.tried) == 4 and not s.needed


def test_search_extends_the_largest_drop_and_finds_a_planted_pair():
    depth1 = {"w1": 3, "w2": 2, "t0": 1, "t1": 3}  # w1 and t1 tie: t1 is smaller (0 chars)
    s = run(depth1)
    assert s.status == RUNNING and s.path == ("t1",)
    assert [c.key for c in s.needed] == ["t1+w1", "t1+w2"]
    s = run({**depth1, "t1+w1": N, "t1+w2": 3})
    assert s.status == FOUND and s.winner.candidate.key == "t1+w1"
    assert len(s.tried) == 6  # the multiple-comparisons denominator


def test_search_respects_the_depth_cap():
    s = run({"w1": 3, "w2": 2, "t0": 1, "t1": 1}, max_depth=1)
    assert s.status == DEPTH_EXHAUSTED and not s.needed and s.path == ("w1",)


def test_search_stops_when_nothing_lowers_the_target():
    s = run({"w1": 1, "w2": 1, "t0": None, "t1": 1})
    assert s.status == NO_IMPROVEMENT and s.winner is None
    assert [t.outcome for t in s.tried].count(None) == 1  # unevaluable candidates are logged


def test_search_respects_the_candidate_cap():
    s = run({}, max_candidates=3)
    assert [c.key for c in s.needed] == ["w1", "w2", "t0"] and s.capped == 1
    s = run({"w1": 3, "w2": 2, "t0": 1}, max_candidates=3)
    assert s.status == CANDIDATE_CAP and s.capped == 1  # an incomplete depth is not extended
    depth1 = {"w1": 3, "w2": 2, "t0": 1, "t1": 1}
    s = run(depth1, max_candidates=5)  # depth 2 would be 3 candidates; 1 fits
    assert s.status == RUNNING and [c.key for c in s.needed] == ["w1+w2"] and s.capped == 2
    s = run({**depth1, "w1+w2": 3}, max_candidates=5)
    assert s.status == CANDIDATE_CAP and s.capped == 2 and s.winner is None
    assert len(s.tried) == 5
    s = run({**depth1}, max_candidates=4)  # nothing left for depth 2
    assert s.status == CANDIDATE_CAP and s.capped == 3 and not s.needed
