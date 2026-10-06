# Materiality shifts

- Store: `results/raw/rows.jsonl`.

## Data

| Cell | ok jobs | not ok | deferred | duplicate rows | repeats |
|---|---|---|---|---|---|
| B | 2803 | 2 (failed 2) | 0 | 0 | 5 |
| B' | 561 | 0 (failed 0) | 0 | 0 | 1 |
| Q1 | 1683 | 0 (failed 0) | 0 | 0 | 3 |
| Q4 | 1683 | 0 (failed 0) | 0 | 0 | 3 |
| Q3c | 100 | 0 (failed 0) | 0 | 0 | 1 |
| D2 | 555 | 6 (failed 6) | 0 | 0 | 51 |

_Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes)._

## Policy x criterion means shifted by more than M = 5 points (primary)

Primary metric 2 of prereg s6: per cell, the number of policy x criterion panel means whose |shift from B| exceeds M = 5 points, set in advance. Shift = cell repeat mean - B repeat mean, unweighted panel means on the common-complete set. Noise SE: the repeat-noise standard error of one unit's shift; M / SE gives the margin as a repeat-noise multiple. B split band: the same count for every split of B's repeats into the cell's repeat count and the rest, min / median / max (what repeats alone do; descriptive, not a test; n/a when the cell has as many repeats as B or more). M = 3 and M = 8 are a descriptive sensitivity and are not used to pick M.

| Cell | factor | pairing | repeats | units | beyond M = 5 | B split band (M = 5) | noise SE | M / SE | beyond 3 | beyond 8 | noise |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B' | drift (B repeated at the end) | paired | 1 | 121 | **0** | 0 / 0 / 0 (n=5) | 0.85 | 5.9 | 0 | 0 | B |
| Q1 | policy identifier (name removed) | paired | 3 | 121 | **15** | 0 / 0 / 0 (n=10) | 0.66 | 7.6 | 36 | 6 | own |
| Q4 | evidence packet (none) | paired | 3 | 121 | **19** | 0 / 0 / 0 (n=10) | 0.56 | 8.9 | 38 | 1 | own |
| Q3c | instruction wording | paired | 1 | 121 | **2** | 2 / 3 / 7 (n=5) | 2.00 | 2.5 | 21 | 0 | B |
| D2 | persona (none) | no personas | 51 | 121 | **12** | n/a | 0.76 | 6.6 | 30 | 2 | own |

## Units beyond M = 5, per cell

- B': none.
- Q1: directed_industrial_policy x democratic_voice +14.5 (22.1 SE); directed_industrial_policy x macro_stabilisation +13.7 (20.9 SE); nit x implementation_readiness -12.5 (-19.0 SE); directed_industrial_policy x meaning_human_value +11.7 (17.8 SE); directed_industrial_policy x standards_of_living +11.3 (17.2 SE); ubs x full_transformation +10.6 (16.2 SE); directed_industrial_policy x economic_feasibility +7.8 (11.9 SE); directed_industrial_policy x mild_disruption +7.6 (11.6 SE); directed_industrial_policy x economic_agency_mobility +7.3 (11.1 SE); nit x economic_feasibility -6.5 (-9.9 SE); ubc x economic_feasibility +6.1 (9.3 SE); ubi x mild_disruption +5.8 (8.9 SE); directed_industrial_policy x moderate_disruption +5.7 (8.7 SE); ubc x full_transformation -5.6 (-8.5 SE); directed_industrial_policy x full_transformation +5.1 (7.7 SE).
- Q4: directed_industrial_policy x meaning_human_value +8.9 (16.0 SE); sawf x meaning_human_value -8.0 (-14.3 SE); ui x economic_agency_mobility -7.5 (-13.4 SE); sawf x full_transformation +7.3 (13.1 SE); directed_industrial_policy x moderate_disruption +7.0 (12.6 SE); ubc x implementation_readiness -6.7 (-12.0 SE); sawf x democratic_voice -6.2 (-11.1 SE); ubi x meaning_human_value -6.2 (-11.1 SE); directed_industrial_policy x standards_of_living +6.0 (10.7 SE); directed_industrial_policy x macro_stabilisation +6.0 (10.7 SE); nit x implementation_readiness -6.0 (-10.7 SE); almp x economic_feasibility +5.6 (10.1 SE); ui x economic_feasibility +5.5 (9.9 SE); ubi x mild_disruption -5.4 (-9.7 SE); directed_industrial_policy x mild_disruption +5.4 (9.6 SE); almp x standards_of_living -5.2 (-9.4 SE); sawf x mild_disruption -5.2 (-9.3 SE); sawf x moderate_disruption +5.2 (9.2 SE); ubs x economic_feasibility -5.1 (-9.1 SE).
- Q3c: eitc x standards_of_living -6.8 (-3.4 SE); ubs x full_transformation -6.4 (-3.2 SE).
- D2: ubi x mild_disruption +10.6 (14.0 SE); ubs x economic_feasibility +9.1 (12.0 SE); fjg x economic_feasibility +7.6 (10.1 SE); ubi x macro_stabilisation +7.0 (9.3 SE); ubi x economic_feasibility +6.8 (9.1 SE); fjg x standards_of_living +6.7 (8.9 SE); ubi x meaning_human_value +6.7 (8.9 SE); fjg x mild_disruption +6.2 (8.3 SE); sawf x macro_stabilisation +5.4 (7.1 SE); sawf x moderate_disruption -5.3 (-7.1 SE); eitc x meaning_human_value -5.1 (-6.8 SE); sawf x implementation_readiness +5.0 (6.6 SE).

## Added criteria (descriptive, not in the primary count), M = 5

Political Support and Administrative Capacity and Speed are not Table 4 columns (prereg s10, 2026-10-04): counted here separately and never added to the primary count above.

| Cell | units | beyond M = 5 | beyond 3 | beyond 8 |
|---|---|---|---|---|
| B' | 22 | 0 | 1 | 0 |
| Q1 | 22 | 1 | 8 | 1 |
| Q4 | 22 | 4 | 7 | 2 |
| Q3c | 22 | 1 | 5 | 0 |
| D2 | 22 | 0 | 3 | 0 |

## How to read this

- A cell without personas (D2) makes one call per policy and repeat, so a failed call drops only that repeat x policy: its means average the surviving repeats per policy, and its single runs, repeat-noise SE and variance components use only the repeats with no failed call (TASK-37, prereg s13).
- Every cell and every policy x criterion is reported; the CSV files hold all shifts. Holm correction applies to the primary set only if inference language is used (prereg s6).
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong.
- Noise column: 'own' when the cell has two or more repeats; 'B' when a one-repeat cell borrows B's noise (assumes equal noise).
- D2 (no persona) and D2b (another panel) are not paired with B's personas; their shifts mix the factor with who rates. Block D cells are read separately from blocks R and Q (prereg s5).
