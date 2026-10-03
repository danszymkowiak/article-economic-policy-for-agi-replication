# TODOs and blockers

Tasks 1-10 close-out (2026-10-03). Nothing here blocks tasks 11+. Open items now live on the
tasks that own them (see `backlog task view <id>`, Implementation Notes).

## Resolved
- TASK-9 AC5: paper format is the baseline (765 calls, 8,415 ratings). AC and prereg reworded.
- Fractional design: the seeded balanced greedy subset is accepted and documented in
  `prereg/prereg.md` section 4 as the preregistered procedure.
- `results/raw/*` is gitignored (`.gitkeep` kept). Redistribution is decided at write-up.
- Spend/retry fixes from the independent review (attempt count from the store, intent records,
  idempotent re-collect, file lock, deferred status, torn-write tail not swallowing records).

## Carried to later tasks
- TASK-11: real snapshots and prices, alias-vs-pinned check, `max_tokens` cap, cached/reasoning
  token pricing, ambiguous-submit reconciliation, confirm before first paid call per provider.
- TASK-12: re-estimate cost from real usage, optional 0.9x ceiling margin, torn final line
  repair (needs approval), Parquet only if needed, single-writer `exists()` assumption.
- TASK-14 to 17: replace the placeholder template and fake inputs.
- TASK-19 to 21: analysis counts only `ok` rows; `deferred`, `duplicate`, `failed` handled explicitly.
- TASK-22/23: remaining prereg `TODO`s (levels, thresholds, run count and seed, adversarial
  procedure) must be decided before tagging the prereg frozen.
