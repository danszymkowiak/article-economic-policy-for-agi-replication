"""Rule-based removal of policy names from evidence packets (Q1, description-only). Pure.

Q1 removes the policy name everywhere (prereg s5), so the packet text loses it too. Names are
labels, not content: descriptive wording and real-world programme names (e.g. a national fund or
a pilot) stay, because the definition already describes the policy. Rules, applied in order:

1. The packet header `# Evidence packet: <name>` becomes `# Evidence packet: <code>`.
2. The packet's source article titles (its `- <title>, revision N: <url>` lines) are labels in
   the metadata: in the source lines, the pass-overlap line and the `## ... (<title>)` heading
   suffixes they become `<code> source <k>`. The revision links stay, so attribution survives.
3. Every policy's names and acronyms, anywhere in the text, become that policy's code: the name
   from `Policy.name` without its parenthetical, the parenthetical acronym (whole word, case-
   sensitive, optional plural s), plus the variants in NAME_VARIANTS and ACRONYM_VARIANTS.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence

from llm_panel.domain.models import Policy

# Case-insensitive variants of the Table 3 names found in the Wikipedia packets.
NAME_VARIANTS: dict[str, tuple[str, ...]] = {
    "eitc": (r"earned income credits?",),
    "almp": (r"active labou?r[- ]market(?: polic(?:y|ies)| programmes?| programs?| measures?)?",),
    "directed_industrial_policy": (r"(?:directed )?industrial polic(?:y|ies)",),
    "fjg": (r"(?:federal )?jobs? guarantees?",),
    "ubi": (r"(?:universal )?basic incomes?",),
    "nit": (r"negative income tax(?:es)?",),
    "ubs": (r"(?:universal )?basic services",),
    "ubc": (r"(?:universal )?basic capital",),
    "sawf": (
        r"sovereign (?:AI |wealth )?funds?",
        r"sovereign (?:AI )?dividends?",
        r"AI (?:fund|dividend)s?",
    ),
}
# Case-sensitive alternative acronyms for the same policy (whole word, optional plural s).
ACRONYM_VARIANTS: dict[str, tuple[str, ...]] = {"eitc": ("EIC",), "sawf": ("SWF",)}
_PAREN = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")
_HEADER = re.compile(r"^# Evidence packet: .*$", re.MULTILINE)
_SOURCE = re.compile(r"^- (.+?), revision \d+:", re.MULTILINE)
_OVERLAP = "character overlap between the passes:"


def _phrase(text: str) -> str:
    """A name as a case-insensitive whole-phrase pattern, any space or hyphen between words."""
    words = [re.escape(w) for w in re.split(r"[\s-]+", text.strip()) if w]
    return r"(?i:\b" + r"[\s-]+".join(words) + r"s?\b)"


def _patterns(policy: Policy) -> list[str]:
    m = _PAREN.match(policy.name)
    name, acronym = (m.group(1), m.group(2)) if m else (policy.name, "")
    pats = [_phrase(name)]
    acronyms = ([acronym] if acronym else []) + list(ACRONYM_VARIANTS.get(policy.id, ()))
    pats += [r"\b" + re.escape(a) + r"s?\b" for a in acronyms]
    pats += [r"(?i:\b" + v + r"\b)" for v in NAME_VARIANTS.get(policy.id, ())]
    return pats


def name_rules(policies: Sequence[Policy], codes: Mapping[str, str]) -> Callable[[str], str]:
    """Rule 3 as one function: one pass, longest pattern first, so replacements never chain."""
    pairs = sorted(
        ((pat, codes[p.id]) for p in policies for pat in _patterns(p)),
        key=lambda pc: -len(pc[0]),
    )
    combined = re.compile("|".join(f"(?P<g{i}>{pat})" for i, (pat, _) in enumerate(pairs)))
    code_of = {f"g{i}": code for i, (_, code) in enumerate(pairs)}
    return lambda text: combined.sub(lambda m: code_of[m.lastgroup], text)


_SUFFIX = re.compile(r"\(([^()]*)\)\s*$")


def _relabel(line: str, title_re: re.Pattern, label: Mapping[str, str]) -> str:
    """Titles in a source line or the overlap line, or a heading's trailing (title) only."""
    sub = lambda s: title_re.sub(lambda m: label[m.group(0)], s)  # noqa: E731
    if _SOURCE.match(line) or _OVERLAP in line:
        return sub(line)
    if line.startswith("## ") and (m := _SUFFIX.search(line)):
        return line[: m.start()] + "(" + sub(m.group(1)) + ")" + line[m.end() :]
    return line


def denamed_packet(
    text: str, policy_id: str, policies: Sequence[Policy], codes: Mapping[str, str]
) -> str:
    if policy_id not in codes:
        raise ValueError(f"unknown policy {policy_id!r}")
    code = codes[policy_id]
    out = _HEADER.sub(f"# Evidence packet: {code}", text, count=1)
    titles = list(dict.fromkeys(_SOURCE.findall(out)))
    if titles:
        title_re = re.compile("|".join(re.escape(t) for t in sorted(titles, key=len, reverse=True)))
        label = {t: f"{code} source {k}" for k, t in enumerate(titles, start=1)}
        out = "\n".join(_relabel(ln, title_re, label) for ln in out.split("\n"))
    return name_rules(policies, codes)(out)
