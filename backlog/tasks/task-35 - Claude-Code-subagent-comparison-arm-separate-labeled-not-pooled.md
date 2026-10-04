---
id: TASK-35
title: 'Claude Code subagent comparison arm (separate, labeled, not pooled)'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-04 13:23'
updated_date: '2026-10-04 16:41'
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
- [x] #4 Stability comparison report (within-model repeat noise, rank stability, between-model shifts vs noise)
- [x] #5 Distribution comparison report (rating distributions, persona spread, halo, failure rates, Table 4 agreement)
- [x] #6 Report headed as a separate labeled arm, with the model-plus-harness caveat
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Runner built and tested (subagent_arm/, 11 tests): task files, next prompts, discard, ingest with one retry, own store (gitignored), config with k_c 3 from the study design baseline. Design: agent reads one task file and writes one answer file (expected tool uses 2) so answers do not pass through the session context. Not run: needs the frozen prereg and the user's go-ahead on 1,683 agents. Comparison reports still to write.

Pilot 2026-10-04 (non-inference, subagent_arm/pilot/, 63 agent runs): flow works, 3 tool uses per valid run (Read, Write, hand-back). Hand-written JSON failed 11/36 first attempts (stray brace); switched to criterion | score | rationale lines converted on ingest: 20/20 ok. Cost: first 44 runs added $1.77 Haiku (~$0.04/agent, mostly ~13.6k cached tokens of generic subagent overhead) plus launching overhead; weekly +2pp. Restricted rater agent (.claude/agents/rater.md) needs a session restart to be recognised; not yet measured. Prereg s9a updated.

Usage after 63 runs: Haiku $2.87 (last 20 line-format agents +$1.10 = ~$0.055/agent, cache writes ~30k/agent, higher than the earlier ~$0.04 average); Sonnet orchestration $9.76 total; session limit 44%, week 15% (from 11% at start, ~+4pp for ~$7.5 incl. building). Rough extrapolation: k_C=3 (1,683 agents) well over a week's allowance in this long-context session; k_C=1 (561) roughly half. Next: restart session (loads .claude/agents/rater.md, shrinks main-thread context), run 20 rater agents with the pilot config to measure, then decide k_C. Prereg s9a k_C=3 is a draft and may be reduced.

Rater-agent measurement 2026-10-04 (non-inference, pilot store, 20 agents, subagent_type rater, all first attempts valid, all 3 tool uses, no discards). /usage before/after: Haiku $0.0016 -> $0.58 (~$0.029/agent; cache writes ~10k/agent vs ~30k for the generic agent); Sonnet orchestration $0.110 -> $0.63 (~$0.026/agent, launch prompts echoed plus hand-back and notification turns re-reading context); total ~$0.055/agent, unchanged from the generic agent (the Haiku saving moved into orchestration). Limits: session 45% -> 50%, week 15% -> 16% (rounded). Full k_C=3 (1,683 agents) judged unaffordable. User decision 2026-10-04: one full pass (561) plus two more passes over UBC only with all 51 personas (+102) = 663 agents; implemented as repeat_policies in config.subagent.yaml and build_jobs(repeat_policy_ids); prereg s9a updated (draft, user reviewed). User then upgraded to the Max plan (more headroom), not yet re-measured. Real arm not started: waits for the frozen prereg and the user's go-ahead.

2026-10-04: real run complete (663 agents, 663 ok, 5 invalid first attempts all retried). Descriptive Claude-only report: subagent_arm/report.py -> subagent_arm/reports/claude_arm_report.md (UBC repeat stability, response distributions, halo, failure rates, Table 4 agreement). Criteria 4-5 ticked by user decision with the B-dependent parts DEFERRED until the main run exists (results/raw is empty): cells shifted from B by more than M=5, B repeat noise beside Claude's, clause/rank comparison against B. Report script has no tests.
<!-- SECTION:NOTES:END -->
