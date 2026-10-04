"""Load the transcribed published scores (analysis/published/paper_table4.csv).

Leading `#` lines are provenance and are kept verbatim; the rest is a CSV with one row per policy
and one column per criterion id (plus the survey's net approval).
"""

from __future__ import annotations

import csv
from pathlib import Path

from llm_panel.domain.analysis_baseline import NET_APPROVAL, PublishedTable

__all__ = ["NET_APPROVAL", "PublishedTable", "load_published"]


def load_published(path: Path | str) -> PublishedTable:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    provenance = tuple(ln.lstrip("# ").rstrip() for ln in lines if ln.startswith("#"))
    rows = list(csv.DictReader(ln for ln in lines if ln and not ln.startswith("#")))
    if not rows:
        raise ValueError(f"{path}: no published rows")
    columns = [c for c in rows[0] if c != "policy_id"]
    scores = {c: {r["policy_id"]: float(r[c]) for r in rows} for c in columns}
    return PublishedTable(provenance, scores, tuple(r["policy_id"] for r in rows))
