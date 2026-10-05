---
id: TASK-37
title: >-
  Missing-data handling: D2 per-call rule, survivor-only and worst-case bounds,
  stale resample text
status: Done
assignee:
  - '@claude'
created_date: '2026-10-05 18:11'
updated_date: '2026-10-05 18:38'
labels: []
dependencies: []
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The first full analysis run (2026-10-05, after the s13 stopping-rule deviation) exposed three gaps. (1) D2 (no persona, 51 repeats x 11 one-policy calls) had 6 failed calls on ubi, sawf and ubc; the common-complete rule built for persona cells (a triplet must be present in every repeat) then dropped those three headline policies from D2 entirely, so clauses (a), (b), (d) were n/a and the clause (c) flip ranked only 8 policies. In D2 the repeat plays the persona role (561 calls = one B repeat), so the analogue of the persona x policy pair is the single call. (2) prereg s7 promises survivor-only means (secondary) and a worst-case bound with failures imputed at 0 and at 100; neither existed. (3) Rank report and CLI help still call the bootstrap resample count an open placeholder, but prereg s12 item 6 set it to 2,000. User asked on 2026-10-05 to fix all three and rerun. Post-freeze analysis change: record in prereg s13.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 In a no-persona cell a failed call drops only that repeat x policy; repeat means average the surviving repeats per policy; persona cells are unchanged
- [x] #2 Balanced analyses of a no-persona cell (variance components, repeat-noise SE, single runs) use the repeats with no failed call, and the reports say so
- [x] #3 A missing-data report gives, per cell, the failure rate (flag above 10%), and materiality counts and clause results under common-complete, survivor-only, failures imputed at 0 and failures imputed at 100
- [x] #4 Bootstrap default is 2,000 and no report or help text calls s12 item 6 open
- [x] #5 Tests written first cover each change; full suite passes
- [x] #6 All analyses rerun on results/raw; prereg s13 records the D2 rule and the new report as post-freeze analysis amendments
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Tests first (tests/domain/test_missing_data.py, tests/test_missing_data_report.py, updated rank wording test).
2. analysis_rank: no-persona cells skip the common-complete NaN spread; add complete_repeats() and repeat_mean(); common_complete flag for survivor-only arrays; DEFAULT_RESAMPLES 2000.
3. Consumers: rank/recommend/materiality take repeat means over surviving repeats; single runs, noise SE and variance components use complete repeats only (no-op for persona cells).
4. New domain module analysis_missing (Failure, variant observations, unit means, variant comparison) and application missing_data + CLI 'analyze missing'.
5. Rerun all analyses; diff against the previous reports (only D2 rows may change); prereg s13 amendment.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented. Full suite: 618 passed, 1 failed: tests/test_smoketest_run.py::test_end_to_end_with_ground_truth_scores_passes_and_is_idempotent, which asserts results/raw/rows.jsonl does not exist; it fails identically with these changes stashed (the study store now exists). Pre-existing, not touched. ruff check/format clean.
Reran baseline, ranks (2000, seed 0), variance, recommendations, materiality, missing on results/raw. Diff against the previous reports: every non-D2 CSV row identical; rank_stability.md changes only in the resample sentence.
D2 failures: repeats 3 (sawf), 32 (ubi), 36 (sawf), 38 (ubc), 41 (ubi), 45 (ubi): six distinct repeats, so 45 complete repeats.
D2 after the fix: 121 units, 12 beyond M=5 (was 88 units, 5); clauses (a) holds 6.0, (b) holds 3.3, (c) fails -11.9 (same as B), (d) holds 2.8; Kendall tau vs B 0.78-0.93 over prereg composites.
Missing-data report: failure rates 0-1.1%, nothing flagged. Q1 15 / 15 / 16 / 15 and Q4 19 / 19 / 18 / 18 (cc / survivor / impute 0 / impute 100); D2 12 / 12 / 8 / 15; clauses identical under every view in every cell.
prereg s13 entry added (2026-10-05 analysis amendments).

Follow-up within the task: the materiality, ranks, variance and recommendations reports now carry a shared D2 rule note (NO_PERSONA_NOTE), tested. Test of that found a real edge case: factor_shift crashed (reshape) when a no-persona cell has no complete repeat; fixed and tested (not estimable -> NaN). Final: 620 passed, 1 pre-existing failure (smoketest guard on results/raw existing), so AC5 left unchecked pending a decision on that test. Final rerun: only D2 rows changed versus the pre-fix reports.

Smoketest guard now compares the study store's size and mtime before and after instead of requiring it not to exist (user approved). Full suite: 621 passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
D2 failed calls now drop only their repeat x policy (all 11 policies kept); balanced analyses use D2's 45 complete repeats; new 'analyze missing' report gives survivor-only and 0/100-imputation views of the materiality count and clauses (prereg s7); bootstrap default 2000 and stale 'open' wording removed. Verified by new tests (15), full suite (one pre-existing unrelated smoketest failure), and a rerun diff showing only D2 rows changed. Recorded in prereg s13.
<!-- SECTION:FINAL_SUMMARY:END -->
