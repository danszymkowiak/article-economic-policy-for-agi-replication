---
id: TASK-12
title: 'Pilot: 20 jobs end to end'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:24'
labels:
  - phase2
dependencies:
  - TASK-11
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Validates the full pipeline cheaply before scaling; must stay well inside the 15 USD ceiling.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 20 jobs run through plan -> submit -> collect
- [ ] #2 Raw rows and the failure rate are shown to the user
- [ ] #3 Actual pilot spend is reported against max_spend_usd
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: revisit cost-estimate assumptions with real usage (no batch discount assumed, 100 output tokens per policy, chars/4 input tokens); decide whether a 0.9x safety margin on the ceiling is needed; a torn final line in results/raw still makes reads raise until removed by hand: consider a repair command that quarantines the tail (modifies the store, needs user approval); JSONL only for now, add Parquet only if analysis needs it; store exists() assumes one writer (submit/collect take a file lock).

From the TASK-26 live smoketest (glm-5.3-flash via Zen): a reasoning-capable model can exhaust max_tokens on hidden reasoning and return empty text; 100 tokens/policy truncated JSON, 250/policy still failed 3 of 18 jobs. Calibrate est_output_tokens_per_policy (which is also the max_tokens cap) from real usage, and decide how to handle reasoning models (cap vs reasoning effort). job_id excludes max_tokens, so changing the cap will not rerun jobs that finished as failed: decide whether the cap belongs in the job hash.

Calibration data point from TASK-26 (glm-5.3-flash, 6 policies per call): a cap of 600 tokens/policy gave 18/18 valid jobs with max observed output 2322 tokens per job (about 390 per policy); 250/policy lost 3 of 18, 100/policy truncated everything. Use roughly 600/policy as the starting cap for glm-class models, then recalibrate on the real prompts.
<!-- SECTION:NOTES:END -->
