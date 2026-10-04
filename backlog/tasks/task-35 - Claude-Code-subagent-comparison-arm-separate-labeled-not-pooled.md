---
id: TASK-35
title: 'Claude Code subagent comparison arm (separate, labeled, not pooled)'
status: To Do
assignee: []
created_date: '2026-10-04 13:23'
updated_date: '2026-10-04 13:46'
labels:
  - phase3
dependencies:
  - TASK-34
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cross-model comparison arm (prereg s9a, user-directed 2026-10-04): repeat the baseline B on Claude Haiku 4.5 via Claude Code subagents (one fresh agent per persona x policy call, exact rendered B prompt, no tools), k_C = 3 repeats (1,683 agents), no variation battery. Compare with B on (1) stability and (2) distribution of responses, to see how a different model moves outputs next to run-to-run noise. Separate directory and store (subagent_arm/), labeled, never pooled with main inference. User-approved deviation from the 'single structured batch calls, not agentic subagents' rule. Caveats (prereg s9a): alias not necessarily a pinned snapshot, no temperature or seed control, runs not reproducible, cost is Claude Code usage not the ledger, differences mix model with harness. Tell the user the agent count and get approval before running.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Prereg s9a (draft) matches what is implemented
- [ ] #2 Runner/ingest builds the exact B prompts, rejects any run with tool use, validates against the schema, retries once, logs failures and discards in subagent_arm/ store
- [ ] #3 User approves the agent count before any run; k_C = 3 repeats of B collected
- [ ] #4 Stability comparison report (within-model repeat noise, rank stability, between-model shifts vs noise)
- [ ] #5 Distribution comparison report (rating distributions, persona spread, halo, failure rates, Table 4 agreement)
- [ ] #6 Report headed as a separate labeled arm, with the model-plus-harness caveat
<!-- AC:END -->
