---
id: TASK-16
title: Prompt templates
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 07:36'
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
- [ ] #1 designs/inputs/criteria.yaml holds the paper's criteria (13 panel criteria of Table 4 and Appendix B, plus Political Support and Administrative Capacity and Speed for the essay comparison), with wording from paper Table 1 and Figure 1; the loader reads them and a test checks the count and ids
- [ ] #2 Baseline template: one persona x one policy, all criteria returned in one JSON object, policy shown by Table 3 name and definition; wording drafted and reviewed by the user before wiring
- [ ] #3 Description-only variant (Q1): policy name replaced by its definition and neutral codes P1..P11; a test shows no policy name appears in the rendered prompt
- [ ] #4 Frozen paraphrase sets: three meaning-preserving paraphrases of the policy definitions (Q2) and three of the instruction text (Q3), each hashed, with an equivalence check recorded; user reviews every one
- [ ] #5 Joint-scoring template (design change D1): all 11 policies in one prompt per persona x criterion, kept as a variant
- [ ] #6 config.yaml inputs_dir points at the real inputs; prereg R5 and the prompt-wording row are updated; tests first, run, then stop for user review
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rewrite criteria.yaml to the paper's wording (user reviews). 2. Draft baseline and variant templates under prompts/ for user review of EVERY prompt before wiring. 3. Tests first: render all templates, same placeholder contract, description-only has no names, unknown template fails. 4. Loader and render_prompt for the one-persona-per-policy format; joint-scoring kept as variant. 5. Freeze paraphrases by hash with equivalence check. 6. Point config inputs_dir at real inputs, update prereg R5; run tests; stop for review. Per-policy evidence wiring, named personas and the design expander are TASK-31, 32, 33.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

2026-10-04 drafted for review (no code/tests yet): designs/inputs/{policies,criteria}.yaml (11 policies named+blinded; 15 criteria quoting essay footnotes, user agreed terse wording) and prompts/{all_policies,one_policy}/{baseline,para_1..4}.txt. User will review every prompt and blinded description before wiring. Full paper (SSRN 7470000) returned 403; user supplied a PDF at docs/economic-policy-for-agi-ssrn.pdf (untracked, not committed: redistribution undecided). Paper abstract says 24 interventions vs essay's 11; recorded in reconstruction.md 5a. Next: review feedback, tests first, loader + render_prompt, point config inputs_dir, prereg rows.

2026-10-04: acceptance criteria and plan rewritten to the v2.1 design (one call per persona x policy is the baseline; joint scoring is design change D1; order variants dropped because a single-policy prompt has no policy order). Earlier drafts (essay-based 15 criteria, all_policies and one_policy templates) predate the SSRN paper and need rework. Follow-on tasks: TASK-31 (named personas), TASK-32 (design expander), TASK-33 (per-policy evidence in job building).

2026-10-04 draft phase (v2.1): code + tests, no wiring. New: domain/study_prompt.py (placeholder contract per call unit, render_persona_policy for B/Q1/Q2/Q3, render_joint for D1, neutral codes P1..P11), bootstrap/prompt_files.py (load_templates, load_description_paraphrases, sha256 manifest check); tests in tests/domain/test_study_prompt.py and tests/bootstrap/test_prompt_files.py (criteria count/ids, all templates render, unknown template/unit fails, description-only shows no policy name or acronym, manifest hashes). Old prompts/all_policies and one_policy drafts replaced. NOT done (needs review first): AC6 config inputs_dir, prereg R5 and prompt-wording row, job builder and response-schema wiring. USER MUST REVIEW: (1) designs/inputs/criteria.yaml (13 criteria, Table 1 + Figure 1 verbatim; Implementation Readiness wording is ours); (2) designs/inputs/policies.yaml (Table 3 verbatim, ids = evidence packet names); (3) prompts/persona_policy/baseline.txt (B); (4) prompts/persona_policy/para_1.txt, para_2.txt, para_3.txt (Q3a-c); (5) prompts/joint/baseline.txt (D1); (6) designs/inputs/description_paraphrases/para_1.yaml, para_2.yaml, para_3.yaml (Q2a-c, 33 entries); (7) prompts/manifest.yaml (hashes, element checklists; status draft). Persona preamble (EDSL wording) and block headings (Evidence:, Policy:, Criteria:) are fixed in study_prompt.py, not paraphrased.
<!-- SECTION:NOTES:END -->
