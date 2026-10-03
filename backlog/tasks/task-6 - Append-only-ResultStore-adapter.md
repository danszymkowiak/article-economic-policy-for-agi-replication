---
id: TASK-6
title: Append-only ResultStore adapter
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-5
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Raw results are the source of truth for all analysis and must never be lost; spend tracking later relies on stored usage fields.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 JSONL/Parquet ResultStore never overwrites or deletes rows
- [ ] #2 Each row stores full request, full response (including usage fields), model snapshot string, sampling params, timestamp and status
- [ ] #3 Tests cover append, exists and iteration
<!-- AC:END -->
