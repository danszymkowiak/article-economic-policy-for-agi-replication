---
id: TASK-3
title: Domain dataclasses
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase1
dependencies:
  - TASK-2
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. No I/O in the domain layer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Frozen dataclasses exist for Persona, Policy, Criterion, RunSpec, RenderedJob and Rating
- [ ] #2 Domain package performs no I/O and has unit tests
<!-- AC:END -->
