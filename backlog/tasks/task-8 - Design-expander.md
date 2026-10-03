---
id: TASK-8
title: Design expander
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:07'
labels:
  - phase1
dependencies:
  - TASK-7
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reads design.yaml with factors: model, persona source, paraphrase, policy blinding, evidence packet, repeats
- [ ] #2 Produces RunSpecs for full factorial designs
- [ ] #3 Supports fractional factorial designs
- [ ] #4 Tests cover both modes
- [ ] #5 Presentation order and score aggregation are design factors alongside the others
<!-- AC:END -->
