---
id: TASK-38
title: 'Reversed-scale probe (0 = best, 100 = worst), exploratory'
status: Done
assignee:
  - '@claude'
created_date: '2026-10-05 18:58'
updated_date: '2026-10-05 22:00'
labels:
  - exploratory
dependencies:
  - TASK-22
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Separate, labeled, exploratory probe (post-freeze, pre-data amendment in prereg s13; not pooled with the main analysis or the adversarial arm). Asks whether glm-5.3-flash gives the mirror image when the rating scale is reversed: B's persona x policy prompt with the scale instruction changed so that 0 is best and 100 is worst, on the adversarial arm's 5-persona search panel (seed 20261004), every policy, seed 0: 55 calls (about 0.08 USD actual). Scores are converted with 100 - x. The comparison is the adversarial arm's baseline run (seed 0), with its seed-1 rerun as the repeat-noise reference. Not a catalogue entry: if the model ignored the reversal, converting would push the top policy to the bottom and the arm would count that as a success (instruction-following, not instability). Own directory, store, ledger and ceiling; counts toward the global 15 USD cap in both directions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Measures stated in prereg s13 before data: rating- and panel-mean-level r and mean signed difference after conversion, units beyond M = 5, Kendall tau per composite, target rank, clauses, and a per-call 'looks unconverted' rule, each beside the same quantity for the seed-1 rerun
- [x] #2 Probe has its own store, ledger and ceiling; its ledger counts toward the global cap from config.yaml and the adversarial config, and the probe counts theirs
- [x] #3 Tests cover job building, conversion, the unconverted rule and the report; full test suite passes
- [x] #4 Run only after the user's go-ahead, through --confirm; report headed EXPLORATORY and written to its own directory
- [x] #5 Reversed template in scale_probe/prompts/ (not prompts/, so the study's frozen template set is untouched) with its sha256 in scale_probe/manifest.yaml; wording reviewed by the user before any paid call
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pure analysis (scale_probe/analysis.py) with tests first. 2. Reversed template = baseline with one sentence replaced; manifest hash; CLI refuses on mismatch. 3. Application/CLI/report modeled on adversarial/, reusing its search panel, seeds and baseline jobs; adversarial store read-only. 4. Spend wiring both directions. 5. prereg s13 entry before data. 6. User reviews wording, approves opencode, then submit/collect/report.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built scale_probe/ (analysis, probe, report, cli, config 0.30 USD, manifest, README); tests/scale_probe (31 tests). All configs count scale_probe ledger; pilot tests updated for the new pattern. prereg s13: adversarial run entry and probe entry, written before probe data. Awaiting user review of the template wording and go-ahead.

2026-10-05 run: 55/55 ok, 0 failed. Report scale_probe/report.md. Model follows the reversal (raw r -0.91; 1 of 36 classifiable calls unconverted, 19 undecidable). Converted: mean signed -1.5, 32 Table 4 units beyond M vs 12 for the seed-1 rerun; median tau 0.85 vs 0.88; clauses unchanged. Side finding: the adversarial seed-0 baseline rates UBC on Full Transformation 40-70 across the 5 personas vs 70-84 in the rerun; the arm's target UBI rests on that noisy run (prereg s14 winner's curse).

Verified: 659 tests pass, ruff clean; scale_probe run 55/55 ok through --confirm after user go-ahead; report headed EXPLORATORY in scale_probe/report.md; prereg s13 entry precedes the data.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added scale_probe/, a separate exploratory reversed-scale probe (0 = best): one-sentence template change pinned by hash, run on the adversarial arm's 5-persona panel against its baseline and seed-1 rerun, own store/ledger/0.30 USD ceiling counted in the global cap. Result: the model follows the reversal (raw r -0.91, 1 of 36 classifiable calls unconverted); converted scores 1.5 points lower, 32 vs 12 Table 4 units beyond M against the noise rerun; clauses unchanged. Verified by 31 probe tests and the full suite; awaiting user review before Done.
<!-- SECTION:FINAL_SUMMARY:END -->
