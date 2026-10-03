---
id: TASK-18
title: Baseline comparison to published tables
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase4
dependencies:
  - TASK-17
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Our baseline configuration is compared against the essay published tables
- [ ] #2 Agreement is reported as rank correlation, not exact match
- [ ] #3 Report states that any gap may come from the reconstruction as well as from instability
<!-- AC:END -->
