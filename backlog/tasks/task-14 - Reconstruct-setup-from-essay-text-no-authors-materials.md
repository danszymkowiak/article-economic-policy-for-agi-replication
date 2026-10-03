---
id: TASK-14
title: Reconstruct setup from essay text (no authors materials)
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
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
