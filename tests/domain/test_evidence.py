from llm_panel.domain.evidence import Span, verify_spans

SOURCE = (
    "Overview\nA tax credit for workers.\n"
    "Evidence\nA 2012 study found employment rose 7 percent. Another found no effect.\n"
)


def test_exact_substring_accepted():
    s = Span(heading="Evidence", text="A 2012 study found employment rose 7 percent.")
    result = verify_spans(SOURCE, [s])
    assert result.accepted == [s]
    assert result.rejected == []


def test_paraphrase_rejected_with_reason():
    s = Span(heading="Evidence", text="A 2012 study found employment increased by 7%.")
    result = verify_spans(SOURCE, [s])
    assert result.accepted == []
    assert result.rejected == [(s, "not an exact substring")]


def test_whitespace_changes_are_not_repaired():
    s = Span(heading="Evidence", text="Another  found no effect.")
    assert verify_spans(SOURCE, [s]).accepted == []


def test_empty_span_rejected():
    s = Span(heading="Evidence", text="   ")
    assert verify_spans(SOURCE, [s]).rejected == [(s, "empty")]


def test_duplicate_span_rejected_once_kept_once():
    s = Span(heading="Evidence", text="Another found no effect.")
    result = verify_spans(SOURCE, [s, s])
    assert result.accepted == [s]
    assert result.rejected == [(s, "duplicate")]


def test_order_preserved():
    a = Span(heading="Evidence", text="Another found no effect.")
    b = Span(heading="Overview", text="A tax credit for workers.")
    assert verify_spans(SOURCE, [a, b]).accepted == [a, b]


from llm_panel.domain.evidence import SourceRef, render_packet  # noqa: E402

SRC = SourceRef(title="Earned income tax credit", revid=123, fetched_at="2026-10-04T08:50:00+00:00")
EXTRACTOR = {"model": "claude-sonnet-5-5", "prompt_sha256": "abc123", "run_date": "2026-10-04"}


def test_packet_header_has_attribution_and_extractor():
    spans = [(SRC, Span(heading="Effects", text="Employment rose 7 percent."))]
    text = render_packet("EITC", [SRC], spans, EXTRACTOR)
    assert "https://en.wikipedia.org/w/index.php?oldid=123" in text
    assert "CC BY-SA 4.0" in text
    assert "claude-sonnet-5-5" in text and "abc123" in text
    assert "Employment rose 7 percent." in text


def test_empty_packet_says_so():
    text = render_packet("UBC", [SRC], [], EXTRACTOR)
    assert "No qualifying empirical evidence" in text


def test_spans_grouped_in_given_order_with_heading():
    a = Span(heading="Effects", text="First.")
    b = Span(heading="Costs", text="Second.")
    text = render_packet("EITC", [SRC], [(SRC, a), (SRC, b)], EXTRACTOR)
    assert text.index("First.") < text.index("Second.")
    assert "Effects" in text and "Costs" in text


from llm_panel.domain.evidence import merge_passes, pass_agreement  # noqa: E402

MSRC = "Intro.\nA: One fact here. Second fact there. Third fact now.\nB: Other fact."


def sp(h, t):
    return Span(heading=h, text=t)


def test_merge_keeps_union_in_source_order():
    p1 = [sp("B", "Other fact.")]
    p2 = [sp("A", "One fact here.")]
    merged = merge_passes(MSRC, [p1, p2])
    assert [s.text for s in merged] == ["One fact here.", "Other fact."]


def test_merge_identical_spans_once():
    s = sp("A", "One fact here.")
    assert merge_passes(MSRC, [[s], [s]]) == [s]


def test_merge_contained_span_collapses_to_longer():
    long = sp("A", "One fact here. Second fact there.")
    short = sp("A", "Second fact there.")
    assert merge_passes(MSRC, [[long], [short]]) == [long]


def test_merge_partial_overlap_becomes_contiguous_source_slice():
    a = sp("A", "One fact here. Second fact there.")
    b = sp("A", "Second fact there. Third fact now.")
    merged = merge_passes(MSRC, [[a], [b]])
    assert [s.text for s in merged] == ["One fact here. Second fact there. Third fact now."]
    assert merged[0].text in MSRC


def test_merge_drops_spans_not_in_source():
    bad = sp("A", "Invented fact.")
    good = sp("A", "One fact here.")
    assert merge_passes(MSRC, [[bad, good]]) == [good]


def test_pass_agreement_is_char_overlap_over_union():
    a = [sp("A", "One fact here. Second fact there.")]
    b = [sp("A", "Second fact there.")]
    agree = pass_agreement(MSRC, a, b)
    assert 0 < agree < 1
    assert pass_agreement(MSRC, a, a) == 1.0
    assert pass_agreement(MSRC, [], []) == 1.0


def test_packet_reports_two_pass_agreement():
    text = render_packet("EITC", [SRC], [], EXTRACTOR, agreement={"Earned income tax credit": 0.66})
    assert "two independent extraction passes" in text
    assert "66%" in text
