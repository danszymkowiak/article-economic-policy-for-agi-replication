---
id: TASK-2
title: Draft prereg/prereg.md
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:07'
labels:
  - phase0
dependencies:
  - TASK-1
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. The study design must be written down before any paid calls are made.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 prereg/prereg.md covers hypotheses, factors, metrics and stopping rules
- [ ] #2 Factor levels are left as TODO markers
- [ ] #3 File is marked draft; no paid API calls are made until the user tags it as frozen
- [ ] #4 Prereg states the aim is a sensitivity analysis that reports the whole range (not maximum variation), with the adversarial arm kept separate and labeled
- [ ] #5 Prereg lists the metrics up front: Kendall tau between setups, variance share (persona vs prompt vs model), and survival of the three-stage recommendation
- [ ] #6 Prereg commits to logging every run, including failures, with seed and temperature
<!-- AC:END -->
