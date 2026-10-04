---
id: TASK-35
title: 'Claude Code subagent comparison arm (separate, labeled, not pooled)'
status: To Do
assignee: []
created_date: '2026-10-04 13:23'
labels:
  - phase3
dependencies:
  - TASK-34
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Second baseline: one Claude Code subagent per named persona (51), each given only the exact rendered B prompt for that persona and the 11 policies with evidence packets, returning the standard JSON schema. Collected into its own store (subagent_arm/), analysed against B with the existing analyze commands. A deliberate, user-approved deviation from the 'single structured batch calls, not agentic subagents' ground rule: labeled, not pooled with the main analysis, never enters inference. Caveats to record in a prereg section: Claude alias not a pinned snapshot; no temperature/seed control so job_id semantics differ; cost bypasses the ledger and the 15 USD ceiling; the contrast mixes model, agentic wrapper and sampling; agents must be sandboxed (no file access) so they cannot read the published Table 4 scores. Requested by the user 2026-10-04; do after TASK-34, not before the freeze unless the user says so.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Prereg draft section documents the arm, its caveats and that it is not pooled
- [ ] #2 Subagents verified unable to read repo files (published scores) before any run
- [ ] #3 One B-equivalent repeat (51 agents, 561 policy x persona ratings) collected into subagent_arm/ store with schema validation and failures logged
- [ ] #4 Comparison report vs B via existing analyses, headed as a separate labeled arm
<!-- AC:END -->
