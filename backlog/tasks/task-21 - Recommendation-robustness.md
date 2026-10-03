---
id: TASK-21
title: Recommendation robustness
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
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
- [ ] #1 For each configuration, report whether the three-stage sequence (UI/EITC -> NIT -> UBC) holds
<!-- AC:END -->
