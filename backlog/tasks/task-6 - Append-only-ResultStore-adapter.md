---
id: TASK-6
title: Append-only ResultStore adapter
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:16'
labels:
  - phase1
dependencies:
  - TASK-5
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Raw results are the source of truth for all analysis and must never be lost; spend tracking later relies on stored usage fields.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 JSONL/Parquet ResultStore never overwrites or deletes rows
- [x] #2 Each row stores full request, full response (including usage fields), model snapshot string, sampling params, timestamp and status
- [x] #3 Tests cover append, exists and iteration
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Tests: append/exists/iter, persistence across instances, bytes never change, no update/delete API, all required fields round-trip
2. adapters/jsonl.py: JsonlResultStore + JsonlBatchLedger (O_APPEND single write, fsync); corrupt line raises, never skipped
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
JSONL only (Parquet deferred; analysis can convert from JSONL). exists() caches a terminal-id index per instance; assumes a single writer process.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
adapters/jsonl.py: JsonlResultStore (append/exists/iter_rows, no mutation API) and JsonlBatchLedger. Verified: 44 tests pass incl. byte-prefix-preserved-on-append, persistence, full-field round trip, corrupt-line raises.
<!-- SECTION:FINAL_SUMMARY:END -->
