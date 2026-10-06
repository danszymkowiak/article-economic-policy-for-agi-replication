# Recommendation robustness

- Store: `results/raw/rows.jsonl`.

## Data

| Cell | ok jobs | not ok | deferred | duplicate rows | repeats | pairing with B |
|---|---|---|---|---|---|---|
| B | 2803 | 2 (failed 2) | 0 | 0 | 5 | (reference) |
| B' | 561 | 0 (failed 0) | 0 | 0 | 1 | paired |
| Q1 | 1683 | 0 (failed 0) | 0 | 0 | 3 | paired |
| Q4 | 1683 | 0 (failed 0) | 0 | 0 | 3 | paired |
| Q3c | 100 | 0 (failed 0) | 0 | 0 | 1 | paired |
| D2 | 555 | 6 (failed 6) | 0 | 0 | 51 | no personas |

_Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes)._

## Clauses (prereg s6)

- (a) UBC rank 1 on Full Transformation durability
- (b) UBC rank 1 on Ownership of Gains
- (c) NIT in the top 3 on Moderate durability
- (d) UI and EITC in the top 4 on Mild, both below UBC on Full Transformation
- three-stage sequence UI/EITC -> NIT -> UBC: (a), (c) and (d) all hold

Margin: the policy's score minus the k-th best score among the other policies (rank-1 clauses: the gap to the runner-up), so a clause holds exactly when its margin is positive; a tie at the cut-off does not hold. (d) and the sequence take the smallest margin of their parts. Published Table 4 margins: (a) 15.5, (b) 40.0, (c) 3.9 (NIT 69.8 minus UI 65.9 at rank 4; prereg s6, s10), (d) 5.9.

The paper's Mild recommendation also names employer-led retraining, but ALMP scores 42.5 on Mild in Table 4, so it is excluded from the clauses (prereg s6); its Mild rank is reported under score consistency.

## Three-stage sequence per configuration

