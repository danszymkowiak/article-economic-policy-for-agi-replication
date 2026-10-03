---
id: TASK-9
title: Job builder
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-8
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 RunSpec x persona x policy x criterion x repeat yields RenderedJobs
- [ ] #2 Jobs whose job_id already exists in the store are skipped
- [ ] #3 Tests cover skipping and resumption
<!-- AC:END -->
