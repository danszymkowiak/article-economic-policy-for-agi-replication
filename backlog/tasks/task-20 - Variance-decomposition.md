---
id: TASK-20
title: Variance decomposition
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
labels:
  - phase4
dependencies:
  - TASK-19
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Persona, prompt, model, evidence and repeat noise decomposed (mixed-effects or ANOVA)
- [ ] #2 Report states how much variance persona explains
- [ ] #3 Effective sample size of the persona panel estimated from the persona variance share
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: read only from results/raw; count only status ok rows as ratings; treat deferred rows as budget-censored (not run), failed as model failures, duplicate as ignored; report the counts of each.
<!-- SECTION:NOTES:END -->
