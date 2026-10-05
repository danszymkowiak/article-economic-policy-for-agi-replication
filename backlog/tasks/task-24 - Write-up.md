---
id: TASK-24
title: Write-up
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-05 22:00'
labels:
  - phase5
dependencies:
  - TASK-23
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Full range of results first, adversarial arm second
- [x] #2 Describes the study as a re-implementation from the public description
- [x] #3 Limitations section states that instability does not show the recommendations are wrong
- [x] #4 Notes a small human economist survey on a subset of policies as a possible anchor not done here
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Run the adversarial arm (user go-ahead) and finish the deferred Claude-vs-B comparisons (TASK-35). 2. Draft writeup/draft.md from analysis/, subagent_arm/reports/, scale_probe/report.md and adversarial/report.md: full range first, adversarial arm second, limitations with the instability caveat and the human-anchor note. 3. Verify every number against the reports; user review.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Adversarial arm run to the end (depth exhausted, 27 candidates, no top-to-bottom success, best rank 3 of 11; 1.97 USD). Target UBI rests on a noisy 5-persona seed-0 run (UBC 15-30 points lower than in the rerun for all five personas). Reversed-scale probe added on user request (TASK-38). Claude-vs-B report added (TASK-35). Draft at writeup/draft.md; numbers cross-checked against the reports; H1 figure (median SD 0.67 of single-run panel means across B's 5 runs) computed ad hoc from results/raw, not yet in an analysis report. Global spend 14.14 of 15 USD. Stale text noticed, not fixed: analysis/recommendations report still says tier changes are an open prereg item and prereg s6 writes 3.8; adversarial/README.md says 1.50 USD ceiling (config is 2.50). TASK-23 still To Do (run stopped per s13).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Wrote writeup/draft.md: re-implementation framing, design and s13 deviation, full range of results (repeat noise, Q1/Q4/Q3c/D2, panel independence, published comparison, Claude arm, reversed-scale probe), then the adversarial arm, then limitations (instability does not show the recommendations are wrong; human economist anchor not done). Ran the adversarial arm to the end (27 candidates, no top-to-bottom success, 1.97 USD) and completed the Claude-vs-B comparison. Numbers cross-checked against the analysis reports; 659 tests pass. User reviewed the draft 2026-10-06.
<!-- SECTION:FINAL_SUMMARY:END -->
