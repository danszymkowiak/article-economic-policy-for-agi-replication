---
id: TASK-34
title: Pre-freeze status and open decisions (2026-10-04 build session)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-04 12:59'
updated_date: '2026-10-04 13:43'
labels:
  - phase3
dependencies:
  - TASK-22
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Write-up of the 2026-10-04 build session, paused by the user before freezing the prereg. Branch study-build (not merged to main). Done in this session, one commit each, 573 tests passing: TASK-31 (51 named personas from Table 7, roster verified against paper text, Cochrane excluded), TASK-32 (one-at-a-time expander, blocks R/Q/D, seeded interleaved order, priority + stopping rule), TASK-16 (13 criteria, templates, paraphrases reviewed by user, wired; prereg numbers fixed: B 561 calls, D1 51x13=663, D2 51 repeats x 11 = 561, full plan 561(k_R+2)+7,395 k_Q = 26,112 at k_R=5,k_Q=3), TASK-33 (per-policy evidence, per-criterion schema, Q1 de-naming, --plan counts; user accepted D1 all-11-packets rule and leftover programme names), TASK-12 (pilot: user go-ahead for 20 baseline jobs on glm-5.3-flash via Zen, 20/20 ok, actual $0.0298 of $0.25, output tokens/call min 1614 median ~2626 max 3471, ~$0.0015/call, so full example plan ~$39 > $15 ceiling: run in stages; --max-jobs added), TASK-18 (baseline vs published Table 4), TASK-19 (rank stability, numpy added), TASK-20 (variance decomposition), TASK-21 (recommendation robustness), TASK-28 (planted-effect validation; materiality metric added), TASK-22 (adversarial arm under adversarial/, own store/ledger, $1.50 budget, approved_providers fake only). Not done / user's steps: TASK-23 freeze and tag (user's act); merge study-build to main; TASK-11 AC6 (go-ahead before first paid STUDY call; pilot approval does not cover it). After freezing: dispatch a red-team subagent on the locked design files only (prereg/prereg.md, spec-v2-draft.md, reconstruction.md, designs, prompts/manifest.yaml), consider feedback, log follow-up tasks.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tiers: define tiers for prereg s6 item 1b (paper defines none) or drop the item
- [x] #2 Fix prereg s6 clause (c) margin typo (3.8 vs 3.9, NIT gap to UI at rank 4); code uses 3.9
- [x] #3 Choose the primary ICC for persona effective sample size (per policy x criterion cell vs per-criterion agreement across policies)
- [x] #4 Decide whether materiality counts all 13 criteria or only the 11 in Table 4
- [x] #5 Review adversarial arm choices (14-entry catalogue, 5-persona search panel, Full Transformation composite, target rule, edit-size definition) and budget: raise to ~2.50 USD or cut panel to 3 (1.50 covers depth 1 only at pilot prices)
- [x] #6 Set k_R, k_Q, R-T temperature levels, max_tokens cap and bootstrap resample count from the pilot; generate the study design file; run the second-model paraphrase equivalence check; copy paraphrase hashes into prereg at freezing
- [x] #7 Add essay composite-table comparison (reconstruction R8) and split deferred/failed/duplicate row counts in analysis reports (small gaps left by TASK-18..21)
- [ ] #8 Stage plan agreed (full plan exceeds 15 USD ceiling): choose stages and when the user raises the account budget and config ceiling
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-04: decided AC1 (drop tier item 1b), AC2 (3.9 fixed in prereg s6 and spec-v2-draft), AC3 (per policy x criterion ICC primary), AC4 (primary count over the 11 Table 4 criteria, extras descriptive), AC5 (adversarial arm accepted, budget 2.50 USD in prereg + config). Prereg text and decisions log updated. Code NOT yet changed for AC4 (materiality currently counts all rated criteria) or AC3 (variance report primary labelling). AC6-8 open.

AC4 code done (materiality primary = Table 4 criteria, added criteria in separate section/CSV column criteria_set; ICC labels primary/secondary in variance report). AC6 set: designs/study.yaml (k_R 5, k_Q 3, R-T 0.0/1.0, D3 omitted), config est_output_tokens_per_policy 400 (cap 5200), bootstrap 2000 in prereg. Not done: second-model paraphrase equivalence check (needs paid call + go-ahead), paraphrase hashes copy at freeze, AC7, AC8. Created TASK-35 (subagent arm).

AC7 done: essay composite comparison (analysis/published/essay_composites.csv, R8 check + B vs essay for welfare/agency/durability; feasibility not comparable, six-column composite) in baseline report with --essay option; CellCounts split into failed/deferred/duplicate in all 5 reports. Paraphrase equivalence check done by a blind fresh Claude instance (6/6 PASS, notes in prereg s10). Stage plan decision: keep guard, raise ceiling in stages.

AC6 closed: user confirmed paraphrase wording (SAWF 'publicly owned' kept); hashes copied into prereg s7. Manifest status flip to frozen happens at the user's tag (TASK-23).
<!-- SECTION:NOTES:END -->
