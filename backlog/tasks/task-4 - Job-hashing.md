---
id: TASK-4
title: Job hashing
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-3
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Content-addressed job ids make runs resumable and de-duplicated.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 job_id = sha256(rendered prompt + model snapshot + temperature + seed)
- [ ] #2 Property tests: identical inputs give the same id; changing any component gives a new id
<!-- AC:END -->
