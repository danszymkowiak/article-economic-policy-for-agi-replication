---
id: TASK-11
title: 'Study-model readiness on OpenCode Zen (prices, aliases, global spend)'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:42'
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
- [x] #1 Study model(s) on Zen are chosen with the user, and their list prices are recorded in config.yaml with the date and source
- [x] #2 The alias limitation is resolved with the user and written into the prereg limitations: the response-reported model id is stored per row, and a check flags rows whose reported id differs from the requested one or changes during the study
- [x] #3 Cached and reasoning tokens are verified against real Zen usage fields, and cost estimates and actuals cover them (tests added)
- [x] #4 A request that timed out (possibly billed, not retried) is charged at the estimate and counted toward the ceiling, covered by a test
- [x] #5 The 15 USD hard ceiling is enforced across all ledgers (study, smoketest, pilot), not per ledger, with tests
- [ ] #6 User confirms before the first paid study call
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md (tasks 1-10 close-out): (1) pin real snapshots and prices in config.yaml, and add a code check that a snapshot is a pinned version, not an alias (rule is provider-specific, so write it against the provider's docs); (2) cap max_tokens in the client so the output-cost estimate is a true upper bound; (3) price cached/reasoning tokens that providers report separately; (4) ambiguous submit errors (timeout after the batch was created) are recorded as submit_failed and could be paid twice: tag batches with the job-set hash as metadata and reconcile against the provider's batch list before resubmitting; (5) confirm with user before the first paid call on this provider.

Amended 2026-10-03 per user: Anthropic client dropped (no Anthropic account); scope changed to Zen readiness. Items (2) max_tokens cap and the Cloudflare/User-Agent and usage-on-error fixes were done in TASK-27 and the smoketests; remaining carried-over items are now the acceptance criteria above.

Done 2026-10-03 (free half, 3-5): (3) Real Zen usage shape verified from smoketest data: prompt_tokens includes prompt_tokens_details.cached_tokens, completion_tokens includes completion_tokens_details.reasoning_tokens (total = prompt + completion). Stored as cached_input_tokens / reasoning_tokens; usage_cost charges cached at optional Price.input_cached_per_mtok (config key input_cached), default = full input price (upper bound); reasoning is already in output tokens, not charged twice. Real Zen cached price still unknown, so none is set. (4) Timeout path already charged the estimate via collect._usage; added tests (Zen timeout returns empty usage, collect stores estimated usage that counts in spend). (5) New config key counts_spend_from (paths/globs of other configs): Spend.external counts their committed spend against the global 15 USD (HARD_CEILING_USD) in check_ceiling, additionally to each ledger's own max_spend_usd. Fails closed (unmatched pattern or unreadable config refuses), not recursive, own ledger skipped. All 4 configs wired with config*.yaml; status prints 'other ledgers'. Suite: 219 passed. Remaining: 1, 2, 6 need the user.

AC1: study model glm-5.3-flash chosen by user 2026-10-03; price 0.15 in / 0.50 out per 1M recorded in config.yaml (Zen docs, 2026-10-03); est_output_tokens_per_policy set to 600 (cap).

AC2 done 2026-10-03: domain/model_ids.check_model_ids compares each row's response-reported model with the requested id (provider prefix ignored) and flags mismatches or ids that change over time; status prints it, submit raises ModelIdDrift (REFUSED). Prereg limitations amended (draft). Real smoketest rows: 25/25 report glm-5.3-flash. Suite 227 passed. Only AC6 (user go-ahead before first paid study call) remains.
<!-- SECTION:NOTES:END -->
