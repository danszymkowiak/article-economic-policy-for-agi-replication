# Variance decomposition

- Store: `results/raw/rows.jsonl`.

## Data

| Cell | ok jobs | not ok | deferred | duplicate rows | repeats | personas used | personas dropped | criteria |
|---|---|---|---|---|---|---|---|---|
| B | 2803 | 2 (failed 2) | 0 | 0 | 5 | 49 | 2 | 13 |
| B' | 561 | 0 (failed 0) | 0 | 0 | 1 | 51 | 0 | 13 |
| Q1 | 1683 | 0 (failed 0) | 0 | 0 | 3 | 51 | 0 | 13 |
| Q4 | 1683 | 0 (failed 0) | 0 | 0 | 3 | 51 | 0 | 13 |
| Q3c | 100 | 0 (failed 0) | 0 | 0 | 1 | 9 | 1 | 13 |
| D2 | 555 | 6 (failed 6) | 0 | 0 | 45 | 0 | 0 | 13 |

_Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes)._

Personas enter the within-cell decomposition only when complete in every rated policy x criterion and repeat (a balanced design); the per policy x criterion and per criterion analyses use every persona complete there.

## What the design can and cannot identify

- **Identifiable within a cell** (fully crossed persona x policy x criterion x repeat): every main effect and interaction of those four factors, except that the top interaction is confounded with residual error. With one repeat, repeat noise is not separable at all: the persona x policy x criterion term then holds it, and the report flags this.
- **Identifiable per varied factor**: the cell's level shift and its policy x criterion specific shift against B, each beyond the repeat noise measured in B (and in the cell when it has two or more repeats). This is a contrast between two configurations, not a variance over a population of prompts, models or evidence packets: each factor has one alternative level (Q2 and Q3 three paraphrases), so a factor variance component is not identifiable.
- **Not identifiable**: any interaction between varied factors (e.g. model x evidence, wording x temperature): the design is one-at-a-time, never factorial, so no two factors are changed together. The shift of a cell is the whole effect of its one change under B's other settings; it may differ under other settings. Persona x factor interactions are estimable in principle for paired cells but are not estimated here (shifts are at panel-mean level).
- D2 (no persona) and D2b (another panel) are not paired with B's personas; their shifts compare panel means of different raters and mix the factor with who rates.

## Within-cell decomposition, baseline B

Method-of-moments components of a balanced crossed random-effects ANOVA. Negative raw estimates are shown and count as 0 in shares.

| Term | df | mean square | component | share |
|---|---|---|---|---|
| repeat | 4 | 42.86 | -0.01 | 0.0% |
| criterion | 12 | 376964.19 | 117.71 | 27.8% |
| policy | 10 | 145791.48 | 26.98 | 6.4% |
| persona | 48 | 758.35 | 0.79 | 0.2% |
| repeat x criterion | 48 | 36.88 | 0.02 | 0.0% |
| repeat x policy | 40 | 108.58 | 0.03 | 0.0% |
| repeat x persona | 192 | 99.91 | 0.07 | 0.0% |
| criterion x policy | 120 | 59711.08 | 243.58 | 57.6% |
| criterion x persona | 576 | 52.64 | 0.33 | 0.1% |
| policy x persona | 480 | 167.76 | 1.10 | 0.3% |
| repeat x criterion x policy | 480 | 25.70 | -0.00 | 0.0% |
| repeat x criterion x persona | 2304 | 27.42 | 0.14 | 0.0% |
| repeat x policy x persona | 1920 | 88.89 | 4.84 | 1.1% |
| criterion x policy x persona | 5760 | 33.04 | 1.42 | 0.3% |
| repeat x criterion x policy x persona (with residual) | 23040 | 25.93 | 25.93 | 6.1% |

## How much variance persona explains

- In B, all persona terms without repeat (persona, persona x policy, persona x criterion, persona x policy x criterion) take **0.9%** of the variance of a single rating; the persona main effect alone 0.2%. Repeat noise (every term with repeat) takes 7.3%; the policy and criterion structure 91.8%.
- Per policy x criterion (persona x repeat decomposition), persona share sigma2_P / (sigma2_P + sigma2_run + sigma2_residual), min / median / max over cells: 0.0% / 9.0% / 49.6% (n=143).

| Cell | persona main | all persona terms | repeat noise | policy/criterion | per policy x criterion persona share (min / median / max) |
|---|---|---|---|---|---|
| B | 0.2% | 0.9% | 7.3% | 91.8% | 0.0% / 9.0% / 49.6% (n=143) |
| B' | 0.1% | 7.7% (noise confounded) | n/a | 92.3% | n/a |
| Q1 | 0.2% | 0.6% | 7.7% | 91.6% | 0.0% / 8.2% / 48.6% (n=143) |
| Q4 | 0.2% | 1.3% | 6.5% | 92.1% | 0.0% / 15.6% / 51.2% (n=143) |
| Q3c | 0.3% | 8.4% (noise confounded) | n/a | 91.6% | n/a |
| D2 | n/a | n/a | 5.7% | 94.3% | n/a |

## Precision of a panel mean (prereg H1)

