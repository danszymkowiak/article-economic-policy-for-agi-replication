---
id: TASK-23
title: Freeze prereg and run full design
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase5
dependencies:
  - TASK-22
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
