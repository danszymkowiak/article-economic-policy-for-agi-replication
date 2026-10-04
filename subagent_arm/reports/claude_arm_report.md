# Claude subagent arm: descriptive report (separate arm, not pooled)

**Separate, labeled arm.** Claude Haiku 4.5 run as Claude Code subagents (restricted `rater` agent, alias `claude-haiku-4-5`, no temperature/seed control). Differences from any other model mix model, agentic harness and uncontrolled sampling. Descriptive only; no inference language. Instability of scores shows they lack the claimed precision, not that the recommendations are wrong.

## 0. Completeness and failures

- 663 valid persona x policy calls: pass 1 = 561, UBC repeats = 102.
- 5 invalid first attempts out of 668 rows (0.7% of rows); every one was retried and passed. 2 of them were caused by a driver-side typo in the agent prompt (task file not found), not by the rater; discards are logged in the store.

## 1. Stability (UBC, the repeated policy)

Panel mean (51 personas) per pass, and pass-to-pass spread:

| criterion | pass 1 | pass 2 | pass 3 | SD across passes | range |
|---|---|---|---|---|---|
| standards_of_living | 72.2 | 71.9 | 71.8 | 0.22 | 0.4 |
| meaning_human_value | 60.5 | 61.8 | 60.0 | 0.92 | 1.8 |
| macro_stabilisation | 46.8 | 46.1 | 44.1 | 1.41 | 2.7 |
| economic_agency_mobility | 75.2 | 75.8 | 74.8 | 0.49 | 1.0 |
| ownership_of_gains | 85.8 | 85.4 | 85.9 | 0.24 | 0.4 |
| democratic_voice | 68.9 | 68.8 | 68.0 | 0.46 | 0.8 |
| political_support | 60.3 | 62.4 | 59.9 | 1.33 | 2.5 |
| economic_feasibility | 50.0 | 52.5 | 50.8 | 1.27 | 2.5 |
| admin_capacity_speed | 62.4 | 60.9 | 62.2 | 0.79 | 1.4 |
| implementation_readiness | 54.9 | 56.4 | 57.0 | 1.07 | 2.1 |
| mild_disruption | 67.1 | 67.0 | 67.1 | 0.08 | 0.2 |
| moderate_disruption | 75.8 | 74.7 | 74.6 | 0.63 | 1.1 |
| full_transformation | 81.9 | 80.6 | 82.4 | 0.96 | 1.9 |

Largest pass-to-pass range in a panel mean: 2.7; median 1.4; cells with range above the materiality margin M = 5: 0 of 13.

Persona-level noise and variance decomposition (per criterion, one-way on personas, 3 passes):

| criterion | persona SD (of 3-pass means) | within-persona run SD | run share of single-rating variance |
|---|---|---|---|
| standards_of_living | 0.8 | 3.6 | 95% |
| meaning_human_value | 0.0 | 6.5 | 100% |
| macro_stabilisation | 4.5 | 9.6 | 82% |
| economic_agency_mobility | 0.8 | 3.3 | 94% |
| ownership_of_gains | 0.9 | 3.0 | 92% |
| democratic_voice | 0.0 | 4.2 | 100% |
| political_support | 0.0 | 6.0 | 100% |
| economic_feasibility | 0.3 | 6.6 | 100% |
| admin_capacity_speed | 2.5 | 9.7 | 94% |
| implementation_readiness | 0.0 | 8.8 | 100% |
| mild_disruption | 0.0 | 6.4 | 100% |
| moderate_disruption | 0.6 | 4.2 | 98% |
| full_transformation | 0.7 | 4.7 | 98% |

Median run share of single-rating variance: 98%. Single ratings from the same persona on the same policy differ across passes by roughly the within-persona run SD shown; the 51-persona panel mean averages most of that out.

UBC rank among the 11 policies on each Table 4 criterion, with UBC from each pass and the other policies' pass-1 means (1 = highest):

| criterion | pass 1 | pass 2 | pass 3 |
|---|---|---|---|
| standards_of_living | 9 | 9 | 9 |
| meaning_human_value | 6 | 5 | 6 |
| macro_stabilisation | 9 | 10 | 11 |
| economic_agency_mobility | 2 | 2 | 2 |
| ownership_of_gains | 1 | 1 | 1 |
| democratic_voice | 1 | 1 | 1 |
| economic_feasibility | 8 | 8 | 8 |
| implementation_readiness | 8 | 8 | 8 |
| mild_disruption | 10 | 10 | 10 |
| moderate_disruption | 1 | 1 | 1 |
| full_transformation | 1 | 1 | 1 |

## 2. Distribution of responses (pass 1, all 561 calls)