- B, SD across its 5 runs of each Table 4 policy x criterion panel mean, min / median / max: 0.12 / 0.67 / 1.79 (n=121); range across runs (max - min), min / median / max: 0.29 / 1.69 / 4.84 (n=121).
- The paper prints panel means to one decimal, a precision of 0.05 points. Descriptive: H1 sets no threshold (prereg s14).

## Effective number of independent raters

Design-effect formula: **n_eff = n / (1 + (n - 1) icc)**, n = personas rated. Two readings of icc, both from the decompositions above; the run-shared one is primary and the agreement one secondary (prereg s6, s10):

- *Run-shared, PRIMARY* (per policy x criterion cell; persona x repeat decomposition): icc_run = sigma2_run / (sigma2_P + sigma2_run + sigma2_residual), the correlation of two personas' ratings within one run. Its complement is the persona share plus the persona-specific noise share. It needs two or more repeats.
- *Agreement, secondary* (per criterion; persona x policy x repeat decomposition): icc_agree = (sigma2_policy + sigma2_policy x run) / (that + sigma2_persona x policy + sigma2_residual), the correlation of two personas' single-run ratings across policies. Its complement is the persona x policy (persona-specific view) share plus noise; near 1 means the panel behaves as one model (prereg H4).

- B, run-shared n_eff over policy x criterion cells, min / median / max: 12.2 / 50.9 / 51.0 (n=143); icc_run 0.00 / 0.00 / 0.06 (n=143).

| Criterion (B) | personas | policies | icc_agree | persona x policy share | n_eff |
|---|---|---|---|---|---|
| standards_of_living | 49 | 11 | 0.90 | 1.1% | 1.1 |
| meaning_human_value | 49 | 11 | 0.70 | 4.5% | 1.4 |
| macro_stabilisation | 49 | 11 | 0.92 | 0.4% | 1.1 |
| economic_agency_mobility | 49 | 11 | 0.81 | 2.5% | 1.2 |
| ownership_of_gains | 49 | 11 | 0.98 | 0.1% | 1.0 |
| democratic_voice | 49 | 11 | 0.79 | 1.9% | 1.3 |
| economic_feasibility | 49 | 11 | 0.83 | 1.9% | 1.2 |
| implementation_readiness | 49 | 11 | 0.92 | 0.5% | 1.1 |
| mild_disruption | 49 | 11 | 0.71 | 3.9% | 1.4 |
| moderate_disruption | 49 | 11 | 0.79 | 0.7% | 1.3 |
| full_transformation | 49 | 11 | 0.90 | 0.6% | 1.1 |
| admin_capacity_speed | 49 | 11 | 0.85 | 0.4% | 1.2 |
| political_support | 49 | 11 | 0.86 | 0.8% | 1.2 |

- Agreement n_eff over criteria, min / median / max: 1.0 / 1.2 / 1.4 (n=13).

## Varied factors against repeat noise (one-at-a-time, versus B)

Units are policy x criterion panel means. Level shift: mean of cell - B, with its repeat-noise SE. Shift SD: SD of the unit-specific shift beyond repeat noise (0 when the estimate is negative). Ratio: that variance over B's single-run panel-mean noise variance (raw, may be negative); band: the same ratio over every split of B's repeats into the cell's repeat count and the rest (descriptive, not a test; n/a when the cell has as many repeats as B or more).

| Cell | factor | pairing | units | repeats | level shift (SE) | shift SD | ratio to noise | B split band | noise |
|---|---|---|---|---|---|---|---|---|---|
| B' | drift (B repeated at the end) | paired | 143 | 1 | 0.35 (0.09) | 0.58 | 0.56 | -0.36 to 0.30 | B |
| Q1 | policy identifier (name removed) | paired | 143 | 3 | 1.29 (0.05) | 3.58 | 21.05 | -0.16 to 0.23 | own |
| Q4 | evidence packet (none) | paired | 143 | 3 | -0.15 (0.05) | 3.47 | 19.71 | -0.16 to 0.23 | own |
| Q3c | instruction wording | paired | 143 | 1 | 0.23 (0.28) | 0.65 | 0.12 | -0.33 to 0.66 | B |
| D2 | persona (none) | no personas | 143 | 45 | 0.52 (0.12) | 2.68 | 11.75 | n/a | own |

## How to read this

- A cell without personas (D2) makes one call per policy and repeat, so a failed call drops only that repeat x policy: its means average the surviving repeats per policy, and its single runs, repeat-noise SE and variance components use only the repeats with no failed call (TASK-37, prereg s13).
- Descriptive and unthresholded (prereg s6: variance decomposition is a secondary descriptive). Every cell and every policy x criterion is reported; the CSV files hold the full tables.
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong.
- Policy and criterion are fixed in the design; their components are the variance of their effects (divisor n - 1), read descriptively. The 51 personas are the fixed inference target (prereg s3); the persona share describes how much they differ, not a sample of economists.
- Noise column: 'own' when the cell has two or more repeats; 'B' when a one-repeat cell borrows B's noise (assumes equal noise).
- Block D cells change the design, not a small detail, and are read separately from blocks R and Q (prereg s5).
