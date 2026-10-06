# ADVERSARIAL ARM — not pooled with the main analysis

This is the adversarial arm (prereg s9). It searches on purpose for the smallest change that moves the top policy to the bottom of the ranking. It is a worst-case search, not an estimate of how stable the rankings are, and none of it enters the main analysis. Instability of scores shows they lack the claimed precision, not that the recommendations are wrong.

- Store: `adversarial/results/rows.jsonl` (the arm's own store; never `results/raw`).
- Catalogue `adv-catalogue-v1` (14 entries); caps: depth 2, 30 candidates; spend ceiling $2.50 for this ledger, inside the global $15.
- Search panel: 5 personas of `named` drawn with seed 20261004; one run per candidate at seed 0; model `glm-5.3-flash`; primary composite `full_transformation`.
- Status: **depth exhausted**
- Target policy: `ubi` (first in the search-panel baseline: target rank 1.0 of 11, panel mean 59.4 (5 personas)).
- Baseline rerun at seed 1 (repeat-noise reference): target rank 2.0 of 11, panel mean 60.2 (5 personas).
- Candidates tried: **27**. This is the multiple-comparisons denominator: a winner is the most extreme of these single runs, so part of its movement can be repeat noise.
- Greedy path: `w_higher_better`, `w_higher_better+p_drop_top`.
- No candidate moved the target from top to bottom.

## Every candidate tried

| # | Depth | Candidate | Change | Target rank | Drop | Top to bottom | Edits | Chars | Prompts | Failed jobs |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | `w_household` | "a household-facing economic policy" -> "a household-level economic policy" | 2.0 | 1.0 | no | 1 | 6 | 55 | 0 |
| 2 | 1 | `w_could_help` | "that could help the United States" -> "that might help the United States" | 2.0 | 1.0 | no | 1 | 5 | 55 | 0 |
| 3 | 1 | `w_agi` | "artificial general intelligence (AGI)." -> "artificial general intelligence." | 2.0 | 1.0 | no | 1 | 6 | 55 | 0 |
| 4 | 1 | `w_higher_better` | "does better on that criterion" -> "performs better on that criterion" | 3.0 | 2.0 | no | 1 | 7 | 55 | 0 |
| 5 | 1 | `w_rationale` | "Give a one-sentence rationale" -> "Give a brief rationale" | 1.0 | 0.0 | no | 1 | 12 | 55 | 0 |
| 6 | 1 | `e_drop_last` | target packet: drop the last excerpt | 3.0 | 2.0 | no | 1 | 196 | 5 | 0 |
| 7 | 1 | `e_drop_first` | target packet: drop the first excerpt | 2.0 | 1.0 | no | 1 | 608 | 5 | 0 |
| 8 | 1 | `e_reverse` | target packet: excerpts in reverse order | 3.0 | 2.0 | no | 1 | 4608 | 5 | 0 |
| 9 | 1 | `e_keep_first_half` | target packet: keep the first half of the excerpts (rounded up) | 1.0 | 0.0 | no | 1 | 1867 | 5 | 0 |
| 10 | 1 | `p_drop_top` | drop the search-panel persona most favourable to the target | 2.0 | 1.0 | no | 1 | 0 | 0 | 0 |
| 11 | 1 | `t_0` | temperature 0 | 2.0 | 1.0 | no | 1 | 0 | 0 | 0 |
| 12 | 1 | `t_1` | temperature 1 | 2.0 | 1.0 | no | 1 | 0 | 0 | 1 |
| 13 | 1 | `c_reverse` | criteria in reverse order | 1.0 | 0.0 | no | 1 | 2852 | 55 | 0 |
| 14 | 1 | `c_primary_first` | primary composite's criteria listed first | 1.0 | 0.0 | no | 1 | 2852 | 55 | 0 |
| 15 | 2 | `w_higher_better+w_household` | "does better on that criterion" -> "performs better on that criterion"; "a household-facing economic policy" -> "a household-level economic policy" | 1.0 | 0.0 | no | 2 | 13 | 55 | 0 |
| 16 | 2 | `w_higher_better+w_could_help` | "does better on that criterion" -> "performs better on that criterion"; "that could help the United States" -> "that might help the United States" | 2.0 | 1.0 | no | 2 | 12 | 55 | 0 |
| 17 | 2 | `w_higher_better+w_agi` | "does better on that criterion" -> "performs better on that criterion"; "artificial general intelligence (AGI)." -> "artificial general intelligence." | 2.0 | 1.0 | no | 2 | 13 | 55 | 0 |
| 18 | 2 | `w_higher_better+w_rationale` | "does better on that criterion" -> "performs better on that criterion"; "Give a one-sentence rationale" -> "Give a brief rationale" | 1.0 | 0.0 | no | 2 | 19 | 55 | 0 |
| 19 | 2 | `w_higher_better+e_drop_last` | "does better on that criterion" -> "performs better on that criterion"; target packet: drop the last excerpt | 3.0 | 2.0 | no | 2 | 203 | 55 | 0 |
| 20 | 2 | `w_higher_better+e_drop_first` | "does better on that criterion" -> "performs better on that criterion"; target packet: drop the first excerpt | 1.0 | 0.0 | no | 2 | 615 | 55 | 0 |
| 21 | 2 | `w_higher_better+e_reverse` | "does better on that criterion" -> "performs better on that criterion"; target packet: excerpts in reverse order | 3.0 | 2.0 | no | 2 | 4615 | 55 | 0 |
| 22 | 2 | `w_higher_better+e_keep_first_half` | "does better on that criterion" -> "performs better on that criterion"; target packet: keep the first half of the excerpts (rounded up) | 3.0 | 2.0 | no | 2 | 1874 | 55 | 0 |
| 23 | 2 | `w_higher_better+p_drop_top` | "does better on that criterion" -> "performs better on that criterion"; drop the search-panel persona most favourable to the target | 3.0 | 2.0 | no | 2 | 7 | 55 | 0 |
| 24 | 2 | `w_higher_better+t_0` | "does better on that criterion" -> "performs better on that criterion"; temperature 0 | 1.0 | 0.0 | no | 2 | 7 | 55 | 0 |
| 25 | 2 | `w_higher_better+t_1` | "does better on that criterion" -> "performs better on that criterion"; temperature 1 | 2.0 | 1.0 | no | 2 | 7 | 55 | 0 |
| 26 | 2 | `w_higher_better+c_reverse` | "does better on that criterion" -> "performs better on that criterion"; criteria in reverse order | 1.0 | 0.0 | no | 2 | 2859 | 55 | 0 |
| 27 | 2 | `w_higher_better+c_primary_first` | "does better on that criterion" -> "performs better on that criterion"; primary composite's criteria listed first | 1.0 | 0.0 | no | 2 | 2859 | 55 | 0 |

Edit size is compared in order: perturbations, then the largest number of characters changed in one prompt, then prompts changed. Temperature and the persona drop change no characters; weigh them as you see fit.
