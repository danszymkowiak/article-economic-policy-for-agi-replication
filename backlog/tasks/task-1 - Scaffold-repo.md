---
id: TASK-1
title: Scaffold repo
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:12'
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
- [x] #1 pyproject.toml managed with uv, src/ layout, pytest, ruff and pre-commit configured and passing on an empty test
- [x] #2 README stub exists
- [x] #3 Folders exist: prereg/, personas/, prompts/, evidence/, results/raw/, analysis/
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. uv init (python 3.14, src layout, package llm_panel)
2. Add pytest, ruff, pre-commit dev deps and config
3. Empty smoke test passes; ruff + pre-commit pass
4. Create folders with .gitkeep; README stub already exists
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
uv project (python 3.14, package llm_panel, uv_build). pytest/ruff/pre-commit(local hooks via uv run)/hypothesis dev deps. Smoke test, ruff check/format and pre-commit pass.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Scaffolded uv src-layout project with pytest, ruff, pre-commit, required folders. Verified: pytest 1 passed, ruff check/format and pre-commit run all passed.
<!-- SECTION:FINAL_SUMMARY:END -->
