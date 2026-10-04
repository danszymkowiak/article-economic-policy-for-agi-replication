---
id: TASK-19
title: Rank stability
status: Done
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 08:32'
labels:
  - phase4
dependencies:
  - TASK-18
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15. Analysis reads only from results/raw.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Kendall tau computed between configurations
- [x] #2 Bootstrap confidence intervals reported
- [x] #3 Alternative score aggregations (e.g. mean, median, trimmed mean) compared for rank stability
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Refactor TASK-18 reader into cell_observations(store) (all cells, joint D1 jobs included); baseline_observations delegates.
2. Domain analysis_rank.py (pure, numpy): per-cell persona x repeat arrays, aggregation over personas (mean, median, 10% trimmed mean), repeat-mean panels and composites (reuse COMPOSITES), vectorised Kendall tau-b (checked against analysis_baseline.kendall_tau_b), average-rank shifts, top-3/bottom-3 set changes.
3. Cell vs B per composite and aggregation: tau, persona-bootstrap percentile CI (paired resampling of shared personas; placeholder 1000 resamples, prereg s12 item 6 open), single-run tau range, repeat-noise reference: pairwise single-repeat taus among B repeats and the s3 split band (k-repeat mean vs remaining B repeats).
4. Aggregation comparison: tau between aggregations within each cell, and stability metrics per aggregation.
5. application/rank_stability.py: run + Markdown/CSV rendering (non-inference label, wording rule); CLI 'analyze ranks'.
6. Tests first on synthetic rows: identical -> 1, reversed -> -1, noise; bootstrap CI contains point; aggregations differ under outliers.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: read only from results/raw; count only status ok rows as ratings; treat deferred rows as budget-censored (not run), failed as model failures, duplicate as ignored; report the counts of each.

Decisions: numpy added (uv add numpy) for the vectorised persona bootstrap; full study scale (B k=5, 14 cells, 51 personas, 1000 resamples) runs in about 29 s. Bootstrap resample count 1000 is a PLACEHOLDER (prereg s12 item 6 open), flagged in the report. Median and 10% trimmed mean are not in prereg s6, so the report labels the aggregation comparison exploratory. 'Per-policy rankings' read as the 11 single-criterion columns (already in COMPOSITES) plus per-policy rank shifts. Completeness is per persona x policy x criterion triplet (so D1 joint jobs fit); paired comparisons keep triplets complete in both cells. cell_observations() now reads every cell (incl. D1 joint jobs); baseline_observations delegates to it. Pilot store check (non-inference, output in scratchpad only) runs cleanly. Tests: uv run pytest -q 484 passed; ruff clean.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added rank stability analysis: domain/analysis_rank.py (pure numpy: aggregations mean/median/10% trimmed mean, vectorised Kendall tau-b checked against the TASK-18 tau-b, persona-bootstrap percentile CIs with paired/independent/no-persona rules, single-run range, B repeat-noise pairwise taus and s3 split bands, per-policy average-rank shifts, top-3/bottom-3 set changes, between-aggregation agreement), application/rank_stability.py (Markdown + 4 CSVs, non-inference label, wording rule) and CLI 'llm-panel analyze ranks [--resamples --seed --out]'. Verified with synthetic-row tests (identical cells tau 1, reversed -1, noise in between, outlier persona moves mean but not median/trimmed mean) in tests/domain/test_analysis_rank.py and tests/test_rank_stability.py; full suite 484 passed.
<!-- SECTION:FINAL_SUMMARY:END -->