| criterion | mean | SD | p10 | median | p90 | % multiple of 5 | % in 0-10 | % in 90-100 |
|---|---|---|---|---|---|---|---|---|
| standards_of_living | 73.4 | 7.0 | 65 | 75 | 82 | 50% | 0% | 0% |
| meaning_human_value | 61.3 | 11.1 | 45 | 62 | 75 | 51% | 0% | 0% |
| macro_stabilisation | 66.0 | 14.5 | 42 | 71 | 80 | 48% | 0% | 0% |
| economic_agency_mobility | 67.6 | 10.1 | 52 | 70 | 78 | 42% | 0% | 0% |
| ownership_of_gains | 38.4 | 23.3 | 20 | 30 | 85 | 55% | 0% | 1% |
| democratic_voice | 56.9 | 10.7 | 42 | 58 | 70 | 45% | 0% | 0% |
| political_support | 64.5 | 10.7 | 48 | 66 | 77 | 41% | 0% | 0% |
| economic_feasibility | 54.3 | 9.5 | 40 | 55 | 66 | 43% | 0% | 0% |
| admin_capacity_speed | 67.8 | 14.0 | 48 | 70 | 85 | 42% | 0% | 1% |
| implementation_readiness | 64.0 | 17.4 | 40 | 64 | 89 | 41% | 0% | 10% |
| mild_disruption | 72.2 | 7.2 | 62 | 75 | 80 | 39% | 0% | 0% |
| moderate_disruption | 61.3 | 12.0 | 45 | 60 | 77 | 42% | 0% | 0% |
| full_transformation | 47.3 | 24.5 | 20 | 39 | 82 | 42% | 1% | 0% |

All ratings: mean 61.1, SD 17.1; share multiples of 5 45%; share of 10s multiples 20%.

Persona spread: SD of persona means (each over all policies and criteria) = 1.21; range 58.4 to 65.1.
Mean across policies of the between-persona SD per criterion: min 3.7, median 6.6, max 8.7.

Halo: mean pairwise correlation among the 13 criteria across calls, after centring each policy's ratings on its panel mean (so it is persona-driven co-movement): 0.19 (min -0.08, max 0.63). Same without centring: 0.13.
Rationale length (characters): mean 184, median 183, max 309.

## 3. Agreement with published Table 4 (pass 1 panel means; UBC also with 3-pass mean)

Policies compared: ['almp', 'directed_industrial_policy', 'eitc', 'fjg', 'nit', 'sawf', 'ubc', 'ubi', 'ubs', 'ui', 'wage_insurance']

| composite | n | Spearman | Kendall tau-b | mean abs diff | mean signed diff (ours - published) |
|---|---|---|---|---|---|
| standards_of_living | 11 | 0.46 | 0.31 | 13.6 | +13.6 |
| meaning_human_value | 11 | -0.05 | -0.05 | 12.8 | +6.4 |
| macro_stabilisation | 11 | 0.35 | 0.27 | 17.3 | +14.0 |
| economic_agency_mobility | 11 | -0.04 | 0.02 | 10.2 | +7.8 |
| ownership_of_gains | 11 | 0.73 | 0.67 | 12.4 | +1.7 |
| democratic_voice | 11 | 0.41 | 0.31 | 5.8 | +3.2 |
| economic_feasibility | 11 | -0.39 | -0.20 | 17.2 | -3.8 |
| implementation_readiness | 11 | 0.89 | 0.75 | 10.4 | +8.1 |
| mild_disruption | 11 | 0.19 | 0.16 | 18.4 | +18.1 |
| moderate_disruption | 11 | 0.42 | 0.27 | 13.9 | +7.3 |
| full_transformation | 11 | 0.85 | 0.71 | 14.0 | -7.7 |
| welfare_resilience | 11 | 0.27 | 0.24 | 11.7 | +11.4 |
| agency_voice | 11 | 0.47 | 0.35 | 6.8 | +4.2 |
| feasibility | 11 | 0.62 | 0.49 | 12.2 | +2.2 |
| scenario_durability | 11 | 0.57 | 0.42 | 11.8 | +5.9 |

UBC cells, Claude pass 1 / 3-pass mean / published:

| criterion | pass 1 | 3-pass mean | published | diff (3-pass - published) |
|---|---|---|---|---|
| standards_of_living | 72.2 | 72.0 | 69.8 | +2.2 |
| meaning_human_value | 60.5 | 60.8 | 52.3 | +8.5 |
| macro_stabilisation | 46.8 | 45.7 | 64.0 | -18.3 |
| economic_agency_mobility | 75.2 | 75.3 | 66.7 | +8.6 |
| ownership_of_gains | 85.8 | 85.7 | 94.9 | -9.2 |
| democratic_voice | 68.9 | 68.6 | 67.2 | +1.4 |
| economic_feasibility | 50.0 | 51.1 | 55.0 | -3.9 |
| implementation_readiness | 54.9 | 56.1 | 30.0 | +26.1 |
| mild_disruption | 67.1 | 67.1 | 63.0 | +4.1 |
| moderate_disruption | 75.8 | 75.0 | 66.0 | +9.0 |
| full_transformation | 81.9 | 81.6 | 93.5 | -11.9 |

UBC cells where Claude's 3-pass mean differs from the published value by more than 5: 7 of 11.

## 4. Not computed here

The Claude-versus-B comparisons (cells shifted by more than M = 5 against B, B's repeat noise beside Claude's, rank and clause comparison against B) need the main arm's baseline B store (`results/raw`), which is empty: the preregistered main run has not been made. They are left until it exists. The published-Table 4 comparison above is the only between-source comparison available now.
