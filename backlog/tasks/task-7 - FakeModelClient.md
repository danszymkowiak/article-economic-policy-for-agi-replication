---
id: TASK-7
title: FakeModelClient
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:16'
labels:
  - phase1
dependencies:
  - TASK-6
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Used for all tests and dry runs so no money is spent.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 FakeModelClient implements ModelClient and returns deterministic scores
- [x] #2 Fake responses include synthetic usage fields so spend tracking can be tested
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. domain/schema.py: RESPONSE_SCHEMA (ratings: label, score 0-100, rationale)
2. adapters/fake_client.py: deterministic scores from hash, synthetic usage, injectable malformed/error/pending behaviour
3. Tests incl. schema validity and determinism
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Response format fixed in domain/schema.py: {ratings:[{policy,score,rationale}]} where policy is the label shown in the prompt. Fake supports injected malformed/error/pending behaviour for retry tests.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
FakeModelClient (deterministic hash-based scores, synthetic usage input/output tokens) plus RESPONSE_SCHEMA. Verified: 51 tests pass; responses validate against the schema, identical across instances, usage fields present.
<!-- SECTION:FINAL_SUMMARY:END -->
