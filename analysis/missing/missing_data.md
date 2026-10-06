# Missing-data sensitivity

- Store: `results/raw/rows.jsonl`.

## Failures

A cell with failures above 10% of its attempted calls is flagged (prereg s7) and still analysed on the common-complete set.

| Cell | ok jobs | not ok | deferred | duplicate rows | failure rate | flag |
|---|---|---|---|---|---|---|
| B | 2803 | 2 (failed 2) | 0 | 0 | 0.1% |  |
| B' | 561 | 0 (failed 0) | 0 | 0 | 0.0% |  |
| Q1 | 1683 | 0 (failed 0) | 0 | 0 | 0.0% |  |
| Q4 | 1683 | 0 (failed 0) | 0 | 0 | 0.0% |  |
| Q3c | 100 | 0 (failed 0) | 0 | 0 | 0.0% |  |
| D2 | 555 | 6 (failed 6) | 0 | 0 | 1.1% |  |

_Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes)._

## Views

- Common-complete (primary): the materiality count and the clauses exactly as in the materiality and recommendations reports.
- Survivor-only (secondary): every valid rating, no common-complete filter and no pairing with B; a unit's mean is the panel mean per repeat over the personas present, then the mean over the repeats present.
- Worst-case bound: every failed call's ratings imputed at 0, and separately imputed at 100, then averaged as survivor-only (B under the same imputation).
- Beyond M: Table 4 policy x criterion means whose |shift from B| exceeds M = 5. Clauses: on the cell's own repeat mean (B's row gives B's own result).

| Cell | view | units | beyond M = 5 | max abs shift | (a) | (b) | (c) | (d) | sequence |
|---|---|---|---|---|---|---|---|---|---|
| B | common-complete (primary) | 121 | 0 | 0.0 | holds | holds | fails | holds | fails |
| B | survivor-only | 121 | 0 | 0.0 | holds | holds | fails | holds | fails |
| B | failures imputed at 0 | 121 | 0 | 0.0 | holds | holds | fails | holds | fails |
| B | failures imputed at 100 | 121 | 0 | 0.0 | holds | holds | fails | holds | fails |
| B' | common-complete (primary) | 121 | 0 | 2.9 | holds | holds | fails | holds | fails |
| B' | survivor-only | 121 | 0 | 2.9 | holds | holds | fails | holds | fails |
| B' | failures imputed at 0 | 121 | 0 | 2.9 | holds | holds | fails | holds | fails |
| B' | failures imputed at 100 | 121 | 0 | 2.9 | holds | holds | fails | holds | fails |
| Q1 | common-complete (primary) | 121 | 15 | 14.5 | fails | holds | fails | holds | fails |
| Q1 | survivor-only | 121 | 15 | 14.5 | fails | holds | fails | holds | fails |
| Q1 | failures imputed at 0 | 121 | 16 | 14.5 | fails | holds | fails | holds | fails |
| Q1 | failures imputed at 100 | 121 | 15 | 14.5 | fails | holds | fails | holds | fails |
| Q4 | common-complete (primary) | 121 | 19 | 8.9 | holds | holds | fails | holds | fails |
| Q4 | survivor-only | 121 | 19 | 8.9 | holds | holds | fails | holds | fails |
| Q4 | failures imputed at 0 | 121 | 18 | 8.9 | holds | holds | fails | holds | fails |
| Q4 | failures imputed at 100 | 121 | 18 | 8.9 | holds | holds | fails | holds | fails |
| Q3c | common-complete (primary) | 121 | 2 | 6.8 | holds | holds | fails | holds | fails |
| Q3c | survivor-only | 121 | 4 | 5.6 | holds | holds | fails | holds | fails |
| Q3c | failures imputed at 0 | 121 | 3 | 5.6 | holds | holds | fails | holds | fails |
| Q3c | failures imputed at 100 | 121 | 4 | 5.7 | holds | holds | fails | holds | fails |
| D2 | common-complete (primary) | 121 | 12 | 10.6 | holds | holds | fails | holds | fails |
| D2 | survivor-only | 121 | 12 | 10.6 | holds | holds | fails | holds | fails |
| D2 | failures imputed at 0 | 121 | 8 | 9.1 | holds | holds | fails | holds | fails |
| D2 | failures imputed at 100 | 121 | 15 | 12.2 | holds | holds | fails | holds | fails |

Clauses:

- (a) UBC rank 1 on Full Transformation durability
- (b) UBC rank 1 on Ownership of Gains
- (c) NIT in the top 3 on Moderate durability
- (d) UI and EITC in the top 4 on Mild, both below UBC on Full Transformation
- three-stage sequence UI/EITC -> NIT -> UBC: (a), (c) and (d) all hold

## How to read this

- The imputations are bounds, not estimates: a failed call is unlikely to have given 0 or 100 on every criterion, and imputing every failure at one extreme is not the most adverse case for a count or a clause. Where a result is the same under every view, it survives these two imputations.
- B's failures are imputed too, so a cell with no failures of its own can still move under imputation; survivor-only drops the pairing with B, so a partial cell (Q3c) can differ from its common-complete count.
- In a cell without personas (D2) a failed call drops only that repeat x policy (TASK-37, prereg s13), so its common-complete and survivor-only means coincide.
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong.
