---
id: TASK-10
title: 'CLI: plan, submit, collect, status'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-9
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Budget is tight: the user is token-limited, so the ceiling is enforced in code, not by convention.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Config key max_spend_usd = 15
- [ ] #2 `plan --dry-run` prints job count and estimated cost per provider and exits
- [ ] #3 `submit` refuses to run without --confirm
- [ ] #4 `submit` refuses any job set whose estimated cost plus cumulative actual spend exceeds max_spend_usd
- [ ] #5 `status` shows cumulative spend versus the ceiling
- [ ] #6 Tests cover the refusal paths using FakeModelClient
<!-- AC:END -->
