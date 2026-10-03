---
id: TASK-15
title: Persona builders
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-03 11:51'
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
- [x] #1 Builders exist for: (a) paper-style survey-based personas as reconstructed, (b) IGM Clark Center US panel, (c) IGM Europe panel, (d) no persona
- [x] #2 Provenance is recorded for each persona source
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

Built domain/personas.py (pure): TRAIT_SPACE incl. country, balanced seeded synthetic panel, anonymous-record IGM builder (refuses identifying fields), provenance dict; bootstrap persona_files + 'llm-panel build-personas synthetic|igm' (refuses to overwrite); loader reads list or {provenance, personas} files, load_provenance. (d) no persona already existed in StudyInputs. Generated personas/reconstructed.yaml (seed 2026). IGM builders exist and are tested on fixtures; the IGM respondent data is NOT yet sourced (needs user decision on how to obtain it). Suite: 245 passed.

2026-10-04 user decision: drop the IGM US and Europe persona-source levels from this design (data not sourced). Updated prereg.md factor table, README and reconstruction.md; IGM builder kept, tested, for a possible later extension. Persona source factor is now reconstructed vs none.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Persona builders for reconstructed (synthetic, 51, seed 2026), IGM US/Europe (from anonymous records, data not yet sourced) and none; provenance stored with each source file; documented in prereg/reconstruction.md section 4a. Verified by 245 passing tests and generating the real baseline panel.
<!-- SECTION:FINAL_SUMMARY:END -->
