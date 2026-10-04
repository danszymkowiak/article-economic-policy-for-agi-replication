---
id: TASK-20
title: Variance decomposition
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 08:49'
labels:
  - phase4
dependencies:
  - TASK-19
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Persona, prompt, model, evidence and repeat noise decomposed (mixed-effects or ANOVA)
- [x] #2 Report states how much variance persona explains
- [x] #3 Effective sample size of the persona panel estimated from the persona variance share
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Domain (pure, numpy): src/llm_panel/domain/analysis_variance.py with a balanced crossed random-effects ANOVA (method of moments, EMS solved by Moebius inversion over factor subsets; top interaction confounded with residual; negatives reported, truncated at 0 for shares).
2. (a) Within each persona cell (B primary): 4-way persona x policy x criterion x repeat decomposition on personas complete in every triplet; persona share (main and all persona terms); per policy x criterion persona x repeat ANOVA (persona share, run-shared ICC, n_eff = n/(1+(n-1)ICC)); per criterion persona x policy x repeat agreement ICC and n_eff (H4 reading). Full ranges.
3. (b) Each varied cell versus B at panel-mean level (policy x criterion units): level shift, unit-specific shift variance net of repeat noise (MS_unit x repeat / k on each side), as multiple of B's single-run and panel-mean noise; B split null band for the same k. Factor label per cell; identifiable vs not stated in report.
4. Application: src/llm_panel/application/variance.py reusing cell_observations/build_cell_array; Markdown + CSVs; CLI llm-panel analyze variance --out analysis/variance.
5. Tests first: planted variance shares recovered within tolerance, exact persona-only case, n_eff formula, cell shift recovery and null band, report wording, CLI.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: read only from results/raw; count only status ok rows as ratings; treat deferred rows as budget-censored (not run), failed as model failures, duplicate as ignored; report the counts of each.

Implemented domain/analysis_variance.py (balanced crossed random-effects ANOVA by method of moments, Moebius inversion of EMS; within-cell 4-way decomposition; per policy x criterion persona share, run-shared ICC and n_eff; per criterion agreement ICC and n_eff; factor_shift of each varied cell vs B at panel-mean level against repeat noise with B split band), application/variance.py (report + 4 CSVs) and CLI 'llm-panel analyze variance --out analysis/variance'. align_cells (analysis_rank) and report_order (rank_stability) made public for reuse. No new dependency (numpy only). Identifiability stated in the report: factor x factor interactions not identifiable (one-at-a-time); persona x factor not estimated. Status counts remain ok / not ok only (CellCounts reused; deferred/duplicate split not done, as in TASK-19). Validation: uv run pytest -q 501 passed; ruff clean; pilot store run (non-inference, scratchpad output) completes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Variance decomposition: method-of-moments variance components (persona, policy, criterion, repeat and interactions) within each cell, persona variance share (overall and per policy x criterion, full range), effective number of raters n_eff = n/(1+(n-1)icc) from run-shared and agreement ICCs, and each varied factor (prompt wording Q1-Q3, evidence Q4, temperature, model D3, persona D2/D2b, scoring D1) as a shift beyond B's repeat noise with a B split band. CLI llm-panel analyze variance writes variance.md and four CSVs. Verified by tests with planted variance shares recovered within tolerance (tests/domain/test_analysis_variance.py, tests/test_variance.py); full suite 501 passed.
<!-- SECTION:FINAL_SUMMARY:END -->
