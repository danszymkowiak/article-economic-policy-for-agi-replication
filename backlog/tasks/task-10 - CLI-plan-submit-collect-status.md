---
id: TASK-10
title: 'CLI: plan, submit, collect, status'
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:21'
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
- [x] #1 Config key max_spend_usd = 15
- [x] #2 `plan --dry-run` prints job count and estimated cost per provider and exits
- [x] #3 `submit` refuses to run without --confirm
- [x] #4 `submit` refuses any job set whose estimated cost plus cumulative actual spend exceeds max_spend_usd
- [x] #5 `status` shows cumulative spend versus the ceiling
- [x] #6 Tests cover the refusal paths using FakeModelClient
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. domain/pricing.py (SpendSettings, cost estimate, usage cost, missing-price refusal) + domain/validation.py (schema + label check)
2. bootstrap/config.py (max_spend_usd=15, hard ceiling 15 enforced on load, approved_providers, prices) and inputs_loader
3. application: spend.py (actual + outstanding + new estimate vs ceiling), submit.py, collect.py (validate, retry once, spend-checked), status.py
4. bootstrap/cli.py: plan --dry-run | submit --confirm | collect | status, injectable client factory; fake client optional persistent state
5. Tests for refusal paths with FakeModelClient; fake input fixtures in designs/fake_inputs
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Guards run before any batch is sent: --confirm, approved_providers (extra), price present, then ceiling = actual stored spend + outstanding in-flight estimates + new estimate. Config rejects max_spend_usd > 15. collect validates (schema + labels), retries malformed/errored once (itself ceiling-checked; blocked retry is logged as failed), logs failures. Fake client can persist state so submit/collect work across processes. See TODO.md for open items.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CLI (plan --dry-run, submit --confirm, collect, status) with spend-ceiling enforcement, application layer (spend/submit/collect/status), config and inputs loaders. Verified: 112 tests pass including refusal paths via FakeModelClient (no --confirm, estimate over ceiling, cumulative actual spend, unapproved provider, missing price) and retry/failure paths; real CLI smoke run on a scratch copy with the fake provider.
<!-- SECTION:FINAL_SUMMARY:END -->
