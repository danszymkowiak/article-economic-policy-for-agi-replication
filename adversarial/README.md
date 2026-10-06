# ADVERSARIAL ARM (not pooled with the main analysis)

This directory holds the adversarial arm of the LLM-panel sensitivity study (prereg section 9,
TASK-22). It looks, on purpose, for the **smallest plausible change that moves a policy from the
top of the ranking to the bottom**. It is a worst-case search, not an estimate of how stable
the rankings are. Its data, numbers and report are kept apart from the main analysis and are
not pooled with it. Instability of scores shows they lack the claimed precision, not that the
recommendations are wrong.

## Procedure (pre-specified, bounded)

- **Catalogue** `adv-catalogue-v1` (`catalogue.py`), fixed before any adversarial data: five
  meaning-preserving one-sentence wording edits of the study template, four edits of the target
  policy's evidence packet (drop the last or first excerpt, reverse the excerpts, keep the first
  half), dropping the search-panel persona most favourable to the target, temperature 0 or 1,
  and two criterion orders (reversed, primary composite first). Changing an entry means a new
  catalogue version.
- **Search panel**: 5 of the 51 named personas, drawn with a recorded seed; every policy; the
  study's persona x policy prompt; one run per candidate (seed 0). A baseline rerun at seed 1 is
  the repeat-noise reference for the target's rank.
- **Target**: the policy ranked first on the primary composite (Full Transformation durability,
  clause (a)) in the search-panel baseline.
- **Greedy search** (`search.py`): depth 1 tries every catalogue entry alone. If any moves the
  target to strictly last place, the smallest of those wins. Otherwise the entry with the
  largest rank drop is kept, and depth 2 tries it combined with every entry of another slot.
  The search stops at the first depth with a success, when no entry lowers the target, at depth
  2, at 30 candidates, or when the budget runs out.
- **Smallest** means the lowest edit size, compared in this order: number of perturbations; the
  most characters changed in any one rendered prompt; number of prompts changed.
- **Every candidate tried is logged and reported**, not only the winner. Their number is the
  multiple-comparisons denominator.

## Budget and data

`config.adversarial.yaml` sets the arm's own ceiling (2.50 USD, raised from 1.50 by the user on
2026-10-04; prereg s10), store and ledger (`adversarial/results/`, gitignored), and counts every root config's ledger toward the global
15 USD hard cap. Every root config counts this ledger too. Submission goes through the study's
guards: `--confirm`, approved providers, model-id drift, and both ceilings. Candidates are
sent whole, in search order. One that does not fit waits, and no cheaper later candidate goes
ahead of it, until collected spend frees room. When nothing fits and nothing is in flight, the
search stops as `budget exhausted`.

## Running (done; results in `report.md` and `candidates.csv`)

```bash
uv run python -m adversarial plan               # search state, next candidates, estimate; read-only
uv run python -m adversarial submit --confirm   # send what the search needs next (spends money)
uv run python -m adversarial collect            # validate, store, retry malformed once
uv run python -m adversarial report             # adversarial/report.md and candidates.csv
```

Run `collect` then `submit --confirm` repeatedly (cron-friendly) until the status is no longer
`running`. Paid runs need the provider in `approved_providers`.
