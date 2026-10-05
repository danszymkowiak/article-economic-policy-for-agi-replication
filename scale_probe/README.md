# EXPLORATORY: reversed-scale probe (not pooled with the main analysis)

A small, separate probe (TASK-38; prereg s13, post-freeze, written before any probe data). It asks
the study model to rate each policy from 0 to 100 where **0 is best and 100 is worst**, and checks
whether the scores come back as the mirror image of the normal scale. It is not part of the
preregistered analysis and not part of the adversarial arm, and its numbers are never pooled with
either.

## Design

- **Prompt**: B's persona x policy template with one sentence changed
  (`prompts/reversed_scale.txt`, hash in `manifest.yaml`; a test rebuilds it from the baseline).
- **Panel and settings**: the adversarial arm's baseline run exactly (its 5-persona search panel,
  every policy, its seed, model and max_tokens cap), so the scale sentence is the only change.
  55 calls.
- **Comparison**: raw scores converted with 100 - x, against the arm's baseline run; the arm's
  baseline rerun (another seed) is the repeat-noise reference. Both are read from
  `adversarial/results/` read-only.
- **Measures** (fixed before data, `analysis.py`): agreement of single ratings and panel means
  (r, mean signed and absolute difference), Table 4 units beyond M = 5, Kendall tau per composite,
  the target's rank, clauses (a)-(d), and a per-call "looks unconverted" rule; each also for the
  rerun, and again without unconverted calls.

## Budget and data

Own store, ledger and ceiling (`config.scale_probe.yaml`, 0.30 USD) under `scale_probe/results/`
(gitignored). Its ledger counts toward the global 15 USD cap from every root config and the
adversarial config, and it counts theirs.

```bash
uv run python -m scale_probe plan              # status and estimate; read-only
uv run python -m scale_probe submit --confirm  # spends money
uv run python -m scale_probe collect
uv run python -m scale_probe report            # scale_probe/report.md
```
