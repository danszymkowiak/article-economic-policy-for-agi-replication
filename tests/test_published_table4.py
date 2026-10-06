"""The transcribed published scores match the SSRN PDF, value by value (TASK-18).

The PDF is not redistributed: place it at `docs/economic-policy-for-agi-ssrn.pdf` (sha256 in the
README) to run these tests. The text comes from `pdftotext -layout`; the tests are skipped where
the PDF is missing or poppler is not installed.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from llm_panel.bootstrap.published_loader import NET_APPROVAL, load_published

REPO = Path(__file__).parents[1]
PDF = REPO / "docs" / "economic-policy-for-agi-ssrn.pdf"
CSV = REPO / "analysis" / "published" / "paper_table4.csv"

# Table 4 column order (Living ... Ready, Net App., Mild, Mod., Trans.)
TABLE4_COLUMNS = (
    "standards_of_living", "meaning_human_value", "macro_stabilisation",
    "economic_agency_mobility", "ownership_of_gains", "democratic_voice",
    "economic_feasibility", "implementation_readiness", NET_APPROVAL,
    "mild_disruption", "moderate_disruption", "full_transformation",
)  # fmt: skip
APPENDIX_B_LABELS = {
    "Standards of Living": "standards_of_living",
    "Meaning & Value": "meaning_human_value",
    "Macro Stabilization": "macro_stabilisation",
    "Economic Agency": "economic_agency_mobility",
    "Ownership of Gains": "ownership_of_gains",
    "Democratic Voice": "democratic_voice",
    "Economic Feasibility": "economic_feasibility",
    "Impl. Readiness": "implementation_readiness",
    "Public Net Approval": NET_APPROVAL,
    "Mild Disruption": "mild_disruption",
    "Moderate Disruption": "moderate_disruption",
    "Full Transformation": "full_transformation",
}
TABLE3_NAMES = {
    "eitc": "Earned Income Tax Credit (EITC)",
    "ui": "Unemployment Insurance (UI)",
    "almp": "Active Labour-Market Policies (ALMP)",
    "wage_insurance": "Wage Insurance",
    "directed_industrial_policy": "Directed Industrial Policy",
    "fjg": "Federal Jobs Guarantee (FJG)",
    "ubi": "Universal Basic Income (UBI)",
    "nit": "Negative Income Tax (NIT)",
    "ubs": "Universal Basic Services (UBS)",
    "ubc": "Universal Basic Capital (UBC)",
    "sawf": "Sovereign AI Fund / Dividend (SAWF)",
}
NUMBER = re.compile(r"[+-]?\d+\.\d")


@pytest.fixture(scope="module")
def paper_text():
    if not PDF.exists():
        pytest.skip(f"{PDF.relative_to(REPO)} not present (not redistributed; see README)")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext (poppler) not installed")
    out = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True
    )
    return out.stdout


@pytest.fixture(scope="module")
def published():
    return load_published(CSV)


def _table4(text):
    start = text.index("Table 4. Evaluation of Household-Facing Mitigation Policies")
    return text[start : text.index("Notes: All panel criteria", start)]


def _appendix_b(text):
    start = text.index("Appendix B: Policy-by-Policy Evaluation Profiles")
    body = text[start : text.index("Appendix C:", start)]
    sections = re.split(r"^B\.\d+\. ", body, flags=re.MULTILINE)[1:]
    return {s.splitlines()[0].split("  ")[0].strip(): s for s in sections}


def test_csv_holds_11_policies_by_12_columns_with_provenance(published):
    assert set(published.scores) == set(TABLE4_COLUMNS)
    for column in TABLE4_COLUMNS:
        assert set(published.scores[column]) == set(TABLE3_NAMES)
    provenance = " ".join(published.provenance)
    assert "SSRN abstract 7470000" in provenance
    assert "Table 4" in provenance and "Appendix B" in provenance
    assert "retrieved 2026-10-04" in provenance


def test_every_value_matches_table4(paper_text, published):
    lines = _table4(paper_text).splitlines()
    for policy_id, name in TABLE3_NAMES.items():
        (line,) = [ln for ln in lines if ln.strip().startswith(name)]
        values = [float(v) for v in NUMBER.findall(line[line.index(name) + len(name) :])]
        assert len(values) == len(TABLE4_COLUMNS), line
        for column, value in zip(TABLE4_COLUMNS, values, strict=True):
            assert published.scores[column][policy_id] == value, (policy_id, column)


def test_every_value_matches_appendix_b(paper_text, published):
    sections = _appendix_b(paper_text)
    assert set(sections) == set(TABLE3_NAMES.values())
    for policy_id, name in TABLE3_NAMES.items():
        found = {}
        for line in sections[name].splitlines():
            for label, value in re.findall(r"([A-Z][A-Za-z.& ]*?)†?\s+([+-]?\d+\.\d)%?", line):
                if label.strip() in APPENDIX_B_LABELS:
                    found[APPENDIX_B_LABELS[label.strip()]] = float(value)
        assert set(found) == set(TABLE4_COLUMNS), (name, sorted(found))
        for column, value in found.items():
            assert published.scores[column][policy_id] == value, (policy_id, column)
