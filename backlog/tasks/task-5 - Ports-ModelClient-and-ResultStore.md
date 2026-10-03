---
id: TASK-5
title: 'Ports: ModelClient and ResultStore'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-4
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ModelClient port defines submit_batch and fetch_results
- [ ] #2 ResultStore port defines append, exists and iter_rows
<!-- AC:END -->
