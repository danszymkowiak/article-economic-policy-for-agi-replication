# How stable are LLM-panel policy scores?

A preregistered sensitivity study of the simulated-economist panel in "Economic Policy for AGI"
(Jacobs and Imas, 2026). We rebuilt the panel from its public description, with 51 named economist
personas each scoring 11 redistributive policies, and measured how far its scores, ranks and
recommendations move when the same panel is rerun, and when one small input detail changes.

This is a **re-implementation, not a replication**. The authors' prompts, persona data and
literature text are not public, so ours are stand-ins and our absolute scores are not the paper's.
[`prereg/reconstruction.md`](prereg/reconstruction.md) lists every reconstruction choice.

**Status:** study complete. The write-up is a draft: [`writeup/draft.md`](writeup/draft.md).

## Findings in brief

- **Repeat noise is far above the paper's printed precision.** Across five identical runs, a
  policy x criterion panel mean has a median standard deviation of 0.67 points, against the
  one-decimal (0.05-point) precision of the published tables. Rankings stay largely stable.
- **Small input changes move scores beyond repeat noise.** Removing policy names moved 15 of 121
  panel means by more than 5 points, and removing the evidence packet moved 19. Repeats of the
  baseline moved none. Removing names also flipped the claim that UBC leads on Full
  Transformation durability.
- **The 51 personas behave almost as one rater.** The effective number of independent raters is
  1.0 to 1.4.
- **The recommendations held up better than the scores.** A bounded adversarial search found no
  small change that moved the top policy to the bottom.

Instability of the scores shows they lack the claimed precision. It does not show that the
paper's recommendations are wrong.

## What's here

| Path | Contents |
|---|---|
| [`writeup/draft.md`](writeup/draft.md) | The write-up: methods, the full range of results, limitations, related work |
| [`prereg/prereg.md`](prereg/prereg.md) | Preregistration, frozen at git tag `prereg-v1` (2026-10-04). Post-freeze changes are dated in section 13 |
| [`prereg/reconstruction.md`](prereg/reconstruction.md) | How each element of the paper was rebuilt, and which parts are stand-ins |
| `prereg/spec-v2-draft.md` | The earlier design spec and its red-team log (superseded by the prereg) |
| `analysis/` | Main-study reports (markdown and CSV) that the write-up cites. `analysis/published/` holds the paper's tables, transcribed |
| `adversarial/` | Adversarial arm: code, `README.md`, `report.md`. Separate and labeled, never pooled |
| `subagent_arm/` | Same baseline run on Claude Haiku 4.5 as Claude Code subagents. Separate, never pooled |
| `scale_probe/` | Exploratory reversed-scale probe (0 = best). Separate, never pooled |
| `designs/`, `prompts/` | Study designs, personas, policies, criteria and prompt templates, with hashes in `prompts/manifest.yaml` |
| `evidence/` | Evidence packets built from pinned English Wikipedia revisions (`raw/`, extraction passes, `packets/`) |
| `src/llm_panel/` | The pipeline |
| `tests/` | Test suite |
| [`docs/adding-a-provider.md`](docs/adding-a-provider.md) | How to add a model provider |

Code and prereg comments refer to internal task ids (`TASK-nn`). The tracker itself is not
published. The ids only link the code to the work item that produced it.

## Source paper

- Jacobs and Imas, "Economic Policy for AGI", SSRN abstract 7470000, 15 September 2026:
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7470000>
- Essay version: <https://institute.deepmind.com/essays/economic-policy-for-agi/>, retrieved
  2026-10-03.

The prereg and the CSV headers in `analysis/published/` cite local copies at
`docs/economic-policy-for-agi-ssrn.pdf` and `docs/economic-policy-for-agi.html`. Those copies are
not redistributed. To check that yours matches the version we used:

| File | sha256 |
|---|---|
| `economic-policy-for-agi-ssrn.pdf` | `329f21d42fa4cceb999f91f1e765b1d8e1f801271bc4869858e87508f4f436b8` |
| `economic-policy-for-agi.html` (raw page HTML) | `6119a14c2822f769514532600a97d5e527d615cde1865be050416b326fcb7739` |

## Data

The aggregate reports are committed. Raw model responses (the append-only stores under
`results/` and each arm's `results/`) and spend ledgers are not published yet. Whether they can be
redistributed depends on the providers' terms. Results are reported in aggregate only, never per
named economist.

## Running it

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest -q                      # full suite, about 2 minutes; no network or API calls
```

The fake provider runs the whole pipeline at no cost:

```bash
uv run llm-panel plan --design designs/example_fake.yaml --dry-run   # job counts and estimated cost; read-only
uv run llm-panel submit --design designs/example_fake.yaml --confirm # refuses without --confirm or above the ceiling
uv run llm-panel collect                                             # validate, store, retry malformed once
uv run llm-panel status                                              # spend versus the ceiling, row counts
```

This writes under `results/`. Use a scratch copy of `config.yaml` (`--config`) to keep it apart.

### Commands

| Command | What it does |
|---|---|
| `plan` | Count jobs and estimate cost. Never submits |
| `submit` | Submit jobs as batches. Spends money, needs `--confirm` |
| `collect` | Fetch finished batches, validate against the JSON schema, store, retry malformed responses once |
| `reconcile` | Resolve a submit that crashed midway against its local batch file. Makes no provider calls |
| `status` | Spend versus ceiling, row counts |
| `build-personas` | Build a persona source file with provenance |
| `check` | Check smoketest expectations against the store |
| `analyze {baseline,ranks,variance,recommendations,materiality,missing}` | Regenerate the reports in `analysis/` from the raw store |

`plan` and `submit` take `--max-jobs N` for staged runs: finished and in-flight jobs are skipped
and the next N in the design's run order are taken. Each arm has its own entry point
(`uv run python -m adversarial|subagent_arm|scale_probe --help`) and README.

### Real runs

The study used `glm-5.3-flash` via OpenCode Zen, with the key in
`OPENCODE_API_KEY` (put it in a gitignored `.env`). `config.yaml` sets approved providers,
per-model prices and a hard spend ceiling (`max_spend_usd`, at most 15 USD). The ceiling counts
the ledgers of every config, including the arms'. `submit` refuses anything that would go over it.
The study design is `designs/study.yaml`. The `config.smoketest*.yaml` and `config.pilot.yaml`
files are for the pipeline check and the pilot. Their data was never used for inference.

## Design

Clean architecture: a functional core and a thin imperative shell. The layers are domain (pure,
no I/O) -> ports (`ModelClient`, `ResultStore`) -> adapters (provider clients, JSONL store) ->
application (build jobs, submit, collect, analyse) -> bootstrap (config, CLI).

- `job_id` is a sha256 of the rendered prompt, model id, temperature and seed, so reruns skip
  finished work.
- Model snapshots are pinned. Zen ids are aliases, so the model id each response reports is
  logged and checked for drift.
- Every run is logged, failures included, with seed and temperature, in an append-only store.
  Analysis reads only from that store.

## License

MIT, see [`LICENSE`](LICENSE). Evidence excerpts in `evidence/` are from Wikipedia and are
licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); the revision of each
source is recorded in `evidence/raw/manifest.json`.
