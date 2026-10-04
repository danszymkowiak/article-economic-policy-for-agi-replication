---
id: TASK-33
title: Per-policy evidence and one-persona-per-policy calls in job building
status: To Do
assignee: []
created_date: '2026-10-04 07:16'
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
- [ ] #1 Job builder makes persona x policy jobs, selecting each policy's packet from evidence/packets, with a none level; job_id covers the evidence text
- [ ] #2 Response schema is one object per call with a score and rationale per criterion mirroring paper Appendix B, validated by the existing schema layer
- [ ] #3 A tested rule-based de-naming step replaces policy names in packet text with neutral codes for the description-only variant, with a test that no name remains
- [ ] #4 Cost estimate and plan output count calls correctly (561 per configuration-repeat at baseline) and the joint-scoring variant remains available
<!-- AC:END -->
