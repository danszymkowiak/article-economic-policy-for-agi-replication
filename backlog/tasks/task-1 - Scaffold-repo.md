---
id: TASK-1
title: Scaffold repo
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase0
dependencies: []
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Working vertical slice first; study design is frozen before any paid call.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pyproject.toml managed with uv, src/ layout, pytest, ruff and pre-commit configured and passing on an empty test
- [ ] #2 README stub exists
- [ ] #3 Folders exist: prereg/, personas/, prompts/, evidence/, results/raw/, analysis/
<!-- AC:END -->
