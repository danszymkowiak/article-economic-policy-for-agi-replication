---
id: TASK-21
title: Recommendation robustness
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 09:01'
labels:
  - phase4
dependencies:
  - TASK-20
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 For each configuration, report whether the three-stage sequence (UI/EITC -> NIT -> UBC) holds
- [x] #2 Report whether recommendations follow from the scores, e.g. UBS leads on durability yet is absent from the sequence, NIT recommended despite low political support
- [x] #3 Report how blinding policy names changes UBC versus Sovereign AI Fund on Ownership of Gains
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Domain (pure) src/llm_panel/domain/analysis_recommend.py: prereg s6 clauses (a)-(d) with continuous margins (score minus k-th best other; holds iff margin > 0), three-stage sequence = (a) and (c) and (d), score-consistency checks (durability leaders vs the sequence, UBS leads yet absent, NIT political support rank vs clause c, ALMP Mild rank), UBC - SAWF ownership gap, r(net approval, Full) and r(Readiness, Full), per-cell analysis (repeat mean + single runs, flips vs B repeat mean on the aligned common-complete set) and B noise floor (single runs, k-split flip rates, gap band).
2. Application recommendations.py: read cells via cell_observations, render Markdown + CSVs (clauses, consistency, blinding), NON-INFERENCE label, wording rule, whole ranges across cells.
3. CLI: llm-panel analyze recommendations [--out analysis/recommendations] [--published ...] (net approval is a fixed survey input).
4. Tests first: synthetic scores/rows engineered so each clause holds/fails; published Table 4 passes all clauses.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: read only from results/raw; count only status ok rows as ratings; treat deferred rows as budget-censored (not run), failed as model failures, duplicate as ignored; report the counts of each.

Implemented domain/analysis_recommend.py (pure), application/recommendations.py, CLI 'analyze recommendations' (--published used only for the fixed net-approval survey input). Decisions: margin = score minus k-th best other (holds iff > 0; ties fail); sequence = (a) and (c) and (d); flips vs B repeat mean on the aligned common-complete set (TASK-19 align_cells); B noise floor = B single runs vs B mean plus k-split disagreement shares; consistency checks (leaders, UBS, NIT political support rank below median, ALMP Mild rank) labelled exploratory. Prereg s6 (c) margin 3.8 is the gap to rank 3 (UBC 66.0); the top-3 margin is 3.9 (UI 65.9), reported in the report. Tier changes (s6 1b) not computed: the paper defines no tiers (open prereg item). Status counts still ok / not ok only (deferred/failed/duplicate split is the open follow-up from TASK-19/20). Validation: uv run pytest -q 522 passed (21 new); ruff clean; pilot store run to scratchpad only (non-inference).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added llm-panel analyze recommendations: per cell and per single run, the four prereg s6 clauses with continuous margins and flips against B's repeat mean, the three-stage sequence (a)+(c)+(d) (AC1), score consistency (durability leaders vs the sequence, UBS leading yet absent, NIT recommended despite low panel political support, ALMP Mild rank; AC2, exploratory), the UBC minus SAWF Ownership of Gains gap in Q1 versus B with a B k-split noise band and every cell's gap (AC3), r(approval, Full) and r(Readiness, Full) per cell. Writes recommendations.md plus 4 CSVs under analysis/recommendations, with the wording rule and whole ranges across cells. Verified by 21 new tests on engineered synthetic scores/rows (each clause holding and failing, ties, missing policies, published Table 4 passing all clauses with margins 15.5/40.0/3.9/5.9, blinding flip, noise splits, CLI); full suite 522 passed.
<!-- SECTION:FINAL_SUMMARY:END -->
