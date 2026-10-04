---
id: TASK-18
title: Baseline comparison to published tables
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 08:22'
labels:
  - phase4
dependencies:
  - TASK-12
  - TASK-17
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Our baseline configuration is compared against the essay published tables
- [x] #2 Agreement is reported as rank correlation, not exact match
- [x] #3 Report states that any gap may come from the reconstruction as well as from instability
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Transcribe Table 4 / Appendix B (11 policies x 11 panel criteria + net approval) into analysis/published/paper_table4.csv with provenance header; test verifies every value against pdftotext of the committed SSRN PDF (Table 4 rows and each B.k profile).
2. Domain (pure) src/llm_panel/domain/analysis_baseline.py: average ranks, Spearman, Kendall tau-b, Table 4 composites (11 single criteria + welfare, agency, feasibility = Econ.F + Readiness, durability mean), common-complete repeat-mean panel means, per-composite agreement (Spearman, Kendall, MAD).
3. Application src/llm_panel/application/baseline_comparison.py: cell B observations from ResultStore ok rows; report rendering (Markdown + CSV) with AC3 caveat and the precision-not-wrongness wording.
4. Bootstrap: published CSV loader; CLI 'llm-panel analyze baseline --published ... --out ...'; non-inference store label when the store is not results/raw. Gitignore generated analysis outputs.
5. Tests first throughout; full suite; commit.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-04: depends on the pilot (analysis is developed on pilot and smoketest data) as well as the evidence packets.

Implemented: analysis/published/paper_table4.csv (11 policies x 11 panel criteria + net approval, provenance header: SSRN abstract 7470000, Table 4 p.14 and Appendix B pp.35-38, PDF sha256, retrieved 2026-10-04); tests/test_published_table4.py checks every value against pdftotext of the committed PDF, both Table 4 and each B.k profile (skips if poppler is missing; a mutated value fails both tests). Domain analysis_baseline.py (pure): average ranks, Spearman, Kendall tau-b (checked against scipy reference values), Table 4 composites, common-complete repeat-mean panel, per-composite agreement. Application baseline_comparison.py reads ok cell B rows via the ResultStore port and renders Markdown + two CSVs. CLI: llm-panel --config <cfg> analyze baseline [--published ...] [--out analysis/baseline]; reports from a store other than results/raw are labeled NON-INFERENCE. Generated analysis/* is gitignored except analysis/published/. No new dependencies.
Composite reading (recorded in code and report): Feasibility = Economic Feasibility + Implementation Readiness only (the two Table 4 Feasibility columns); Political Support and Admin Capacity & Speed are rated but not compared; net approval is survey data, not compared. Scenario Durability = mean of 3 scenarios (paper text: ALMP 23 on average). The essay's Feasibility composite is the mean of six columns (EITC 79.8), so it is not comparable to ours.
Ran on the pilot store (non-inference, output to scratchpad only): 20 cell B jobs, all 15 composites computed; numbers not recorded here as they are pilot data.
Not done (out of brief): comparison with the essay's composite tables (prereg s6 mentions 'Table 4 and the essay'; reconstruction R8 verification of composites against the essay).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Baseline B versus the paper's published Table 4 / Appendix B: transcribed published scores with provenance (verified value by value against the committed SSRN PDF in a test), pure rank statistics (Spearman, Kendall tau-b, mean abs. difference) per Table 4 composite, and an 'llm-panel analyze baseline' command that reads only the configured raw store and writes Markdown + CSV reports. The report states agreement as rank correlation, not exact match, and that any gap may come from the reconstruction as well as from instability. Verified with uv run pytest -q (464 passed), including tests/test_published_table4.py, tests/domain/test_analysis_baseline.py and tests/test_baseline_comparison.py (AC1: comparison run end to end from synthetic store rows; AC2: Spearman/Kendall reported and recover rank 1.0 on published-equal data; AC3: report wording asserted).
<!-- SECTION:FINAL_SUMMARY:END -->
