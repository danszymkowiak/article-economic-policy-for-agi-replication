---
id: TASK-32
title: 'One-at-a-time design expander (blocks R, Q, D)'
status: To Do
assignee: []
created_date: '2026-10-04 07:16'
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
- [ ] #1 Expander turns a design file into cells for blocks R (repeats, temperature levels, end-of-study drift repeat B'), Q (description-only, description paraphrases, instruction paraphrases, no evidence) and D (joint scoring, no persona, synthetic personas, second model)
- [ ] #2 Tests prove every Q and R-T cell differs from baseline in exactly one factor, and that all cells share the same 51 personas
- [ ] #3 Run order is randomised and interleaved across cells and repeats from a recorded seed, deterministically
- [ ] #4 The priority order and cost-based stopping rule from prereg section 8 are encoded; cells not run are reported as not run
<!-- AC:END -->
