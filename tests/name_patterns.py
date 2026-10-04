"""Every name, short name and acronym that would identify a study policy. Description-only (Q1)
text must contain none of them: the rendered prompt (TASK-16) and the evidence packets
(TASK-33). Lower-case patterns match case-insensitively, the others case-sensitively."""

import re

NAME_PATTERNS = (
    r"earned income", r"\bEITC\b", r"unemployment insurance", r"\bUI\b", r"active labou?r",
    r"\bALMPs?\b", r"wage insurance", r"industrial policy", r"jobs? guarantee", r"\bFJG\b",
    r"basic income", r"\bUBI\b", r"negative income tax", r"\bNIT\b", r"basic services",
    r"\bUBS\b", r"basic capital", r"\bUBC\b", r"sovereign", r"\bSAWF\b", r"AI fund",
    r"AI dividend", r"earned income credit", r"\bEICs?\b", r"\bSWFs?\b",
)  # fmt: skip


def names_found(text: str) -> list[str]:
    return [
        m.group(0)
        for pat in NAME_PATTERNS
        for m in re.finditer(pat, text, re.IGNORECASE if pat.islower() else 0)
    ]
