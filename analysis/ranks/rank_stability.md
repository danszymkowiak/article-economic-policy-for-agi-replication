# Rank stability between cells

- Store: `results/raw/rows.jsonl`.

## Data

| Cell | ok jobs | not ok | deferred | duplicate rows | repeats | personas | pairing with B |
|---|---|---|---|---|---|---|---|
| B | 2803 | 2 (failed 2) | 0 | 0 | 5 | 51 | (reference) |
| B' | 561 | 0 (failed 0) | 0 | 0 | 1 | 51 | paired |
| Q1 | 1683 | 0 (failed 0) | 0 | 0 | 3 | 51 | paired |
| Q4 | 1683 | 0 (failed 0) | 0 | 0 | 3 | 51 | paired |
| Q3c | 100 | 0 (failed 0) | 0 | 0 | 1 | 10 | paired |
| D2 | 555 | 6 (failed 6) | 0 | 0 | 51 | 0 | no personas |

_Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes)._

- Persona bootstrap: 2000 resamples, seed 0; 95% percentile intervals. The count is prereg s12 item 6 (set 2026-10-04).
- B repeats: 5. Primary aggregation: unweighted mean over personas (prereg s4).

## Repeat-noise reference: Kendall tau among B's repeats (mean aggregation)

Pairwise: tau between two single B repeats. Split k: tau between the mean of k B repeats and the mean of the remaining ones, over every split (prereg s3; a descriptive band, not a test: the splits overlap).

| Composite | Kind | n | min | median | max |
|---|---|---|---|---|---|
| mild_disruption | pairwise | 10 | 0.89 | 0.96 | 1.00 |
| moderate_disruption | pairwise | 10 | 0.88 | 0.91 | 1.00 |
| full_transformation | pairwise | 10 | 0.96 | 1.00 | 1.00 |
| welfare_resilience | pairwise | 10 | 0.96 | 1.00 | 1.00 |
| agency_voice | pairwise | 10 | 0.96 | 0.96 | 1.00 |
| feasibility | pairwise | 10 | 0.96 | 0.96 | 1.00 |
| scenario_durability | pairwise | 10 | 0.89 | 0.96 | 1.00 |
| mild_disruption | split_k1 | 5 | 0.93 | 0.96 | 0.96 |
| moderate_disruption | split_k1 | 5 | 0.88 | 0.89 | 0.89 |
| full_transformation | split_k1 | 5 | 0.96 | 1.00 | 1.00 |
| welfare_resilience | split_k1 | 5 | 0.96 | 1.00 | 1.00 |
| agency_voice | split_k1 | 5 | 0.96 | 1.00 | 1.00 |
| feasibility | split_k1 | 5 | 0.96 | 1.00 | 1.00 |
| scenario_durability | split_k1 | 5 | 0.93 | 0.96 | 1.00 |
| mild_disruption | split_k3 | 10 | 0.89 | 0.96 | 1.00 |
| moderate_disruption | split_k3 | 10 | 0.85 | 0.89 | 0.93 |
| full_transformation | split_k3 | 10 | 1.00 | 1.00 | 1.00 |
| welfare_resilience | split_k3 | 10 | 0.96 | 1.00 | 1.00 |
| agency_voice | split_k3 | 10 | 0.96 | 1.00 | 1.00 |
| feasibility | split_k3 | 10 | 0.96 | 0.98 | 1.00 |
| scenario_durability | split_k3 | 10 | 0.96 | 1.00 | 1.00 |

## Kendall tau versus B (mean aggregation, prereg composites)

Each entry: tau-b [persona-bootstrap 95% interval].

| Cell | mild_disruption | moderate_disruption | full_transformation | welfare_resilience | agency_voice | feasibility | scenario_durability |
|---|---|---|---|---|---|---|---|
| B' | 0.96 [0.85, 1.00] | 0.96 [0.85, 1.00] | 1.00 [0.96, 1.00] | 1.00 [0.93, 1.00] | 0.96 [0.93, 1.00] | 0.96 [0.89, 1.00] | 0.93 [0.85, 1.00] |
| Q1 | 0.78 [0.71, 0.86] | 0.78 [0.71, 0.93] | 0.93 [0.89, 0.96] | 0.93 [0.85, 0.96] | 0.85 [0.82, 0.89] | 0.89 [0.82, 0.89] | 0.75 [0.67, 0.78] |
| Q4 | 0.78 [0.78, 0.85] | 0.78 [0.75, 0.93] | 1.00 [0.93, 1.00] | 0.93 [0.89, 0.93] | 0.93 [0.89, 0.96] | 0.93 [0.89, 0.96] | 0.85 [0.78, 0.89] |
| Q3c | 0.89 [0.78, 0.96] | 0.96 [0.72, 0.96] | 1.00 [0.89, 1.00] | 0.93 [0.82, 1.00] | 0.93 [0.89, 1.00] | 0.96 [0.82, 1.00] | 0.89 [0.75, 0.93] |
| D2 | 0.78 [0.71, 0.82] | 0.93 [0.82, 0.96] | 0.93 [0.93, 0.93] | 0.89 [0.89, 0.93] | 0.85 [0.85, 0.89] | 0.93 [0.93, 0.96] | 0.89 [0.85, 0.93] |

