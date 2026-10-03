---
id: TASK-11
title: Anthropic batch client
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md (tasks 1-10 close-out): (1) pin real snapshots and prices in config.yaml, and add a code check that a snapshot is a pinned version, not an alias (rule is provider-specific, so write it against the provider's docs); (2) cap max_tokens in the client so the output-cost estimate is a true upper bound; (3) price cached/reasoning tokens that providers report separately; (4) ambiguous submit errors (timeout after the batch was created) are recorded as submit_failed and could be paid twice: tag batches with the job-set hash as metadata and reconcile against the provider's batch list before resubmitting; (5) confirm with user before the first paid call on this provider.
<!-- SECTION:NOTES:END -->
