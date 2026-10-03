---
id: TASK-16
title: Prompt templates
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 08:08'
labels:
  - phase3
dependencies:
  - TASK-15
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Paper-faithful template (as reconstructed from the essay)
- [ ] #2 3-5 neutral paraphrases
- [ ] #3 Blinded variant describing policy mechanics without names
- [ ] #4 Policy presentation-order variants (e.g. shuffled or reversed) for the order factor
- [ ] #5 Paper format (all 11 policies in one prompt) built first; one-policy-per-call variant second
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.
<!-- SECTION:NOTES:END -->
