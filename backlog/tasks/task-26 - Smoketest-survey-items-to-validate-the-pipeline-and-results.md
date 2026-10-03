---
id: TASK-26
title: Smoketest survey items to validate the pipeline and results
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 08:10'
updated_date: '2026-10-03 11:26'
labels:
  - phase2
dependencies:
  - TASK-10
  - TASK-27
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Tasks 1-10 are tested only against fake policies and a fake model. We want a small set of survey items unrelated to the re-implemented AGI-policy survey, with known or checkable answer structure, so we can tell whether the pipeline (expand, build, submit, collect, validate, analysis) and the downstream metrics behave sensibly against a real API without contaminating or pre-judging the real study. Items must not overlap with the paper's 11 policies, criteria or personas, must be synthetic and non-sensitive, and smoketest data must never enter the inference set. The user has OpenCode Zen credits (key in OPENCODE_API_KEY) and no Anthropic account, so the real-API run goes through the Zen client (TASK-27) on big-pickle.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A smoketest inputs set (designs/smoketest/) defines a handful of non-AGI-policy items (policies, criteria, personas) with expected properties stated in advance, e.g. an obviously dominated option scored below an obviously better one, and a control pair that should score equal
- [x] #2 A scripted run with the fake client exercises plan, submit, collect and status end to end on the smoketest design and checks the stated expectations (ranking order, schema validity, idempotent rerun, spend accounting)
- [x] #3 A live smoketest ran on a paid OpenCode Zen model (glm-5.3-flash; big-pickle and deepseek-v4-flash were unavailable) via the TASK-27 client under a 0.25 USD ceiling, logged like every other run with the response-reported model id
- [x] #4 Smoketest data is clearly separated from study data: separate design file, config, store, ledger and Zen state, and a test proves a smoketest run writes only to its own store
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Smoketest inputs in designs/smoketest/inputs (household electricity-bill domain, unrelated to AGI policy): 6 options incl. a clearly good one, a dominated variant of it, a clearly bad one and a control pair of paraphrases; 2 criteria; 3 synthetic personas; design.yaml on opencode/big-pickle, 3 repeats.
2. designs/smoketest/expectations.yaml stating, before any run, what must hold on the savings criterion (good > dominated > bad by a margin; control pair within a tolerance). Pure checker domain/smoketest.py (tests first) over Ratings; 'llm-panel check' subcommand reading ok rows from a store (request + response text -> parse_ratings).
3. FakeModelClient gets an optional ground-truth score function so the fake run can actually satisfy (and, with a perverse scorer, violate) the expectations.
4. config.smoketest.yaml at repo root with its own store, ledger and zen dir under results/smoketest/, max_spend_usd 0 (any nonzero price is refused), gitignored outputs; tests prove a smoketest run writes only to its own store.
5. Scripted fake-client end-to-end test (plan, submit, collect, status, idempotent rerun, check). Then, on the user's go-ahead (given 2026-10-03), the live big-pickle run, logged like any other run.
6. AC4 (analysis on a planted effect) needs TASK-19/20 analysis functions that do not exist yet: report and ask rather than fake it.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Amended 2026-10-03 per user: smoketest runs against a real API (OpenCode Zen, big-pickle) instead of fake-only. The fake-client run stays as the first check. CLAUDE.md ground rule amended to allow labeled non-inference paid/real runs with explicit go-ahead; the user approved. Any switch to a priced Zen model needs fresh confirmation.

Progress 2026-10-03: built designs/smoketest (6 household-electricity options incl. dominated variant, bad option and a control pair; 2 criteria; 3 synthetic personas; 18 calls), expectations.yaml fixed before any run, pure checker domain/smoketest.py, 'llm-panel check' subcommand (exit 1 on failure), FakeModelClient scorer hook, config.smoketest.yaml (own store/ledger, ceiling 0), tests/test_smoketest_run.py (fake-client end to end with ground truth passes and is idempotent; perverse scorer fails; malformed jobs lower the ok rate). uv run pytest: 174 passed. Live probes (outside the store, 2 calls, both failed, no cost): HTTP 403 code 1010 (default urllib User-Agent, fixed), then HTTP 403 'free tier can only be used from within OpenCode' for big-pickle. The full live run has NOT been executed. AC5 (big-pickle) cannot be met; needs a paid Zen model and a nonzero smoketest budget, pending user decision. AC4 still depends on TASK-19/20 analysis functions that do not exist yet.

