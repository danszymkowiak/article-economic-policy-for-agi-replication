---
id: TASK-12
title: 'Pilot: 20 jobs end to end'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase2
dependencies:
  - TASK-11
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Validates the full pipeline cheaply before scaling; must stay well inside the 15 USD ceiling.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 20 jobs run through plan -> submit -> collect
- [ ] #2 Raw rows and the failure rate are shown to the user
- [ ] #3 Actual pilot spend is reported against max_spend_usd
<!-- AC:END -->
