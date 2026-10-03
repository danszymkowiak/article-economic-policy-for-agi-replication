---
id: TASK-11
title: 'Study-model readiness on OpenCode Zen (prices, aliases, global spend)'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:27'
labels:
  - phase2
dependencies:
  - TASK-10
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Originally "Anthropic batch client". The user has no Anthropic account and uses OpenCode Zen credits, so the Zen client was built as TASK-27 and this task now covers what is still needed before real study runs spend money. Zen model ids are aliases (CLAUDE.md says to pin snapshots, which Zen cannot do), prices must be real and dated, and the 15 USD hard ceiling is currently enforced per ledger, so smoketest and study ledgers do not add up. Generic schema validation, retry-once and the ceiling guard were delivered by TASK-7/10 and TASK-27.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Study model(s) on Zen are chosen with the user, and their list prices are recorded in config.yaml with the date and source
- [ ] #2 The alias limitation is resolved with the user and written into the prereg limitations: the response-reported model id is stored per row, and a check flags rows whose reported id differs from the requested one or changes during the study
- [ ] #3 Cached and reasoning tokens are verified against real Zen usage fields, and cost estimates and actuals cover them (tests added)
- [ ] #4 A request that timed out (possibly billed, not retried) is charged at the estimate and counted toward the ceiling, covered by a test
- [ ] #5 The 15 USD hard ceiling is enforced across all ledgers (study, smoketest, pilot), not per ledger, with tests
- [ ] #6 User confirms before the first paid study call
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md (tasks 1-10 close-out): (1) pin real snapshots and prices in config.yaml, and add a code check that a snapshot is a pinned version, not an alias (rule is provider-specific, so write it against the provider's docs); (2) cap max_tokens in the client so the output-cost estimate is a true upper bound; (3) price cached/reasoning tokens that providers report separately; (4) ambiguous submit errors (timeout after the batch was created) are recorded as submit_failed and could be paid twice: tag batches with the job-set hash as metadata and reconcile against the provider's batch list before resubmitting; (5) confirm with user before the first paid call on this provider.

Amended 2026-10-03 per user: Anthropic client dropped (no Anthropic account); scope changed to Zen readiness. Items (2) max_tokens cap and the Cloudflare/User-Agent and usage-on-error fixes were done in TASK-27 and the smoketests; remaining carried-over items are now the acceptance criteria above.
<!-- SECTION:NOTES:END -->
