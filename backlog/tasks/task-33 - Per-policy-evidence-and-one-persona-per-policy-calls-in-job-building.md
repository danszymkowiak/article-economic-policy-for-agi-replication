---
id: TASK-33
title: Per-policy evidence and one-persona-per-policy calls in job building
status: Done
assignee:
  - '@claude'
created_date: '2026-10-04 07:16'
updated_date: '2026-10-04 08:04'
labels:
  - phase3
dependencies:
  - TASK-16
  - TASK-17
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The pipeline takes one evidence text per job set and builds persona x criterion calls with all policies in one prompt. The v2.1 baseline is one call per persona x policy, all criteria in one JSON, with that policy's evidence packet. The description-only variant must also remove policy names from the evidence packet.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Job builder makes persona x policy jobs, selecting each policy's packet from evidence/packets, with a none level; job_id covers the evidence text
- [x] #2 Response schema is one object per call with a score and rationale per criterion mirroring paper Appendix B, validated by the existing schema layer
- [x] #3 A tested rule-based de-naming step replaces policy names in packet text with neutral codes for the description-only variant, with a test that no name remains
- [x] #4 Cost estimate and plan output count calls correctly (561 per configuration-repeat at baseline) and the joint-scoring variant remains available
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Domain: RenderedJob gains criterion_ids (per-criterion reply), cell_id, n_ratings; temperature may be None (provider default; omitted in the Zen request).
2. Domain: CRITERION_RESPONSE_SCHEMA (criterion/score/rationale) and parse_ratings dispatch; old policy-keyed schema kept for joint and smoketests.
3. Domain: rule-based de-naming of packet text (policy names/acronyms and the packet's source-article titles in its metadata -> P1..P11).
4. Domain: study_jobs.py maps OAT cells to jobs (persona x policy with that policy's packet; joint = all 11 packets concatenated in Table 3 order; none level) and counts calls.
5. Bootstrap: load evidence packets per set from config paths.evidence_packets, templates from paths.prompts_dir, paraphrases; CLI plan/submit detect design: one_at_a_time and build jobs in run order with per-cell calls and cost.
6. Cost estimate/fake/Zen cap scale by ratings per call. End-to-end test with FakeModelClient; real-input counts 561/663/11.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Decisions: D1 evidence = all 11 packets concatenated in Table 3 order. Q1 de-naming rules in domain/denaming.py (header + source-article titles in packet metadata -> 'Pn source k'; policy names/acronyms/variants incl. EIC and SWF -> codes anywhere; real-world programme names kept). Output-token estimate and Zen max_tokens now scale with ratings per call (13 for persona x policy), so the full-plan estimate (26,112 calls) is an upper bound far above the ceiling until the pilot calibrates est_output_tokens_per_policy. Cells map straight to jobs (no RunSpec); jobs carry cell_id; provider-default temperature is None and omitted from the Zen request. Example design D2b now uses the 'reconstructed' panel (the synthetic panel file in designs/inputs). Prereg s10 entry and s12 item 9 updated (draft).

Validation: uv run pytest -q 427 passed; ruff check/format clean. Evidence: tests/test_study_pipeline.py (plan/fake submit/collect e2e on a one_at_a_time design; real inputs give 561/663/11 per repeat and 26,112 for the example plan; every real packet de-named with no name left), tests/domain/test_study_jobs.py, test_per_criterion.py, test_denaming.py. Real plan run (fake provider, read-only): 26,112 calls, 0 duplicates.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
plan/submit now read the one_at_a_time design: cells -> persona x policy jobs (each policy's packet from evidence/packets, 'none' level, de-named for Q1) or joint D1 jobs, built in the recorded run order with per-cell calls and cost. Added a per-criterion response schema through the existing validator, a rule-based packet de-namer, and ratings-per-call cost scaling. Verified with 427 passing tests incl. a FakeModelClient end-to-end run and real-input counts (561 per baseline repeat).
<!-- SECTION:FINAL_SUMMARY:END -->
