---
id: TASK-2
title: Draft prereg/prereg.md
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:13'
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
- [x] #1 prereg/prereg.md covers hypotheses, factors, metrics and stopping rules
- [x] #2 Factor levels are left as TODO markers
- [x] #3 File is marked draft; no paid API calls are made until the user tags it as frozen
- [x] #4 Prereg states the aim is a sensitivity analysis that reports the whole range (not maximum variation), with the adversarial arm kept separate and labeled
- [x] #5 Prereg lists the metrics up front: Kendall tau between setups, variance share (persona vs prompt vs model), and survival of the three-stage recommendation
- [x] #6 Prereg commits to logging every run, including failures, with seed and temperature
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Write prereg/prereg.md as DRAFT: aim, hypotheses, factors (levels TODO), metrics, stopping rules, logging, adversarial arm separation, spend ceiling, limits. No paid calls.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Wrote prereg/prereg.md as DRAFT (hypotheses, factors with TODO levels, metrics, logging, stopping rules, separate adversarial arm). Verified by reading the sections against each AC; no paid calls.
<!-- SECTION:FINAL_SUMMARY:END -->
