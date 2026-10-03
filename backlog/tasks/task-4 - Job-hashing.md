---
id: TASK-4
title: Job hashing
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:15'
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
- [x] #1 job_id = sha256(rendered prompt + model snapshot + temperature + seed)
- [x] #2 Property tests: identical inputs give the same id; changing any component gives a new id
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Property tests (hypothesis): same inputs -> same id; changing prompt/snapshot/temperature/seed -> new id; no concatenation ambiguity
2. domain/hashing.py job_id() over canonical JSON encoding; RenderedJob.job_id property
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Encoding is JSON list [prompt, snapshot, float(temp), int(seed)] (unambiguous vs raw concatenation); int/float temperature normalised.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
domain/hashing.job_id + RenderedJob.job_id. Verified: hypothesis property tests (same inputs same id; each component change new id; no concatenation ambiguity) - 29 tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
