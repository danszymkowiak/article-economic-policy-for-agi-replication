# article-economic-policy-for-agi-replication

This project re-implements, from the public description only, the simulated-economist panel of
["Economic Policy for AGI"](https://institute.deepmind.com/essays/economic-policy-for-agi/)
by the DeepMind Institute, and studies how sensitive its rankings are to small changes in the
survey approach. It is a re-implementation, not a strict replication: see
[`prereg/reconstruction.md`](prereg/reconstruction.md) for every reconstruction choice and which
parts are our own stand-ins.

## Approach

The authors' prompts, persona data and evidence packet are not available, so this is a
re-implementation from the public description rather than a strict replication. The aim
is a preregistered sensitivity analysis that reports the full range of outcomes, plus a
separate, clearly labeled adversarial arm.

1. **Baseline**: reconstruct the setup from the essay (all 11 policies in one prompt) and
   compare against the published tables by rank correlation.
2. **Factors** (fractional factorial): model, persona source (reconstructed survey, IGM
   Clark Center US, IGM Europe, none), prompt wording, blinded policy labels, evidence
   packet (reconstructed, balanced, none), presentation order, score aggregation, repeats.
3. **Measures**: Kendall's tau between configurations with bootstrap intervals; variance
   share from persona vs prompt vs model vs repeat noise; whether the three-stage
   recommendation (UI/EITC, then NIT, then UBC) survives.
4. **Adversarial arm**: the smallest plausible change that moves a policy from top to bottom.
5. **Preregistration**: the analysis plan in `prereg/` is frozen and tagged before any paid
   run, and every run is logged, failures included.

Instability of the scores would show they lack the claimed precision, not that the
recommendations are wrong.

## Design notes

Python with a layered layout (domain, ports, adapters, application, bootstrap) and
cron-friendly CLI commands (`plan`, `submit`, `collect`, `status`). Jobs are content-addressed
by a hash of the rendered prompt, model snapshot and sampling parameters, so reruns skip
completed work. Raw results go to an append-only store and analysis reads only from it.
Model snapshots are pinned, and total spend is capped at 15 USD in code. Work is tracked in
`backlog/`.

## Source article

A snapshot of the article, retrieved on 2026-10-03, is kept for posterity in
[`docs/economic-policy-for-agi.html`](docs/economic-policy-for-agi.html). The live
page may change or disappear; the snapshot is the reference for this re-implementation.
It is the raw HTML of the page, so external assets such as images and styles are not
included.

## Running the pipeline (fake provider only so far)

```bash
uv run llm-panel plan --design designs/example_fake.yaml --dry-run   # counts and estimated cost; read-only
uv run llm-panel submit --design designs/example_fake.yaml --confirm # refuses without --confirm or over the ceiling
uv run llm-panel collect                                             # validate, store, retry malformed once
uv run llm-panel status                                              # spend versus the 15 USD ceiling
```

`config.yaml` holds the ceiling (`max_spend_usd`, rejected above 15), approved providers and
per-snapshot prices. Spend checks use actual stored usage plus the estimated cost of batches
still in flight plus the new job set. Running this against the example design writes under
`results/`; use a scratch copy of `config.yaml` for experiments.