## Against repeat noise and single runs (mean aggregation, prereg composites)

Below band: composites whose tau is under the minimum of B's split band for the cell's repeat count (n/a when the cell has as many repeats as B or more). Single-run range: each repeat of the cell against B's repeat mean, over the prereg composites.

| Cell | repeats | below band | single-run tau range | top-3 changes | bottom-3 changes | max abs. rank shift |
|---|---|---|---|---|---|---|
| B' | 1 | none | 0.93 to 1.00 | none | moderate_disruption (+almp -directed_industrial_policy); feasibility (+directed_industrial_policy -ubs); scenario_durability (+wage_insurance -eitc) | 2.0 |
| Q1 | 3 | mild_disruption, moderate_disruption, full_transformation, welfare_resilience, agency_voice, feasibility, scenario_durability | 0.71 to 0.96 | moderate_disruption (+ubs -sawf); feasibility (+wage_insurance -nit); scenario_durability (+ubs -ubc) | moderate_disruption (+almp -directed_industrial_policy); agency_voice (+almp -directed_industrial_policy); scenario_durability (+wage_insurance -directed_industrial_policy) | 3.0 |
| Q4 | 3 | mild_disruption, moderate_disruption, welfare_resilience, agency_voice, feasibility, scenario_durability | 0.78 to 1.00 | feasibility (+wage_insurance -nit) | moderate_disruption (+almp -directed_industrial_policy); scenario_durability (+wage_insurance -directed_industrial_policy) | 3.0 |
| Q3c | 1 | mild_disruption, welfare_resilience, agency_voice, scenario_durability | 0.89 to 1.00 | feasibility (+wage_insurance -nit) | moderate_disruption (+almp -directed_industrial_policy) | 2.0 |
| D2 | 51 | n/a | 0.34 to 1.00 | moderate_disruption (+ubs -sawf); welfare_resilience (+ubi -ui) | full_transformation (+ui -almp); feasibility (+directed_industrial_policy -ubs); scenario_durability (+wage_insurance -almp) | 3.0 |

## Aggregation over personas (exploratory)

Not in prereg s6, so exploratory. Range of tau versus B over all 15 composites, under each aggregation applied to both sides; then the lowest tau between two aggregations of the same cell's scores.

| Cell | vs B, mean | vs B, median | vs B, trimmed_mean_10 |
|---|---|---|---|
| B' | 0.82 to 1.00 | 0.92 to 1.00 | 0.82 to 1.00 |
| Q1 | 0.64 to 0.93 | 0.65 to 0.95 | 0.60 to 0.93 |
| Q4 | 0.67 to 1.00 | 0.69 to 0.99 | 0.67 to 0.96 |
| Q3c | 0.78 to 1.00 | 0.65 to 0.98 | 0.78 to 1.00 |
| D2 | 0.42 to 0.96 | 0.42 to 0.96 | 0.42 to 0.96 |

| Cell | min tau mean vs median | min tau mean vs trimmed_mean_10 | min tau median vs trimmed_mean_10 |
|---|---|---|---|
| B | 0.86 | 0.95 | 0.90 |
| B' | 0.92 | 0.96 | 0.92 |
| Q1 | 0.88 | 0.93 | 0.92 |
| Q4 | 0.92 | 0.96 | 0.92 |
| Q3c | 0.87 | 0.93 | 0.80 |
| D2 | 1.00 | 1.00 | 1.00 |

## How to read this

- A cell without personas (D2) makes one call per policy and repeat, so a failed call drops only that repeat x policy: its means average the surviving repeats per policy, and its single runs, repeat-noise SE and variance components use only the repeats with no failed call (TASK-37, prereg s13).
- Rank metrics are reported for every cell because the paper makes its recommendations by rank order, but they are secondary to the flip counts and materiality shifts (prereg s6). Tau moves only when near-ties swap, and the published scores have many.
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong.
- The persona bootstrap asks whether other personas would agree. It is secondary, a generalisation caveat only, and is not mixed into the comparison with repeat noise (prereg s3). Paired cells share B's persona draw; D2b (another panel) gets its own draw; D2 (no persona) is not resampled.
- Ties count by Kendall tau-b's correction; ranks are average ranks (rank 1 = highest score). A policy is in the top 3 when its average rank is at most 3, so a tie across the boundary is in neither set.
- Block D cells change the design, not a small detail, and are read separately from blocks R and Q (prereg s5).
- Every composite and every cell is reported (CSV files hold all composites, aggregations and per-policy rank shifts). Political Support and Administrative Capacity & Speed are not in any composite.
