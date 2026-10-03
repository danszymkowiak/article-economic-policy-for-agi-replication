---
id: TASK-22
title: Adversarial arm
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase4
dependencies:
  - TASK-21
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Kept separate from the main results so it is not confused with them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Lives in its own directory and is clearly labeled adversarial
- [ ] #2 Searches for the smallest plausible change that moves a policy from top to bottom
<!-- AC:END -->
