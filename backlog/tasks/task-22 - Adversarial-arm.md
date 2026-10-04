---
id: TASK-22
title: Adversarial arm
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 09:32'
labels:
  - phase4
dependencies:
  - TASK-21
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Kept separate from the main results so it is not confused with them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Lives in its own directory and is clearly labeled adversarial
- [x] #2 Searches for the smallest plausible change that moves a policy from top to bottom
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. adversarial/ package at repo root, labeled ADVERSARIAL: catalogue.py (pure, versioned catalogue adv-catalogue-v1: 5 wording edits, 4 target-packet edits, 1 persona-subset drop, 2 temperatures, 2 criterion orders; slots forbid conflicting combos), search.py (pure: edit size, changed-span chars, packet edits, outcome evaluation, greedy depth<=2 search with candidate cap), arm.py (application: render candidate jobs via study_jobs on a seeded small search panel, plan/submit through existing plan_from_build/submit guards, collect, search status incl. budget exhaustion), report.py (adversarial/report.md + candidates.csv), cli.py/__main__.py (python -m adversarial plan|submit --confirm|collect|report).
2. adversarial/config.adversarial.yaml: own store/ledger under adversarial/results, max_spend_usd 1.50, counts_spend_from ../config*.yaml; root configs count adversarial/config*.yaml.
3. Tests first (fake client only): planted vulnerability found at depth 2 with smallest edit chosen, budget and depth/candidate caps, every candidate logged, never writes results/raw, submit needs --confirm.
4. prereg s9 DRAFT procedure + budget text; s12 item 7 marked drafted.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented adversarial/ package (catalogue.py, search.py pure; arm.py application; report.py; cli.py via python -m adversarial) with config.adversarial.yaml (1.50 USD, own store/ledger in adversarial/results, counts ../config*.yaml; root configs now also count adversarial/config*.yaml). Edit size = (perturbations, max per-prompt chars summed over each perturbation's own changed span, prompts changed). Search panel 5 named personas (seed 20261004), one run per candidate, baseline rerun at seed 1 as noise reference; primary composite full_transformation; depth<=2, <=30 candidates. approved_providers is [fake] until the user approves paid adversarial runs. prereg s9 drafted, s12 item 7 marked drafted. pytest pythonpath and ruff src include the repo root for the adversarial package. Budget note: at pilot cost (~0.0015 USD/call, 55 calls/candidate) 1.50 USD covers depth 1 but probably not all of depth 2. Tests: uv run pytest -q -> 573 passed (31 new in tests/adversarial).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the ADVERSARIAL ARM under adversarial/: a fixed, versioned catalogue (adv-catalogue-v1, 14 perturbations: wording, target-packet edits, persona drop, temperature, criterion order) and a pre-specified greedy search (depth <= 2, <= 30 candidates, own 1.50 USD ceiling inside the global 15 USD cap) for the smallest change that moves the top policy on Full Transformation to last place; every candidate is logged in adversarial/report.md (headed 'ADVERSARIAL ARM — not pooled with the main analysis') and candidates.csv. Submission reuses the study's plan/submit/collect guards. Verified with fake-client tests: planted vulnerability found at depth 2 with the smallest edit chosen, depth/candidate/budget caps respected, all candidates logged, nothing written to results/raw, submit refuses without --confirm, committed config plans offline. prereg s9 procedure and budget drafted (still DRAFT).
<!-- SECTION:FINAL_SUMMARY:END -->
