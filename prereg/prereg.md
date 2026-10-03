# Preregistration: sensitivity of the "Economic Policy for AGI" panel ratings

**STATUS: DRAFT. NOT FROZEN.** This file becomes binding only when the user tags it frozen
(e.g. git tag `prereg-v1`). No paid API calls may be made while this status is DRAFT.
Anything marked `TODO` is a decision still to be made before freezing.

## 1. Aim

This is a re-implementation of the "Economic Policy for AGI" simulated-economist panel from
its public description (the authors' prompts, persona data and evidence packet are not
available). It is not a strict replication. The aim is a **sensitivity analysis that reports
the whole range of outcomes** across reasonable analyst choices. It is not a search for the
configuration that maximizes variation. The **adversarial arm** (section 8) is separate,
lives in its own directory and is labeled as adversarial wherever it is reported.

Instability of scores would show that they lack the claimed precision. It would not show
that the article's recommendations are wrong. Write-ups must say so.

## 2. Baseline (reference configuration)

All 11 policies are rated in one prompt, per persona and per criterion, with a score from
0 to 100 and a short rationale, on a reconstruction of the paper's setup (about 15 criteria
x 11 policies x 51 personas, roughly 8,400 calls per configuration).
Baseline levels for each factor: TODO (fixed after task "Reconstruct setup from essay text").
Baseline results are compared with the published tables by rank correlation.

## 3. Hypotheses

Stated as directional expectations, to be reported whether or not they hold.

- **H1 (rank stability).** Policy rankings are not highly stable across defensible
  configurations: Kendall's tau between configurations has a lower bootstrap bound below
  TODO (threshold, e.g. 0.8) for at least some factor changes.
- **H2 (persona share).** Persona source and persona identity explain a small share of
  score variance relative to model and prompt wording (i.e. the panel behaves largely as
  one model rather than 51 independent raters).
- **H3 (recommendation survival).** The three-stage recommendation (UI/EITC, then NIT, then
  UBC) is reproduced in only a subset of configurations. We report the fraction.
- **H4 (labeling).** Blinding policy labels (describing mechanics without names) changes
  scores for policies whose definition is loose (e.g. UBC vs Sovereign AI Fund).
- **H5 (precision).** Between-configuration spread of composite scores exceeds the
  one-decimal precision reported by the source by a wide margin.

## 4. Factors

Fractional factorial design (design file: `design.yaml`). Levels marked TODO are decided
before freezing. Pinned model snapshots, never aliases.

| Factor | Levels |
|---|---|
| Model | TODO (snapshot ids for Claude, GPT, Gemini, one open-weights model; subject to the spend ceiling) |
| Persona source | reconstructed survey (51); IGM Clark Center US; IGM Europe; none |
| Prompt wording | baseline; TODO neutral paraphrases |
| Policy labels | named; blinded (mechanics only) |
| Evidence packet | reconstructed; balanced; none |
| Presentation order | TODO (e.g. fixed, reversed, random per seed) |
| Score aggregation | TODO (e.g. mean, median, trimmed mean) |
| Repeats | TODO (number per cell, to separate sampling noise from factor effects) |

Temperature and seed are recorded for every run. Temperature levels: TODO.
Fraction and generator of the fractional factorial: TODO.

## 5. Metrics (fixed in advance)

1. **Kendall's tau** between the policy rankings of pairs of configurations, with bootstrap
   confidence intervals (resampling personas and repeats). Resample count: TODO.
2. **Variance share** of ratings attributable to persona, prompt wording, model and repeat
   noise (variance decomposition; method TODO, e.g. random-effects model).
3. **Survival of the three-stage recommendation**: whether UI/EITC, then NIT, then UBC is
   reproduced under the pre-stated rule TODO (operational definition from composite scores
   and criteria), reported as a fraction of configurations with intervals.
4. Baseline-versus-published rank correlation (supporting).

Secondary descriptives (score spread, tier changes) are reported but are not used for
inference. Any analysis not listed here is labeled exploratory.

## 6. Logging and data handling

- Every run is logged, **including failures**, with seed and temperature.
- The raw store is append-only; rows are never overwritten or deleted.
- Each row holds the full request, the full response including usage fields, the model
  snapshot string, sampling parameters, timestamp and status.
- Job ids are content hashes (rendered prompt, model snapshot, temperature, seed), so reruns
  skip finished jobs.
- Responses are validated against a JSON schema (score 0-100 plus short rationale).
  Malformed responses are retried once, then logged as failures. Failures are reported,
  not silently dropped.
- Analysis reads only from `results/raw`.

## 7. Stopping rules and budget

- Hard spend ceiling: `max_spend_usd = 15`, enforced in code. `submit` requires `--confirm`
  and refuses any job set whose estimated cost plus cumulative actual spend would exceed it.
- Confirm with the user before any paid call on a new provider.
- Stop when the preregistered design is complete or the ceiling would be exceeded,
  whichever comes first. Cells not run are reported as not run. Priority order if the
  budget binds: TODO (which cells are dropped first, fixed before freezing, never decided by
  looking at results).
- No configurations are added, dropped or re-run based on how their results look. Failed
  runs are retried only per the rule in section 6.
- A pilot (about 20 jobs) checks the pipeline end to end; pilot data are logged and
  excluded from inference unless the pilot configuration is part of the design.

## 8. Adversarial arm (separate, labeled)

The smallest plausible change that moves a policy from top to bottom, searched
separately. It lives in its own directory, is reported in its own section labeled
"adversarial", and is not pooled with the main analysis. Its search procedure and budget
are TODO and must be fixed before freezing.

## 9. Limitations

- Re-implementation from the public description, not the authors' materials.
- Simulated personas on a shared model are unlikely to be independent raters.
- No human economist anchor in this study; a small human survey on a subset of policies
  is a possible extension.
- Budget caps the number of models, repeats and cells.

## 10. Amendments

None while DRAFT. After freezing, changes are recorded here with date and rationale, and
analyses affected are labeled as post-hoc.
