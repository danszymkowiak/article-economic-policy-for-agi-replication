---
id: TASK-16
title: Prompt templates
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 06:26'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Draft real inputs (11 policies named+blinded, 15 criteria) from essay snapshot; user reviews text
2. Draft baseline + 4 paraphrase templates (all-policies) and one-policy variants as prompts/*.txt; user reviews EVERY prompt before wiring
3. Tests first: render all templates, same placeholders/contract, blinded has no names, order variants, unknown template fails
4. Load templates from files, render_prompt takes template text; one_policy format
5. Point config.yaml inputs_dir at real inputs; update prereg (wording/order rows) and reconstruction R5
6. Run tests, stop for review
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

2026-10-04 drafted for review (no code/tests yet): designs/inputs/{policies,criteria}.yaml (11 policies named+blinded; 15 criteria quoting essay footnotes, user agreed terse wording) and prompts/{all_policies,one_policy}/{baseline,para_1..4}.txt. User will review every prompt and blinded description before wiring. Full paper (SSRN 7470000) returned 403; user supplied a PDF at docs/economic-policy-for-agi-ssrn.pdf (untracked, not committed: redistribution undecided). Paper abstract says 24 interventions vs essay's 11; recorded in reconstruction.md 5a. Next: review feedback, tests first, loader + render_prompt, point config inputs_dir, prereg rows.
<!-- SECTION:NOTES:END -->
