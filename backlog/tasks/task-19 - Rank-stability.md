---
id: TASK-19
title: Rank stability
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
labels:
  - phase4
dependencies:
  - TASK-18
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Kendall tau computed between configurations
- [ ] #2 Bootstrap confidence intervals reported
- [ ] #3 Alternative score aggregations (e.g. mean, median, trimmed mean) compared for rank stability
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: read only from results/raw; count only status ok rows as ratings; treat deferred rows as budget-censored (not run), failed as model failures, duplicate as ignored; report the counts of each.
<!-- SECTION:NOTES:END -->
