---
id: TASK-32
title: 'One-at-a-time design expander (blocks R, Q, D)'
status: Done
assignee:
  - '@claude'
created_date: '2026-10-04 07:16'
updated_date: '2026-10-04 07:28'
labels:
  - phase3
dependencies:
  - TASK-8
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The v2.1 design is a baseline plus one-at-a-time variations (noise-floor repeats R, small variations Q, design changes D) with interleaved randomised run order, not the fractional factorial the current expander builds. prereg.md section 5 defines the cells.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Expander turns a design file into cells for blocks R (repeats, temperature levels, end-of-study drift repeat B'), Q (description-only, description paraphrases, instruction paraphrases, no evidence) and D (joint scoring, no persona, synthetic personas, second model)
- [x] #2 Tests prove every Q and R-T cell differs from baseline in exactly one factor, and that all cells share the same 51 personas
- [x] #3 Run order is randomised and interleaved across cells and repeats from a recorded seed, deterministically
- [x] #4 The priority order and cost-based stopping rule from prereg section 8 are encoded; cells not run are reported as not run
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pure domain module domain/oat_design.py: Factors/Cell types, expand_cells for blocks R, Q, D, differing_factors, paired_persona_ids, run_order (seeded interleaved shuffle, B' last), plan_budget (prereg s8 drop-first + priority stop rule, not-run report).
2. bootstrap/design_loader.load_oat_design for a new 'design: one_at_a_time' file; example designs/one_at_a_time_fake.yaml.
3. Keep the fractional expander for smoketests; mapping cells to jobs is TASK-33.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Readings of ambiguous prereg points (also in code comments):
- D2b is missing from the s8 priority order; placed right after D2 pending user confirmation.
- 'Drop Q3, R-T and D3 first': when the whole plan exceeds the remaining budget, those units are dropped one at a time in listed order until the rest fits; then the priority pass stops at the first unit that does not fit (no skipping ahead to cheaper lower-priority units).
- R-T repeats are not fixed by the prereg; k_rt defaults to k_q (R-T is compared to B like a Q cell). Block D repeat counts are required per cell in the design file.
- B' uses seed base_seed + k_R so its job ids differ from every B repeat.
- Cells reference paraphrases only by level name para_1..para_3.
- AC2 '51 personas' applies to every cell except D2 (no persona) and D2b (synthetic panel), which change the persona factor by design.
Tests: uv run pytest -q -> 323 passed; ruff clean.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Pure one-at-a-time expander for blocks R/Q/D with seeded interleaved run order, B' last, priority order + cost stopping rule with not-run report; loader and fake design added. 323 tests pass. Open rulings (D2b priority, drop-first reading, R-T repeats) recorded in notes; need prereg edit.
<!-- SECTION:FINAL_SUMMARY:END -->
