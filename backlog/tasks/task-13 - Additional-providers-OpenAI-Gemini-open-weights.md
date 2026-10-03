---
id: TASK-13
title: 'Additional providers: OpenAI, Gemini, open-weights'
status: To Do
assignee: []
created_date: '2026-10-03 06:03'
labels:
  - phase2
dependencies:
  - TASK-12
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Given the 15 USD ceiling, the user may choose to defer or cheapen this; confirm with the user before running any paid calls on these providers.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 OpenAI, Gemini and one open-weights adapter implement ModelClient
- [ ] #2 Each adapter pins model snapshots and reports usage for spend tracking
- [ ] #3 Tests run against fakes or recorded responses, with no paid calls
<!-- AC:END -->
