---
id: TASK-3
title: Domain dataclasses
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:14'
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
- [x] #1 Frozen dataclasses exist for Persona, Policy, Criterion, RunSpec, RenderedJob and Rating
- [x] #2 Domain package performs no I/O and has unit tests
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Tests first: frozen dataclasses (Persona, Policy, Criterion, RunSpec, RenderedJob, Rating), validation, AST no-I/O scan of domain package
2. Implement src/llm_panel/domain/models.py
3. RenderedJob.job_id delegates to hashing (task 4)
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added frozen dataclasses in llm_panel.domain.models with validation and dict round-trip for RenderedJob. Verified: 20 tests pass incl. frozen-ness check and AST scan forbidding I/O imports/calls in the domain package.
<!-- SECTION:FINAL_SUMMARY:END -->