Repeat mean: holds (margin, versus B's repeat mean); single runs: how many hold, how many flip against B, and the range of their margins.

| Cell | repeat mean | flipped vs B | runs holding | runs flipped | single-run margins |
|---|---|---|---|---|---|
| B | no (-12.5) | (reference) | 0/5 | 0/5 | -14.8 to -10.6 |
| B' | no (-15.3) | no | 0/1 | 0/1 | -15.3 to -15.3 |
| Q1 | no (-14.4) | no | 0/3 | 0/3 | -16.4 to -10.9 |
| Q4 | no (-13.4) | no | 0/3 | 0/3 | -14.6 to -12.7 |
| Q3c | no (-12.7) | no | 0/1 | 0/1 | -12.7 to -12.7 |
| D2 | no (-11.9) | no | 0/45 | 0/45 | -38.0 to -3.0 |

- Across all cells other than B: the sequence holds in the repeat mean of 0 of 5 cells; repeat-mean margin min / median / max -15.3 / -13.4 / -11.9 (n=5); single runs flipped 0 of 53.
- Noise floor, B's single runs against B's repeat mean: 0 of 5 flipped.

## Clause flips

Each entry: repeat mean holds (margin, FLIP or same against B); single runs flipped.

| Cell | (a) | (b) | (c) | (d) |
|---|---|---|---|---|
| B | yes (3.1); runs flipped 1/5 | yes (3.0); runs flipped 0/5 | no (-12.5); runs flipped 0/5 | yes (6.3); runs flipped 0/5 |
| B' | yes (7.2, same); runs flipped 0/1 | yes (2.5, same); runs flipped 0/1 | no (-15.3, same); runs flipped 0/1 | yes (7.5, same); runs flipped 0/1 |
| Q1 | no (-3.0, FLIP); runs flipped 3/3 | yes (0.2, same); runs flipped 0/3 | no (-14.4, same); runs flipped 0/3 | yes (5.1, same); runs flipped 0/3 |
| Q4 | yes (5.4, same); runs flipped 0/3 | yes (4.6, same); runs flipped 0/3 | no (-13.4, same); runs flipped 0/3 | yes (6.0, same); runs flipped 0/3 |
| Q3c | yes (1.7, same); runs flipped 0/1 | yes (2.2, same); runs flipped 0/1 | no (-12.7, same); runs flipped 0/1 | yes (7.1, same); runs flipped 0/1 |
| D2 | yes (6.0, same); runs flipped 18/45 | yes (3.3, same); runs flipped 6/45 | no (-11.9, same); runs flipped 3/45 | yes (2.8, same); runs flipped 26/45 |

Repeat-mean margin across all cells other than B, min / median / max:

- (a): -3.0 / 5.4 / 7.2 (n=5)
- (b): 0.2 / 2.5 / 4.6 (n=5)
- (c): -15.3 / -13.4 / -11.9 (n=5)
- (d): 2.8 / 6.0 / 7.5 (n=5)
- sequence: -15.3 / -13.4 / -11.9 (n=5)

Repeat-noise reference: share of splits of B's repeats where a k-repeat mean and the mean of the remaining repeats disagree on the clause (descriptive, not a test).

| k | splits | (a) | (b) | (c) | (d) | sequence |
|---|---|---|---|---|---|---|
| 1 | 5 | 0.20 | 0.00 | 0.00 | 0.00 | 0.00 |
| 3 | 10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Do the recommendations follow from the scores?

Repeat mean per cell. Leaders: the top-scoring policy on each durability composite. Stage follows: the stage's sole leader is the policy the paper recommends there (Mild: UI or EITC; Moderate: NIT; Full: UBC). Outside the sequence: leaders that are not UI, EITC, NIT or UBC. In published Table 4 the Mild leader is NIT and the Moderate and Scenario Durability leader is UBS, so the paper's own scores do not single out its Mild and Moderate picks either; UBS leads on durability yet is absent from the sequence.

| Cell | leaders mild / moderate / full / scenario | stage follows (mild, moderate, full) | outside the sequence | UBS ranks (mild, moderate, full, scenario) | UBS leads (runs) |
|---|---|---|---|---|---|
| B | ui / ubc / ubc / ubc | yes, no, yes | none | 8.0, 4.0, 4.0, 4.0 | no (0/5) |
| B' | ui / ubc / ubc / ubc | yes, no, yes | none | 8.0, 4.0, 4.0, 4.0 | no (0/1) |
| Q1 | ui / ubi / ubi / ubi | yes, no, no | ubi | 5.0, 2.0, 4.0, 3.0 | no (0/3) |
| Q4 | nit / ubi / ubc / ubc | no, no, yes | ubi | 6.0, 4.0, 4.0, 4.0 | no (0/3) |
| Q3c | ui / ubc / ubc / ubc | yes, no, yes | none | 8.0, 4.0, 4.0, 4.0 | no (0/1) |
| D2 | ui / ubi / ubc / ubi | yes, no, yes | ubi | 8.0, 3.0, 4.0, 4.0 | no (6/45) |

NIT is recommended for Moderate (clause c) although the paper reports low public support for it (net approval +17.1). Political support below, as rated by the panel (rank 1 = highest).

| Cell | NIT political support (rank of n) | low | clause (c) | recommended despite low support (runs) | ALMP Mild rank |
|---|---|---|---|---|---|
| B | 61.8 (7.0 of 11) | yes | no | no (0/5) | 5.0 |
| B' | 60.6 (7.0 of 11) | yes | no | no (0/1) | 5.0 |
| Q1 | 49.6 (8.0 of 11) | yes | no | no (0/3) | 7.0 |
| Q4 | 55.6 (6.0 of 11) | no | no | no (0/3) | 5.0 |
| Q3c | 58.1 (7.0 of 11) | yes | no | no (0/1) | 5.0 |
| D2 | 60.3 (7.0 of 11) | yes | no | no (2/45) | 5.0 |

## Blinding policy names: UBC versus Sovereign AI Fund on Ownership of Gains

Gap = UBC minus Sovereign AI Fund / Dividend (SAWF) on Ownership of Gains (published 94.9 - 54.9 = 40.0). Q1 removes the policy names (description only). Shifts of a single policy are set against the materiality margin M = 5.0 points (prereg s6).

- B: gap 3.0 (repeat mean on the shared set); single runs 2.1 to 3.7.
- Q1: gap 0.2; single runs 0.0 to 0.3.
- Change in the gap: -2.8 points. UBC moves -1.8 (within M), SAWF 1.0 (within M).
- Repeat-noise reference for the change (k = 3-repeat mean of B minus the rest, over every split): -1.0 to 0.9.
- Clause (b) in Q1: yes (margin 0.2); same against B; single runs flipped 0/3.

The same gap in every cell (whole range):

| Cell | gap mean | change vs B | single-run gaps | UBC | SAWF |
|---|---|---|---|---|---|
| B | 3.0 | (reference) | 2.1 to 3.7 | 90.1 | 87.1 |
| B' | 2.5 | -0.5 | 2.5 to 2.5 | 90.1 | 87.6 |
| Q1 | 0.2 | -2.8 | 0.0 to 0.3 | 88.2 | 88.1 |
| Q4 | 4.6 | 1.6 | 3.8 to 5.4 | 89.6 | 85.0 |
| Q3c | 2.2 | -0.6 | 2.2 to 2.2 | 89.1 | 86.9 |
| D2 | 3.3 | 0.3 | -1.0 to 8.0 | 91.6 | 88.3 |

- Gap change across all cells other than B, min / median / max: -2.8 / -0.5 / 1.6 (n=5).

## Correlations with Full Transformation durability

The paper reports r(public net approval, Full Transformation) = -0.57 (recomputed -0.569 from Table 4) and r(Readiness, Full Transformation) = -0.51. Net approval is the paper's fixed survey input.

| Cell | r(approval, Full) mean (single runs) | r(Readiness, Full) mean (single runs) |
|---|---|---|
| B | -0.70 (-0.71 to -0.69) | -0.54 (-0.56 to -0.50) |
| B' | -0.68 (-0.68 to -0.68) | -0.52 (-0.52 to -0.52) |
| Q1 | -0.64 (-0.64 to -0.64) | -0.58 (-0.61 to -0.54) |
| Q4 | -0.70 (-0.71 to -0.70) | -0.60 (-0.60 to -0.60) |
| Q3c | -0.70 (-0.70 to -0.70) | -0.60 (-0.60 to -0.60) |
| D2 | -0.68 (-0.81 to -0.50) | -0.55 (-0.71 to -0.30) |

## How to read this

- Descriptive and unthresholded (prereg s6). Every cell is reported, with ranges across all cells, not only the largest change; the CSV files hold every run.
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong. A clause that flips says the scores cannot carry that rank claim at their stated precision; it does not say the policy advice is mistaken.
- The clauses are the paper's own claims with cut-offs from Table 4, which passes all four, so B is not a test of the paper.
- Flips are counted against B's repeat mean on the persona x policy x criterion set the two cells share (prereg s7). B's own row is the noise floor: its single runs against its mean. The k-split reference compares a k-repeat mean of B with the rest; it is descriptive, not a test (the splits overlap).
- The score-consistency checks (leaders, UBS, NIT's political support, ALMP) are not in prereg s6 and are exploratory. 'Low' political support means a rank below the median policy (our reading; the paper gives no cut-off). Political Support is our rating; the paper does not publish it per policy.
- Tier changes are not a metric: the paper defines no usable tiers for the Table 4 composites, so the tier-change metric was dropped before the freeze (prereg s6, s10).
- Block D cells change the design, not a small detail, and are read separately from blocks R and Q (prereg s5).
- A cell without personas (D2) makes one call per policy and repeat, so a failed call drops only that repeat x policy: its means average the surviving repeats per policy, and its single runs, repeat-noise SE and variance components use only the repeats with no failed call (TASK-37, prereg s13).
