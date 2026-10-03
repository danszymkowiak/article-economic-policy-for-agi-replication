---
id: TASK-28
title: Validate analysis functions on smoketest data with a planted effect
status: To Do
assignee: []
created_date: '2026-10-03 11:25'
updated_date: '2026-10-03 11:25'
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
- [ ] #1 Rank-stability and variance-decomposition functions run on smoketest output (fake client with a planted ground truth, and optionally the stored live smoketest rows) without touching study data
- [ ] #2 A planted factor effect (e.g. a known score shift for one factor level) is recovered with the right sign and approximate size, and a factor with no planted effect is reported as negligible
- [ ] #3 Tests cover both the planted and the null case
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Also verify here that main-study analysis reads only results/raw and ignores smoketest stores (the part of TASK-26 AC2 that could not be tested before analysis existed).
<!-- SECTION:NOTES:END -->
