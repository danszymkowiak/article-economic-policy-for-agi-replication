---
id: TASK-9
title: Job builder
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
labels:
  - phase1
dependencies:
  - TASK-8
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 RunSpec x persona x policy x criterion x repeat yields RenderedJobs
- [x] #2 Jobs whose job_id already exists in the store are skipped
- [x] #3 Tests cover skipping and resumption
- [x] #4 Supports the paper format (all 11 policies in one prompt) as the default, and a one-policy-per-call mode as a later variant
- [x] #5 Job count per configuration is reported for both formats (baseline 15 criteria x 11 policies x 51 personas: 765 calls / 8,415 ratings in paper format; 8,415 calls in one-policy mode)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. domain/rendering.py: placeholder baseline template (real templates = task 16), ordering, blinding labels
2. domain/jobs.py: jobs_for_spec (all_policies default, one_policy variant), count_jobs (calls and ratings)
3. application/build_jobs.py: expand specs x personas x criteria x repeats, dedupe by job_id, skip terminal ids in store, report counts
4. Tests for skipping/resumption, modes, blinding, counts
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Prompt template is a PLACEHOLDER baseline (real templates/paraphrases = TASK-16). Note: AC5's '~8,400 calls' only holds for one-policy-per-call mode (15x11x51=8,415). In the paper format (11 policies per prompt) the baseline is 765 calls yielding 8,415 ratings; count_jobs reports both. Specs differing only in score_aggregation (analysis-level) render identical jobs and are deduplicated by job_id; reported as 'duplicates'.

AC5 reworded 2026-10-03 per user: paper format is the baseline (765 calls, 8,415 ratings). Verified by test_count_jobs_baseline_numbers (uv run pytest: 122 passed).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
domain/rendering.py, domain/jobs.py, application/build_jobs.py: RunSpec x persona x criterion x repeat (x policy in one_policy mode) -> RenderedJobs; store-skipping, dedupe, per-spec call/rating counts. Verified: 83 tests pass incl. skip/resume, both formats, blinding, ordering, baseline counts 765 calls/8415 ratings.
<!-- SECTION:FINAL_SUMMARY:END -->
