"""Fetch a pinned Wikipedia revision as plain text with section headings.

Stdlib only. `html_to_text` is pure and tested; `fetch_revision_text` does the network call.
Reference lists, navigation boxes, styles, edit links and the "See also", "References",
"External links", "Notes", "Further reading" and "Bibliography" sections are dropped, since
none of them is article prose. Everything else, including table cells, is kept in order.
"""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from html.parser import HTMLParser

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "llm-panel-sensitivity-study/0.1 (research; szymkodf@gmail.com)"
DROPPED_SECTIONS = {
    "see also",
    "references",
    "external links",
    "notes",
    "further reading",
    "bibliography",
    "footnotes",
}
SKIP_TAGS = {"style", "script", "sup"}
SKIP_CLASSES = {"navbox", "reflist", "references", "mw-editsection", "toc", "hatnote", "metadata"}
BLOCK_TAGS = {"p", "li", "tr", "div", "h2", "h3", "h4", "h5", "table", "ul", "ol", "dl", "dd", "dt"}
HEADINGS = {"h2", "h3", "h4", "h5"}


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._stack: list[bool] = []  # per open tag: did it start a skip region
        self._heading: str | None = None
        self._section_dropped = False

    def handle_starttag(self, tag: str, attrs) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        skip = tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        if tag in {"br", "img", "hr", "meta", "link"}:
            return
        self._stack.append(skip)
        if skip:
            self._skip_depth += 1
        if self._skip_depth:
            return
        if tag in HEADINGS:
            self._heading = ""
        if tag in {"td", "th"}:
            self._emit(" | ")
        elif tag in BLOCK_TAGS:
            self._emit("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"br", "img", "hr", "meta", "link"} or not self._stack:
            return
        skip = self._stack.pop()
        if skip:
            self._skip_depth -= 1
            return
        if tag in HEADINGS and self._heading is not None:
            name = self._heading.strip()
            self._section_dropped = name.lower() in DROPPED_SECTIONS
            if not self._section_dropped:
                self.parts.append(name)
            self._heading = None
        if tag in BLOCK_TAGS:
            self._emit("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._heading is not None:
            self._heading += data
        else:
            self._emit(data)

    def _emit(self, s: str) -> None:
        if not self._section_dropped:
            self.parts.append(s)


def html_to_text(html: str) -> str:
    parser = _Extractor()
    parser.feed(html)
    text = "".join(parser.parts)
    lines = [" ".join(line.split()) for line in text.split("\n")]
    out: list[str] = []
    for line in lines:
        line = line.strip(" |")
        if line:
            out.append(line)
    return "\n".join(out) + "\n"


def fetch_revision_text(revid: int) -> dict:
    """Fetch one pinned revision. Returns text, sha256 of the text and the fetch timestamp."""
    query = urllib.parse.urlencode(
        {
            "action": "parse",
            "oldid": revid,
            "prop": "text|displaytitle",
            "format": "json",
            "formatversion": 2,
            "disableeditsection": 1,
        }
    )
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        payload = json.load(response)
    html = payload["parse"]["text"]
    text = html_to_text(html)
    return {
        "revid": revid,
        "title": payload["parse"]["title"],
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
