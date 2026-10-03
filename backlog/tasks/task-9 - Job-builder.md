---
id: TASK-9
title: Job builder
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:07'
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
- [ ] #4 Supports the paper format (all 11 policies in one prompt) as the default, and a one-policy-per-call mode as a later variant
- [ ] #5 Job count per configuration is reported (about 15 criteria x 11 policies x 51 personas, roughly 8,400 calls at baseline)
<!-- AC:END -->