Live run 2026-10-03, config.smoketest.yaml, model glm-5.3-flash (reported model id matches), 18 jobs, 1 retry round: actual spend 0.0164 USD of 0.25 ceiling (plan estimated 0.0143 for the first round). Outcomes: 15 ok, 3 failed (finish_reason=length, hit the 1500-token cap, hidden reasoning/long rationales), plus 7 invalid first attempts (6 length, 1 schema violation 'additional property'). Pipeline mechanics verified live: submit, collect, retry-once, terminal failure, spend accounting, idempotent rerun. 'llm-panel check' FAILED two expectations, not changed after the fact: (1) ok rate 15/18 = 0.83 < 0.9, a real finding about the token cap; (2) sm_led_closet vs sm_lights_on gap 2.3 < 10: both scored at the floor (2.3 vs 0.0), so the margin was a badly calibrated expectation of mine, not a pipeline fault. The other three expectations passed (led_all beat led_closet by 63.7 and lights_on by 66.0; chargers a/b differ by 0.0). Bugs found by the live run and fixed with tests: Cloudflare 403/1010 on the default urllib User-Agent; error responses dropped provider-reported usage (so empty-text reasoning blowups were charged at estimate); check counted jobs awaiting retry as ok-rate-neutral. Caveats: job_id does not include max_tokens, so raising the cap does NOT rerun jobs that already finished as failed (use a new base_seed or store). Pre-fix, the 3 empty responses in the first round were charged at the 1500-token estimate rather than actual usage (conservative; store is append-only). AC4 still blocked on TASK-19/20.

Second live run 2026-10-03 on deepseek-v4.1-flash (user's preferred model; config.smoketest-deepseek.yaml, own store results/smoketest/deepseek/, reasoning cap 400 tokens/policy): 18 jobs + 1 retry round, actual spend 0.0676 USD of 0.25 (plan estimated 0.0534 for round one; retry round cost extra). 13 ok, 5 failed (finish_reason=length, empty text: hidden reasoning exhausts the 2400-token cap), 9 first attempts invalid (all length). Check: ok rate 13/18 = 0.72 FAIL; led_all beats led_closet by 73.8 and lights_on by 75.0 PASS; chargers a/b gap 0.0 PASS; closet vs lights_on gap 1.2 FAIL (same miscalibrated expectation as the glm run, unchanged). Mechanically the pipeline works with this model; reliability at this cap is worse than glm-5.3-flash (0.83). Next experiment if approved: raise the cap (e.g. 800/policy) on a new base_seed, or find a provider parameter that limits reasoning.

Third live run 2026-10-03: glm-5.3-flash with cap 600 tokens/policy (config.smoketest-glm-cap600.yaml, own store results/smoketest/glm-cap600/, same design and seeds as run 1). 18/18 jobs ok (one first attempt invalid: schema violation, additional property; fixed by the retry), actual spend 0.0130 USD of 0.10 (plan estimated 0.0332). Largest output seen 2322 tokens of the 3600 cap, so the cap has headroom. Check: ok rate 1.00 PASS; led_all beats led_closet by 69.8 and lights_on by 72.6 PASS; chargers a/b gap 0.0 PASS; closet vs lights_on gap 2.8 FAIL (same miscalibrated expectation, left unchanged: both options score at the floor). Total smoketest spend across the three runs about 0.097 USD. glm-5.3-flash is now the smoketest/pilot default; ceilings are per ledger, so cumulative smoketest spend must be tracked by hand.

AC4 (analysis functions on a planted effect) moved to a follow-up task (TASK-28, depends on TASK-20) with user approval 2026-10-03. Known-bad expectation left as is by user choice: sm_led_closet vs sm_lights_on (margin 10) fails because both options score at the floor.

Post-hoc amendment 2026-10-03 (user approved): expectation sm_led_closet vs sm_lights_on changed from margin 10 to margin 0 (closet >= always-on), because both score at the floor. Re-checking the stored rows of all three live runs (no new calls): the amended expectation passes in each (gaps 2.3, 1.2, 2.8); the other results are unchanged. The two runs that still fail overall do so on the ok-rate expectation only (glm 250-cap 0.83, deepseek 0.72).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built designs/smoketest (non-AGI household-electricity items, expectations fixed before any run), a pure expectations checker, 'llm-panel check', a FakeModelClient scorer hook and isolated smoketest configs. Verified with a fake-client end-to-end test (ground truth passes, perverse scorer fails, idempotent rerun) and three live runs on OpenCode Zen: the final glm-5.3-flash run at 600 tokens/policy had 18/18 valid jobs for 0.013 USD. One expectation (closet vs always-on) fails by design flaw and is left as is. uv run pytest: 176 passed. AC4 moved to TASK-28.
<!-- SECTION:FINAL_SUMMARY:END -->
