---
id: TASK-8
title: Design expander
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 06:17'
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
- [x] #1 Reads design.yaml with factors: model, persona source, paraphrase, policy blinding, evidence packet, repeats
- [x] #2 Produces RunSpecs for full factorial designs
- [x] #3 Supports fractional factorial designs
- [x] #4 Tests cover both modes
- [x] #5 Presentation order and score aggregation are design factors alongside the others
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. domain/design.py: pure Design + expand_full + expand_fractional (seeded, balanced greedy: exact main-effect balance where possible, near-balanced pairs) + to_run_specs
2. bootstrap/design_loader.py reads design.yaml (factors incl. presentation order and score aggregation)
3. Tests both modes, balance, determinism, loader
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fractional mode is a seeded balanced greedy subset (approximate orthogonal array), not a generator-based regular fraction. TODO before prereg freeze: decide fraction/n_runs and whether a regular-fraction generator is wanted. Model-factor levels carry pinned snapshot (+ optional per-model temperature); presentation_order and score_aggregation are factors.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
domain/design.py (full + fractional expansion, to_run_specs) and bootstrap/design_loader.py reading design.yaml; designs/example_fake.yaml. Verified: 66 tests pass covering both modes, main-effect balance, determinism, loader validation.
<!-- SECTION:FINAL_SUMMARY:END -->
