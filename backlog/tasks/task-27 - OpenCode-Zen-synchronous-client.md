---
id: TASK-27
title: OpenCode Zen synchronous client
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 08:21'
updated_date: '2026-10-03 09:22'
labels:
  - phase2
dependencies:
  - TASK-10
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user has credits at OpenCode Zen but no Anthropic account, and wants the smoketest (TASK-26) to run against a real API. Zen has no batch API and its model ids are aliases, so this adapter implements the existing ModelClient port with synchronous requests and records the model id each response reports. First target is big-pickle (https://opencode.ai/zen/v1/chat/completions), which Zen documents as free for a limited time with collected data possibly used to improve the model: use only synthetic non-sensitive items. Key comes from env var OPENCODE_API_KEY (in .env, never read by Claude); Zen auto-reload is off.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Adapter implements the ModelClient port with synchronous requests (bounded concurrency, retry with backoff on 429/5xx) and returns results through collect in the same shape as the fake client
- [x] #2 Reads OPENCODE_API_KEY from the environment, fails clearly if unset, and never logs or stores the key
- [x] #3 max_tokens is capped on every request, usage is recorded per job, and the response-reported model id is stored with each row
- [x] #4 Free models (price 0) work with spend accounting; paid models are charged at config.yaml prices with the existing ceiling, --confirm and exclusive-lock guards
- [x] #5 Unit tests run against mocked HTTP responses (success, malformed JSON retried once then failed, 429, timeout); no network in the test suite
- [x] #6 opencode is added to approved_providers only after the user confirms paid use of it
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pure protocol module domain/zen_protocol.py: build_request(job, max_tokens) for /zen/v1/chat/completions and parse_completion(job_id, status, payload) -> ModelResponse (usage mapped to input/output tokens, reported model id kept in raw). Tests first.
2. Adapter adapters/zen_client.py implementing ModelClient: injectable transport and sleep (no network in tests), key from OPENCODE_API_KEY (clear error if unset, never stored/logged), bounded-concurrency synchronous requests at submit_batch, retry with backoff on 429/5xx/connection errors, NO retry on read timeouts (possible double billing; reported as error so collect applies its normal retry-once rule), responses persisted per batch to a local JSONL so a later 'collect' process can fetch them.
3. max_tokens = est_output_tokens_per_policy x policies per job, wired from config so the cost estimate is an upper bound.
4. bootstrap/env.py: minimal .env loader (does not override existing env, never prints values); CLI factory gets provider 'opencode'; config.yaml gets a big-pickle price of 0 (not added to approved_providers: that waits for the explicit go-ahead at TASK-26 run time).
5. Test zero-price accounting through the existing spend ceiling; run full suite and ruff.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented via TDD (red then green per module): domain/zen_protocol.py (pure), adapters/zen_client.py, bootstrap/env.py, CLI wiring for provider 'opencode', big-pickle price 0 in config.yaml. Verification: uv run pytest = 160 passed (122 before, 38 new); ruff check and format clean. Decisions: read timeouts are NOT retried (possible billing), connection errors and 429/5xx are; missing provider usage leaves usage empty so collect charges the estimate; max_tokens = est_output_tokens_per_policy x policies (config-wired) so the estimate bounds cost; results persisted to results/zen/<batch>.jsonl so a separate collect process can read them; one loopback-only HTTP test exercises the real urllib transport (no external network). Malformed model text is handled by the existing collect retry-once path (covered by existing CLI tests with the fake client), not by the adapter. NOT verified: no live call to Zen has been made, so the assumed OpenAI chat-completions response shape, support for the 'seed' parameter, and big-pickle behaviour (e.g. reasoning tokens eating max_tokens) are unconfirmed until the first TASK-26 run. AC6 left unchecked: 'opencode' is not in approved_providers yet; it waits for the user's go-ahead.

User approved opencode in approved_providers on 2026-10-03 for the free big-pickle smoketest only (TASK-26).

Follow-up 2026-10-03 from the first live probe: Zen sits behind Cloudflare, which returned HTTP 403 'error code: 1010' for urllib's default User-Agent. Added an honest identifying User-Agent (llm-panel/0.1) with a regression test; 174 tests pass. After that, big-pickle answered HTTP 403 'OpenCode's free tier can only be used from within OpenCode'. We do not work around this (no imitating OpenCode's client). Free-tier models are therefore not usable from our client; paid Zen models are.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a synchronous OpenCode Zen ModelClient (pure protocol module, adapter with retry/concurrency/persistence, .env loader, CLI wiring, big-pickle price 0). Verified with uv run pytest: 160 passed, ruff clean. No live call yet; first live check is TASK-26.
<!-- SECTION:FINAL_SUMMARY:END -->
