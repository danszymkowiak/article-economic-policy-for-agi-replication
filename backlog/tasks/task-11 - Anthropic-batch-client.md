---
id: TASK-11
title: Anthropic batch client
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase2
dependencies:
  - TASK-10
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. First real provider; real money starts here, so spend tracking must be correct.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Exact model snapshot strings are pinned, never "latest"
- [ ] #2 Responses are validated against a JSON schema (score 0-100 + short rationale)
- [ ] #3 Malformed responses are retried once, then logged as failures and never dropped
- [ ] #4 Actual spend is computed from each response usage fields and added to the cumulative spend ledger
- [ ] #5 Budget ceiling from the CLI task is enforced for this client
<!-- AC:END -->
