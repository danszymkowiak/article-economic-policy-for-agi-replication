---
id: TASK-16
title: Prompt templates
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 07:52'
labels:
  - phase3
dependencies:
  - TASK-15
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 designs/inputs/criteria.yaml holds the paper's criteria (13 panel criteria of Table 4 and Appendix B, plus Political Support and Administrative Capacity and Speed for the essay comparison), with wording from paper Table 1 and Figure 1; the loader reads them and a test checks the count and ids
- [x] #2 Baseline template: one persona x one policy, all criteria returned in one JSON object, policy shown by Table 3 name and definition; wording drafted and reviewed by the user before wiring
- [x] #3 Description-only variant (Q1): policy name replaced by its definition and neutral codes P1..P11; a test shows no policy name appears in the rendered prompt
- [x] #4 Frozen paraphrase sets: three meaning-preserving paraphrases of the policy definitions (Q2) and three of the instruction text (Q3), each hashed, with an equivalence check recorded; user reviews every one
- [x] #5 Joint-scoring template (design change D1): all 11 policies in one prompt per persona x criterion, kept as a variant
- [x] #6 config.yaml inputs_dir points at the real inputs; prereg R5 and the prompt-wording row are updated; tests first, run, then stop for user review
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rewrite criteria.yaml to the paper's wording (user reviews). 2. Draft baseline and variant templates under prompts/ for user review of EVERY prompt before wiring. 3. Tests first: render all templates, same placeholder contract, description-only has no names, unknown template fails. 4. Loader and render_prompt for the one-persona-per-policy format; joint-scoring kept as variant. 5. Freeze paraphrases by hash with equivalence check. 6. Point config inputs_dir at real inputs, update prereg R5; run tests; stop for review. Per-policy evidence wiring, named personas and the design expander are TASK-31, 32, 33.

7. (16b, user approved drafts 2026-10-04) Move personas/ under designs/inputs/personas, point config inputs_dir at designs/inputs; R5 and Q2/Q3 rows reference reviewed templates and manifest (status reviewed-by-user); prereg 13 criteria and call-count arithmetic; s8 priority/stopping and k_Q for R-T and D; decisions log; s12 TODOs; expander repeats follow s8.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

2026-10-04 drafted for review (no code/tests yet): designs/inputs/{policies,criteria}.yaml (11 policies named+blinded; 15 criteria quoting essay footnotes, user agreed terse wording) and prompts/{all_policies,one_policy}/{baseline,para_1..4}.txt. User will review every prompt and blinded description before wiring. Full paper (SSRN 7470000) returned 403; user supplied a PDF at docs/economic-policy-for-agi-ssrn.pdf (untracked, not committed: redistribution undecided). Paper abstract says 24 interventions vs essay's 11; recorded in reconstruction.md 5a. Next: review feedback, tests first, loader + render_prompt, point config inputs_dir, prereg rows.

2026-10-04: acceptance criteria and plan rewritten to the v2.1 design (one call per persona x policy is the baseline; joint scoring is design change D1; order variants dropped because a single-policy prompt has no policy order). Earlier drafts (essay-based 15 criteria, all_policies and one_policy templates) predate the SSRN paper and need rework. Follow-on tasks: TASK-31 (named personas), TASK-32 (design expander), TASK-33 (per-policy evidence in job building).

2026-10-04 draft phase (v2.1): code + tests, no wiring. New: domain/study_prompt.py (placeholder contract per call unit, render_persona_policy for B/Q1/Q2/Q3, render_joint for D1, neutral codes P1..P11), bootstrap/prompt_files.py (load_templates, load_description_paraphrases, sha256 manifest check); tests in tests/domain/test_study_prompt.py and tests/bootstrap/test_prompt_files.py (criteria count/ids, all templates render, unknown template/unit fails, description-only shows no policy name or acronym, manifest hashes). Old prompts/all_policies and one_policy drafts replaced. NOT done (needs review first): AC6 config inputs_dir, prereg R5 and prompt-wording row, job builder and response-schema wiring. USER MUST REVIEW: (1) designs/inputs/criteria.yaml (13 criteria, Table 1 + Figure 1 verbatim; Implementation Readiness wording is ours); (2) designs/inputs/policies.yaml (Table 3 verbatim, ids = evidence packet names); (3) prompts/persona_policy/baseline.txt (B); (4) prompts/persona_policy/para_1.txt, para_2.txt, para_3.txt (Q3a-c); (5) prompts/joint/baseline.txt (D1); (6) designs/inputs/description_paraphrases/para_1.yaml, para_2.yaml, para_3.yaml (Q2a-c, 33 entries); (7) prompts/manifest.yaml (hashes, element checklists; status draft). Persona preamble (EDSL wording) and block headings (Evidence:, Policy:, Criteria:) are fixed in study_prompt.py, not paraphrased.

2026-10-04 wiring (16b), user approved the drafts as they stand: personas/ moved (git mv, content unchanged) to designs/inputs/personas so config.yaml paths.inputs_dir = designs/inputs loads both panels (named, reconstructed; 51 each), 13 criteria, 11 policies; smoketest configs keep designs/smoketest/inputs. prompts/manifest.yaml status reviewed-by-user 2026-10-04, hashes unchanged. prereg: 13 criteria; call counts recomputed (B 561/config-repeat, D1 51x13=663, D2 11; full plan 561(k_R+1)+7406 k_Q = 25,584 calls at k_R=5,k_Q=3); s8 priority with D2b after D2, R-T and D cells k_Q repeats, stopping rule; decisions log; Readiness limitation; s12 items 4, 8, 9. reconstruction.md: R5 decided with file refs, s3 criteria sentence fixed, persona paths. Expander: removed k_rt and per-D-cell repeats (R-T and D cells now k_Q, loader rejects k_rt and d_cells repeats) to match s8. Evidence: designs/inputs has no evidence/ dir, so load_inputs returns no evidence for the study inputs; per-policy packets are TASK-33. Validation: uv run pytest -q 356 passed; ruff check clean.

2026-10-04 fix round 1: D2 restored to a dedicated repeat count (d2_repeats, default 51: 11 x 51 = 561 calls, one B repeat's worth, independent noise estimator); D1, D2b, D3 stay at k_Q. Prereg s5/s8/decisions log and totals updated: full plan 561(k_R+2) + 7,395 k_Q = 26,112 calls at k_R=5, k_Q=3. pytest 358 passed, ruff clean.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Criteria (13), Table 3 policies, baseline/Q3/D1 templates and Q2 paraphrases drafted, hashed in prompts/manifest.yaml and reviewed by the user 2026-10-04; pure renderer (domain/study_prompt.py) and loaders (bootstrap/prompt_files.py); study config points at designs/inputs (personas moved there); prereg and reconstruction updated (R5, wording rows, 13-criterion call counts, s8 stopping rule, decisions log, TODOs); expander repeats follow s8. Verified with uv run pytest -q (356 passed, incl. criteria ids, all templates render, description-only has no policy names, manifest hashes, config inputs load) and ruff check. Prereg stays DRAFT.
<!-- SECTION:FINAL_SUMMARY:END -->
