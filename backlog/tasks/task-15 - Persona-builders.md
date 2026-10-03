---
id: TASK-15
title: Persona builders
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
labels:
  - phase3
dependencies:
  - TASK-14
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Builders exist for: (a) paper-style survey-based personas as reconstructed, (b) IGM Clark Center US panel, (c) IGM Europe panel, (d) no persona
- [ ] #2 Provenance is recorded for each persona source
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.
<!-- SECTION:NOTES:END -->
