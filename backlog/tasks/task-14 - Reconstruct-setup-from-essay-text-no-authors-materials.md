---
id: TASK-14
title: Reconstruct setup from essay text (no authors materials)
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:38'
labels:
  - phase3
dependencies:
  - TASK-13
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. The authors released no prompts, persona data or evidence packet. Reconstruct the setup from the essay text only. The study is a re-implementation from the public description, not a replication. The essay says personas were built with EDSL, which is public.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every reconstruction choice is documented in prereg/reconstruction.md
- [ ] #2 README and write-up describe the study as a re-implementation from the public description, not a replication
- [ ] #3 Checked whether EDSL persona and survey tooling can be reused, with the finding recorded
- [ ] #4 No stand-in material is presented as the authors original
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

User requirement 2026-10-03: the baseline must include repeats to measure answer stability with IDENTICAL prompts and different seeds. Existing expander gives seed = base_seed + repeat and job_id includes seed. Caveats to handle in prereg/design: (a) presentation_order=random is seeded by the same seed, so repeats would change the prompt; seed-stability cells must use fixed order or a separate order seed; (b) Zen may ignore the seed parameter, so at temperature>0 the variation is sampling noise and not reproducible by seed (record as limitation); at temperature 0 repeats may be identical; (c) fill the prereg 'Repeats: TODO' count and report repeat-only variance as its own component (TASK-20).
<!-- SECTION:NOTES:END -->
