# TODOs and blockers

Collected during the unattended run of tasks 1-10. None blocked progress.

- **Prereg TODOs** (`prereg/prereg.md`): factor levels, thresholds, aggregation/order levels,
  fraction size, adversarial-arm procedure. Decide before tagging it frozen.
- **TASK-9 AC5 discrepancy**: "about 8,400 calls at baseline" holds only for one-policy-per-call
  mode. In the paper format (11 policies in one prompt) the baseline is 765 calls yielding
  8,415 ratings. `plan` reports both. Confirm which was intended.
- **Fractional design** (TASK-8) is a seeded balanced greedy subset, not a generator-based regular
  fraction. Decide whether that is acceptable for the prereg.
- **Placeholder prompt template** (domain/rendering.py) and fake inputs (`designs/fake_inputs/`)
  stand in until TASK-14/15/16/17 reconstruct the real policies, criteria, personas, prompts.
- **Prices and snapshots**: `config.yaml` has fake-model prices only. Real pinned snapshots and
  prices are needed at TASK-11 (and user confirmation before the first paid call per provider).
  There is no code check yet that a snapshot is a pinned version rather than an alias.
- **Cost estimate assumptions**: no batch discount assumed (conservative); output tokens estimated
  at 100 per policy; chars/4 for input tokens. Revisit after the pilot (TASK-12) with real usage.
- **Store**: JSONL only (no Parquet yet); `exists()` caches an index and assumes one writer.
- `results/raw/` is tracked in git. Decide whether raw results get committed or ignored once real
  runs start (size, and any provider terms on redistributing outputs).
