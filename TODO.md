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

## From the independent review of the spend/retry code (fixed in the follow-up commit)

Fixed: attempt number now derived from the store (retry-once survives crashes and failed retry
submits); jobs with no reported usage are charged at the estimate; submits record an intent before
calling the provider so a crash mid-submit shows up as outstanding spend; re-collect is idempotent
per (job, batch); estimate settings validated; submit/collect take an exclusive file lock;
torn-write tail no longer swallows the next record; ceiling-blocked retries are `deferred`
(non-terminal) rather than `failed`.

Still open:
- **Cap `max_tokens` in each real client** (TASK-11) so the output estimate is a true upper bound;
  cached/reasoning tokens reported separately by a provider are not yet priced.
- A torn final line still makes reads raise until that one line is removed by hand.
- A provider call that errors *ambiguously* (timeout after the batch was actually created) is
  recorded as `submit_failed` and could be paid twice. Reconcile manually against the provider
  console if a timeout happens.
- Analysis must treat `deferred`, `duplicate` and `failed` rows explicitly (budget-censored vs
  model failures) and count only `ok` rows as ratings.
- Optional safety margin on the ceiling (e.g. 0.9x) if estimates prove optimistic in the pilot.
