---
id: TASK-14
title: Reconstruct setup from essay text (no authors materials)
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:46'
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
- [x] #1 Every reconstruction choice is documented in prereg/reconstruction.md
- [x] #2 README and write-up describe the study as a re-implementation from the public description, not a replication
- [x] #3 Checked whether EDSL persona and survey tooling can be reused, with the finding recorded
- [x] #4 No stand-in material is presented as the authors original
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

User requirement 2026-10-03: the baseline must include repeats to measure answer stability with IDENTICAL prompts and different seeds. Existing expander gives seed = base_seed + repeat and job_id includes seed. Caveats to handle in prereg/design: (a) presentation_order=random is seeded by the same seed, so repeats would change the prompt; seed-stability cells must use fixed order or a separate order seed; (b) Zen may ignore the seed parameter, so at temperature>0 the variation is sampling noise and not reproducible by seed (record as limitation); at temperature 0 repeats may be identical; (c) fill the prereg 'Repeats: TODO' count and report repeat-only variance as its own component (TASK-20).

2026-10-03: drafted prereg/reconstruction.md (essay facts, 15 criteria, 11 policies, choices R1-R10, EDSL finding, unknowables). EDSL 1.0.8 checked offline in a scratch venv: persona = traits dict rendered as 'Your traits: {...}'; decision = reuse persona format/wording, not runtime (would bypass spend ceiling, ledger, hashing, logging). README reworded to re-implementation. AC1 waits on user decisions R3 (51 baseline personas) and R4 (evidence packet); AC4 checked when stand-in inputs exist.

R3 and R4 decided by user 2026-10-03 (synthetic personas; neutral literature evidence summary) and recorded in prereg/reconstruction.md. AC4: the document labels every stand-in as ours and states no stand-in is the authors' original; the existing designs/fake_inputs are labelled fake. Remaining placeholders (prompt template, fake inputs) are replaced in tasks 15-17.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documented the reconstruction in prereg/reconstruction.md: essay facts (11 policies, 15 criteria, 51 EDSL personas, 0-100 scale), our stand-in choices R1-R10 with status, what stays unknowable. EDSL 1.0.8 checked offline in a scratch venv: reuse persona format/wording ('Your traits: {...}'), not its runtime, because it would bypass spend ceiling, ledger, hashing and logging. User decided R3 (51 synthetic personas) and R4 (neutral literature evidence summary). README reworded to re-implementation. Docs-only task, no code changes; suite unchanged. Note: AC2 mentions the write-up, which does not exist yet; TASK-24 must carry the same wording.
<!-- SECTION:FINAL_SUMMARY:END -->
