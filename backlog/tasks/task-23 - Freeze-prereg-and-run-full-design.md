---
id: TASK-23
title: Freeze prereg and run full design
status: Done
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-05 22:06'
labels:
  - phase5
dependencies:
  - TASK-22
  - TASK-13
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Final paid run; total spend including prior runs must not exceed max_spend_usd = 15, so the full design must be sized to fit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 prereg is frozen and the commit tagged
- [x] #2 Design run as amended in prereg s13 (2026-10-05 deviation): R (B x5, B'), Q1, Q4, D2 run and collected, plus the partial Q3c (100 calls); units not run (Q2, rest of Q3, R-T, D2b, D1, D3) reported as not run, with budget as the reason
- [x] #3 Before each submit, plan's estimate for the unit is checked against the budget left under the ceiling (per-unit, as amended in prereg s13); the full design did not fit, as s13 records
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: prereg TODOs to decide before tagging frozen: factor levels (models, paraphrases, order, aggregation), temperature levels, repeats, fraction run count and seed, bootstrap resample count, variance-decomposition method, recommendation-survival rule, budget-binding priority order, adversarial-arm procedure (also TASK-22). Raw results are gitignored (results/raw/*); decide redistribution at write-up after checking provider terms.

2026-10-04: also waits on TASK-13 (additional providers) for the D3 second-model cell.

2026-10-05: Run stopped per s13 deviation (commit 4af5964). Run: R (B x5, B'), Q1, Q4, D2 complete; Q3c 100 jobs partial; Q2, Q3, R-T, D2b, D1, D3 not run (budget). Spend 11.95 USD actual + 0.13 other ledgers; 2.93 left (2.50 adversarial reserve). Analyses run (analyze baseline/ranks --resamples 2000 --seed 0/variance/recommendations/materiality) into analysis/*. Gaps found: D2 common-complete rule drops ubi/sawf/ubc entirely (6 failed repeats), survivor-only and worst-case bounds (prereg s7) not implemented, ranks report text still says s12 item 6 open.

2026-10-06 closed (user left the call to the implementer). Original AC #3 read 'Full design is run and collected'; it cannot be met within the 15 USD ceiling and was replaced by the s13-amended scope, which the write-up (writeup/draft.md) reports as a post-freeze deviation. Evidence: prereg-v1 tag on 5a30367; per-unit plan estimates checked against the remaining budget before each submit (s13 execution entries, ratio-adjusted); analysis/missing/missing_data.md lists every run cell and its failures. Global spend 14.14 of 15 USD.

Original AC #2 read 'plan --dry-run shows the full design fits within the remaining budget before submit'; the full design did not fit (s13), so it was replaced by the per-unit check that was actually made.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Prereg frozen and tagged (prereg-v1); main run executed in priority units with per-unit budget checks, stopped under the s13 deviation after R, Q1, Q4 and D2 (Q3c partial). Remaining units not run for budget, reported as such in the write-up.
<!-- SECTION:FINAL_SUMMARY:END -->
