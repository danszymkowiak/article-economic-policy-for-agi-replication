---
id: TASK-5
title: 'Ports: ModelClient and ResultStore'
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:15'
labels:
  - phase1
dependencies:
  - TASK-4
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ModelClient port defines submit_batch and fetch_results
- [x] #2 ResultStore port defines append, exists and iter_rows
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. domain/results.py: ModelResponse, BatchResult, StoredRow (is_terminal)
2. ports.py: ModelClient (submit_batch, fetch_results), ResultStore (append, exists, iter_rows), BatchLedger (support for task 10)
3. Tests: runtime_checkable conformance with in-test stubs, signature names
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added BatchLedger port and domain/results.py (ModelResponse, BatchResult, StoredRow, MAX_ATTEMPTS=2) beyond the AC, needed by tasks 6-10. ResultStore.exists means a terminal row exists.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
ports.py defines ModelClient(submit_batch, fetch_results), ResultStore(append, exists, iter_rows), plus BatchLedger. Verified: 35 tests pass incl. port method-set assertions and stub conformance.
<!-- SECTION:FINAL_SUMMARY:END -->
