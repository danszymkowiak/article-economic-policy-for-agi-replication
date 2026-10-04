---
id: TASK-36
title: Reconcile a crashed mid-submit intent against a partial Zen batch file
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-04 18:40'
updated_date: '2026-10-04 18:48'
labels: []
dependencies: []
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Zen has no server-side batch: submit_batch runs one HTTP call per job and appends to results/zen/<batch_id>.jsonl, recording the batch id in the ledger only at the end. An OOM kill left intent 1ac9b415 (1000 B jobs) with no batch id while 341 paid responses sat in zen-dc90acb1....jsonl. Add a 'reconcile' CLI command that resolves an open intent against a batch file: records 'submitted' for only the jobs with responses (so the rest stop counting as outstanding and are re-plannable), and closes the file with a _done marker so collect ingests it. No provider calls.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reconcile records a submitted entry listing only the jobs that have responses, with est_cost for those jobs only
- [ ] #2 Intent no longer open afterwards; unanswered jobs are no longer in flight
- [ ] #3 Batch file gets a _done marker so collect ingests it; re-running reconcile is refused
- [ ] #4 Refuses an intent that is already resolved, or a batch file with jobs outside the intent
- [ ] #5 Tests pass; real ledger reconciled for intent 1ac9b415 with batch zen-dc90acb1
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Tests first: application.reconcile (ledger-only), ZenClient.answered_job_ids/close_batch, CLI reconcile. 2. Implement. 3. Run full suite. 4. Apply to real ledger (intent 1ac9b415, batch zen-dc90acb1); do NOT run collect (it would retry 2 errored jobs = paid calls) until user says go.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented reconcile (application/reconcile.py, ZenClient.answered_job_ids/close_batch, CLI 'reconcile'); tests in tests/test_reconcile.py and test_cli.py. Applied to real ledger 2026-10-04: intent 1ac9b415 -> batch zen-dc90acb1, 341 of 1000 jobs salvaged (339 ok, 2 errored), other 659 not run. collect NOT yet run: it would retry the 2 errored jobs (paid). Pre-existing unrelated failure: tests/test_smoketest_run.py end_to_end asserts real results/raw/rows.jsonl does not exist (it now does).
<!-- SECTION:NOTES:END -->
