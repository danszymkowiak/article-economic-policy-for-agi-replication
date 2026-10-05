---
id: TASK-23
title: Freeze prereg and run full design
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-05 15:18'
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
- [ ] #1 prereg is frozen and the commit tagged
- [ ] #2 plan --dry-run shows the full design fits within the remaining budget before submit
- [ ] #3 Full design is run and collected
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: prereg TODOs to decide before tagging frozen: factor levels (models, paraphrases, order, aggregation), temperature levels, repeats, fraction run count and seed, bootstrap resample count, variance-decomposition method, recommendation-survival rule, budget-binding priority order, adversarial-arm procedure (also TASK-22). Raw results are gitignored (results/raw/*); decide redistribution at write-up after checking provider terms.

2026-10-04: also waits on TASK-13 (additional providers) for the D3 second-model cell.

2026-10-05: Run stopped per s13 deviation (commit 4af5964). Run: R (B x5, B'), Q1, Q4, D2 complete; Q3c 100 jobs partial; Q2, Q3, R-T, D2b, D1, D3 not run (budget). Spend 11.95 USD actual + 0.13 other ledgers; 2.93 left (2.50 adversarial reserve). Analyses run (analyze baseline/ranks --resamples 2000 --seed 0/variance/recommendations/materiality) into analysis/*. Gaps found: D2 common-complete rule drops ubi/sawf/ubc entirely (6 failed repeats), survivor-only and worst-case bounds (prereg s7) not implemented, ranks report text still says s12 item 6 open.
<!-- SECTION:NOTES:END -->
