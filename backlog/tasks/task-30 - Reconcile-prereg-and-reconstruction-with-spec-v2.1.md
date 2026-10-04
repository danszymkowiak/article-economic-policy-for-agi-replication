---
id: TASK-30
title: Reconcile prereg and reconstruction with spec v2.1
status: Done
assignee:
  - '@claude'
created_date: '2026-10-04 07:12'
updated_date: '2026-10-04 07:16'
labels:
  - phase3
dependencies:
  - TASK-17
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The SSRN paper and the red-team pass changed the design (one call per persona x policy, named personas, Table 1 criteria, evidence from pinned Wikipedia, one-at-a-time design with a noise floor and primary metrics). prereg.md and reconstruction.md still describe the earlier design, and prereg/spec-v2-draft.md is only a proposal. The prereg must state the user-approved design before it can be frozen (TASK-23).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 prereg/prereg.md states the v2.1 design (questions, baseline, blocks, metrics, validity rules, budget order) and keeps DRAFT status with remaining TODOs listed
- [x] #2 prereg/reconstruction.md rows R1, R3, the criteria section and section 5a match the paper and spec; stand-ins versus paper-derived items stay marked
- [x] #3 Decisions made with the user (named personas, M = 5, aggregate-only reporting, Wikipedia evidence) are recorded with dates
- [x] #4 spec-v2-draft.md is marked as folded into prereg.md; no contradictions remain between the three files
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rewrite prereg/prereg.md from spec v2.1 keeping sections 6, 7, 9, 10 where still valid; status DRAFT, TODO list explicit. 2. Update reconstruction.md: R1, R3, criteria, 5a, section 6. 3. Mark spec-v2-draft.md as folded in. 4. Cross-check the three files for contradictions; run tests. Stop for review.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-04: prereg.md rewritten from spec v2.1 (questions, H1-H4, baseline, design blocks, metrics, validity rules, budget order, decisions log, 9 open TODOs); reconstruction.md rewritten (paper-first sources, criteria from Table 1, R1/R3/R4 and new R3b/R11/R12, section 5a resolved); spec-v2-draft.md marked FOLDED; README Approach updated to match. Not yet done: designs/inputs/criteria.yaml, prompts/, design expander, persona builder (listed as TODOs).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
prereg.md and reconstruction.md rewritten to the user-approved v2.1 design (Q1/Q2, one persona x policy calls, named personas, Wikipedia evidence, one-at-a-time blocks, primary and rank metrics, decisions log, 9 open TODOs); spec marked folded; README approach aligned. Verified by grep for stale terms (15 criteria, 765 calls, fractional factorial, balanced packet) and full test run (266 pass). Both prereg files remain DRAFT. Known remaining mismatch outside the three files: designs/inputs/criteria.yaml and prompts/ still reflect the earlier design (TASK-16).
<!-- SECTION:FINAL_SUMMARY:END -->
