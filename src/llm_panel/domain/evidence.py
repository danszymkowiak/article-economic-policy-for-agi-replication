"""Verification of extracted evidence spans. Pure: no I/O.

A span is accepted only if its text is an exact substring of the pinned source text. Nothing is
repaired or normalised, so a paraphrase or a whitespace change is rejected, not fixed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    heading: str
    text: str


@dataclass(frozen=True)
class VerifyResult:
    accepted: list[Span]
    rejected: list[tuple[Span, str]]


def verify_spans(source: str, spans: list[Span]) -> VerifyResult:
    accepted: list[Span] = []
    rejected: list[tuple[Span, str]] = []
    seen: set[str] = set()
    for span in spans:
        if not span.text.strip():
            rejected.append((span, "empty"))
        elif span.text in seen:
            rejected.append((span, "duplicate"))
        elif span.text not in source:
            rejected.append((span, "not an exact substring"))
        else:
            seen.add(span.text)
            accepted.append(span)
    return VerifyResult(accepted, rejected)


@dataclass(frozen=True)
class SourceRef:
    title: str
    revid: int
    fetched_at: str

    @property
    def url(self) -> str:
        return f"https://en.wikipedia.org/w/index.php?oldid={self.revid}"


def render_packet(
    policy: str,
    sources: list[SourceRef],
    spans: list[tuple[SourceRef, Span]],
    extractor: dict,
    agreement: dict[str, float] | None = None,
) -> str:
    """Render a public evidence packet: attribution header, then verbatim spans in order."""
    lines = [f"# Evidence packet: {policy}", ""]
    lines.append(
        "Source: English Wikipedia (text licensed CC BY-SA 4.0; excerpts are shared alike)."
    )
    for s in sources:
        lines.append(f"- {s.title}, revision {s.revid}: {s.url} (fetched {s.fetched_at})")
    lines.append(
        f"Extracted verbatim by {extractor['model']} (prompt sha256 {extractor['prompt_sha256']}, "
        f"run {extractor['run_date']}); every excerpt was checked as an exact substring of the "
        "pinned revision text."
    )
    if agreement:
        parts = ", ".join(f"{t} {a:.0%}" for t, a in agreement.items())
        lines.append(
            "The union of two independent extraction passes is shown; character overlap "
            f"between the passes: {parts}."
        )
    lines.append("")
    if not spans:
        lines.append("No qualifying empirical evidence was found in the source text.")
        return "\n".join(lines) + "\n"
    for src, span in spans:
        lines.append(f"## {span.heading} ({src.title})")
        lines.append(span.text)
        lines.append("")
    return "\n".join(lines)


def _interval(source: str, span: Span) -> tuple[int, int] | None:
    start = source.find(span.text)
    if not span.text.strip() or start < 0:
        return None
    return start, start + len(span.text)


def merge_passes(source: str, passes: list[list[Span]]) -> list[Span]:
    """Union of several extraction passes, in source order.

    Spans that are not exact substrings of the source are dropped. Spans that overlap are
    replaced by the contiguous source slice covering both, so every output span is still a
    verbatim substring. The heading is that of the earliest span in the group.
    """
    found: list[tuple[int, int, str]] = []
    for spans in passes:
        for span in spans:
            iv = _interval(source, span)
            if iv is not None:
                found.append((iv[0], iv[1], span.heading))
    found.sort(key=lambda t: (t[0], -t[1]))
    merged: list[list] = []
    for start, end, heading in found:
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end, heading])
    return [Span(heading=h, text=source[s:e]) for s, e, h in merged]


def pass_agreement(source: str, a: list[Span], b: list[Span]) -> float:
    """Character overlap over character union of two passes' spans (1.0 if both are empty)."""

    def covered(spans: list[Span]) -> set[int]:
        chars: set[int] = set()
        for span in spans:
            iv = _interval(source, span)
            if iv is not None:
                chars.update(range(*iv))
        return chars

    ca, cb = covered(a), covered(b)
    union = ca | cb
    return len(ca & cb) / len(union) if union else 1.0
