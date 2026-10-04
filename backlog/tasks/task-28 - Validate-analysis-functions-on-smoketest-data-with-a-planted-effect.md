---
id: TASK-28
title: Validate analysis functions on smoketest data with a planted effect
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 11:25'
updated_date: '2026-10-04 09:15'
labels:
  - phase3
dependencies:
  - TASK-26
  - TASK-20
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Split out of TASK-26 (user approved 2026-10-03). The smoketest pipeline is verified, but the rank-stability and variance-decomposition functions (TASK-19/20) did not exist yet, so we could not check that they recover a known effect. Once they exist, run them on controlled smoketest output so we know the analysis can detect a real effect and stays quiet on a null factor before it is applied to the study. Smoketest data stays separate from study data and never enters inference.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Rank-stability and variance-decomposition functions run on smoketest output (fake client with a planted ground truth, and optionally the stored live smoketest rows) without touching study data
- [x] #2 A planted factor effect (e.g. a known score shift for one factor level) is recovered with the right sign and approximate size, and a factor with no planted effect is reported as negligible
- [x] #3 Tests cover both the planted and the null case
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Grep: materiality-shift counts (prereg s6 item 2) not implemented anywhere; add pure domain/analysis_materiality.py (per policy x criterion |shift from B| > M, M=5 primary, 3 and 8 descriptive; repeat-noise multiple per unit; B split reference count) with planted-effect tests.
2. application/materiality.py (loaders reuse cell_observations/build_cell_array, Markdown + CSV) and CLI 'analyze materiality'.
3. FakeModelClient: optional job_scorer(job, label) so a test can plant a ground truth by cell/persona/policy/criterion.
4. tests/test_planted_effect_validation.py: tiny one_at_a_time design in a temp project, plan -> fake submit -> collect -> analyze (ranks, variance, recommendations smoke, materiality) with a planted +10 shift on one policy x criterion in Q1 and no effect elsewhere; assert sign/size recovered, null cells negligible (inside repeat-noise floor), rank metrics move as expected.
5. Test that study analysis reads only results/raw and ignores a populated results/smoketest store; non-study store labelled NON-INFERENCE.
6. Read-only smoke run on stored live smoketest rows (output to scratchpad, not committed).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Also verify here that main-study analysis reads only results/raw and ignores smoketest stores (the part of TASK-26 AC2 that could not be tested before analysis existed).

Implemented (b5230fc). Planted truth: score = truth[policy][criterion] + zero-mean persona effect + hash noise sd 3; Q1 shifts SAWF x ownership_of_gains by +12 (lifts it above UBC). tests/test_planted_effect_validation.py runs plan -> fake submit -> collect -> analyze on a tiny one_at_a_time design (6 personas, 3 policies, 2 criteria, k_R=4, k_Q=2, D2 8 repeats) in a temp non-inference store. Recovered: materiality 1 unit beyond M=5 (sawf x ownership, shift ~+12, >5 SE); variance Q1 level shift ~2, shift SD ~12/sqrt(6), ratio above B band; ranks tau 1/3 on ownership, SAWF 2->1; clause (b) flips in Q1 mean and both runs. 14 null cells: 0 units beyond M=5/8, |z|<4, |ratio|<3, tau 1, clause means hold. Noted: M=3 is ~3 SE at this scale and noise alone can cross it (D2); D2 single runs (one rating each) show single-run flips of (b) from noise. Study config (results/raw) ignores a populated results/smoketest store ('No cell B data', no NON-INFERENCE label). New: domain/analysis_materiality.py, application/materiality.py, 'llm-panel analyze materiality' (prereg s6 item 2, was missing). FakeModelClient gained job_scorer(job, label). Live smoketest rows: all four analyses ran read-only (outputs in scratchpad); the rows are fractional-design (no cell_id) so every report says 'No cell B data'; store hash unchanged. Suite 542 passed; ruff clean.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Validated the rank-stability, variance, recommendation and new materiality analyses end to end on fake-client output with a planted ground truth (+12 on one policy x criterion in Q1): all recover the effect with the right sign and size, and the 14 null cells are negligible. Added the missing prereg s6 primary metric 2 (materiality shifts, M=5; 3 and 8 descriptive) as 'llm-panel analyze materiality'. Verified that study analysis reads only results/raw. Evidence: tests/test_planted_effect_validation.py, tests/test_materiality.py, tests/domain/test_analysis_materiality.py; uv run pytest -q 542 passed.
<!-- SECTION:FINAL_SUMMARY:END -->
