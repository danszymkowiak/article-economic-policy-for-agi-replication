# Preregistration: stability of the "Economic Policy for AGI" panel ratings

**STATUS: DRAFT. NOT FROZEN.** This file becomes binding only when the user tags it frozen
(e.g. git tag `prereg-v1`). No paid API calls may be made while this status is DRAFT, except
labeled non-inference runs (smoketest, pilot) the user has approved. Anything marked `TODO` is a
decision still to be made before freezing; section 12 lists them all.

Design basis: the SSRN paper (Jacobs and Imas, 15 Sep 2026, `docs/economic-policy-for-agi-ssrn.pdf`)
and its essay version (`docs/economic-policy-for-agi.html`). The design follows
`spec-v2-draft.md`, which holds the red-team resolution log; where the two differ, this file
governs. Reconstruction choices and which parts are stand-ins are in `reconstruction.md`.

## 1. Aim

This is a re-implementation of the paper's simulated-economist panel from its public description
(the authors' prompts, persona data and literature text are not available). It is not a strict
replication. The paper reports panel-mean scores to one decimal, with no model, temperature or
repeat count, and concedes results cannot be replicated exactly "even with identical prompting".
We measure what the paper leaves open, and report the whole range of outcomes, not a search for
the configuration that maximises variation. The **adversarial arm** (section 9) is separate, lives
in its own directory and is labeled as adversarial wherever it is reported.

Instability of scores would show that they lack the claimed precision. It would not show that the
paper's recommendations are wrong. Write-ups say so next to every headline claim.

## 2. Questions and hypotheses

- **Q1 (repeat stability).** Rerun the same panel with identical inputs: how much do scores,
  ranks, tiers and the headline recommendation move?
- **Q2 (small variations).** How much do they move when a small, defensible input detail changes,
  chiefly replacing policy names with the policy definitions, relative to Q1?

Directional expectations, reported whether or not they hold:

- **H1 (precision).** Repeat-to-repeat variation of a panel-mean score exceeds the paper's
  one-decimal precision (0.05 points) by a wide margin.
- **H2 (recommendation flips from noise alone).** At least one of the four recommendation clauses
  (section 6) flips in some single repeats of the baseline.
- **H3 (labels).** Replacing names with definitions moves scores by at least M (section 6) for
  policies whose definition is loose (e.g. UBC versus Sovereign AI Fund / Dividend).
- **H4 (independence).** The effective number of independent raters in the 51-persona panel is far
  below 51 (the panel behaves largely as one model).

## 3. Inference target and uncertainty

- **Target: the 51 fixed personas.** They are a fixed design, not a sample of economists. The
  primary uncertainty is repeat variance: would the same panel give the same answer again. Q1 and
  Q2 are answered against it.
- A persona bootstrap ("would other personas agree") is secondary, reported only as a
  generalisation caveat, never mixed into a Q1/Q2 comparison.
- Single-run metrics are reported alongside repeat-mean metrics; the paper's situation was
  effectively one run, so the single-run flip rate is the practically relevant number.
- Repeat noise is modelled once: persona x policy x criterion ratings with a repeat-level variance
  fitted from block R, propagated to panel means. Effects are reported in score units and as a
  multiple of the repeat-noise standard error of a panel mean.
- The reference band for "what repeats do" is the contrast of a k_Q-run mean against the remaining
  (k_R - k_Q)-run mean over R's splits. It is a descriptive band, not a test: the splits overlap and
  are not independent.

## 4. Baseline configuration B

Items marked (inf) are our inference from the paper, not stated by it. Stand-ins are listed in
`reconstruction.md`.

- **Unit of call (inf):** one persona x one policy, all criteria returned in one JSON object (score
  0-100 + one-sentence rationale each); policies are scored independently. The paper says 51 x 25 =
  1,275 evaluations "across multiple dimensions" (Figure 2), which supports a persona-by-policy
  unit; "all criteria in one JSON" is our reading. 51 x 11 = 561 calls per configuration-repeat.
- **Policies:** the paper's 11 redistributive policies, each shown by its Table 3 name and
  definition. The paper also scores 14 revenue and governance mechanisms on a different rubric;
  they are out of scope.
- **Criteria:** the 13 panel criteria of the paper's Table 4 and Appendix B (Standards of Living,
  Meaning, Macro Stabilisation; Economic Agency, Ownership, Democratic Voice; Economic Feasibility;
  Implementation Readiness; Mild, Moderate, Full Transformation) plus Political Support and
  Administrative Capacity and Speed (Table 1 criteria not reported in Table 4; compared with the
  essay only). Popular Support is survey data in the paper and is not rated. Wording follows
  paper Table 1 and Figure 1. Readiness carries an unexplained dagger on every Appendix B profile
  (no footnote in the paper; the essay calls it "author-coded"): we rate it, and its published
  comparison is lower-confidence.
- **Evidence (inf):** one fixed packet per policy, identical across personas, from pinned English
  Wikipedia revisions: verbatim, evidence-only excerpts extracted by two independent LLM passes
  (union), every span verified as an exact substring (`evidence/`). The paper says agents are
  "prompted with extensive literature reviews" but not what they said; the Wikipedia packets are a
  stand-in. Packets are published with attribution. Evidence is uneven across policies because the
  sources are; packet size is recorded and its association with scores reported.
- **Personas:** the 51 named economists of the paper's Appendix A, Table 7 (name, institution,
  primary field). The paper's personas also drew on biographies, research histories and actual IGM
  survey responses, which we do not have, so the model's memorised knowledge of each person fills
  the gap. John Cochrane is named in the paper's text but is not in Table 7; we use Table 7.
  Results are reported only in aggregate, never per named economist, and no rationale text
  attributed to a named person is published.
- **Model:** one cheap pinned study model on OpenCode Zen, provider-default temperature (TODO:
  model id; the temperature is recorded and measured in the pilot).
- **Aggregation:** unweighted mean over personas; composites are unweighted means of sub-criteria
  (checked against the published composites in the baseline-comparison task).

## 5. Design

One-at-a-time from B. Not a fractional factorial: with a small budget it would spread runs too
thin to separate effects from noise. All cells use the same 51 personas (paired). Run order is
randomised and cells and repeats are interleaved over time.

**Block R, noise floor (Q1).** B repeated k_R times; **R-T**: B at temperature 0 and one higher
level (TODO: level); **B'**: one more B repeat at the very end, as a provider-drift control.

**Block Q, small variations (Q2), k_Q repeats each, nothing else changed:**

| Cell | Change |
|---|---|
| Q1 description-only | policy name removed everywhere (prompt, evidence packet, labels use neutral codes P1..P11); the definition is the only identifier |
| Q2a-c description wording | three meaning-preserving paraphrases of the Table 3 definitions |
| Q3a-c instruction wording | three paraphrases of the instruction/rubric text |
| Q4 evidence | no packet (the "none" level) |

**Block D, design changes (reported separately, not "small variations"):** D1 joint scoring, all 11
policies in one prompt per persona x criterion (612 calls per repeat); D2 no persona (11 policies x
many repeats; also an independent noise estimator); D2b our synthetic trait panel in place of the
named economists; D3 a second pinned model, if budget allows.

Temperature and seed are recorded for every run. Zen may ignore `seed`; the pilot checks, and if it
does repeats measure sampling noise and are not reproducible by seed.

## 6. Metrics (fixed in advance)

**Primary, per Q cell and for each R-T cell versus B, compared with the same quantities in R:**

1. **Flip counts:** (a) the four recommendation clauses below, flipped or not in each single run
   and in the repeat-mean; (b) tier changes among the paper's tiers for the composites in Table 4.
2. **Materiality shifts:** the number of policy x criterion panel means whose |shift| from B
   exceeds **M = 5 points** (about one-sixth of a tier width and far above the paper's one-decimal
   precision; set now, not from data), with the repeat-noise multiple. Sensitivity to M (3 and 8)
   is shown descriptively and is not used to pick M.

**Rank metrics, reported for every cell (the paper makes its recommendations by rank order) but
secondary to flips:** Kendall tau on the three durability composites and each dimension composite
between a cell and B; per-policy rank shift; top-3 and bottom-3 set changes. Ties are broken by
average rank. Tau moves only when near-ties swap, and Table 4 has many (UBC 66.0 vs UI 65.9 on
Moderate; three scores exactly 65.0 on Full Transformation).

Holm correction applies to the primary set only, and only if inference language is used. Everything
else (each criterion x cell, descriptive heatmaps, variance decomposition) is descriptive and
unthresholded. Any analysis not listed here is labeled exploratory.

**Recommendation clauses.** These restate the paper's own claims, with cut-offs chosen from
Table 4; the published data pass them, so the baseline is not a test of the paper. Each is reported
with its continuous margin (score gap to the next policy):

- (a) UBC rank 1 on Full Transformation durability (published margin 15.5);
- (b) UBC rank 1 on Ownership of Gains (margin 40.0);
- (c) NIT in the top 3 on Moderate durability (published rank 2; margin to rank 4 is 3.8);
- (d) UI and EITC both in the top 4 on Mild durability (published ranks 3 and 4; EITC margin 5.9)
  and both below UBC on Full Transformation durability.

The paper's Mild-scenario recommendation also names employer-led retraining, but ALMP scores 42.5 on
Mild in Table 4, so the published data do not support that part; it is excluded from the clauses and
reported as such. Also reported, recomputed per cell: the paper's r(public net approval, Full
Transformation durability) = -0.57 (recomputed -0.569 from Table 4; approvals are fixed survey
inputs) and r(Readiness, Full Transformation durability) = -0.51.

**Secondary descriptives:** persona-level SD across repeats and the effective number of raters;
within-call correlation among criteria (halo); variance decomposition with persona x policy crossed
random effects and cells as fixed effects.

**Comparison with the paper (supporting only):** rank agreement of B with Table 4 and the essay.
Table 4 has many round values (65.0 three times, 50.0, 27.0, 30.0, 78.0, 68.0) that a mean of 51
continuous scores would rarely produce, so the paper's aggregation or adjustment is uncertain, and
agreement does not validate our procedure. Our output schema and comparison table mirror the
paper's Appendix B per-policy profiles.

## 7. Logging, validity and data handling

- Every run is logged, **including failures**, with seed and temperature. The raw store is
  append-only; rows are never overwritten or deleted. Each row holds the full request, the full
  response including usage fields, the model snapshot string, sampling parameters, timestamp and
  status. Job ids are content hashes (rendered prompt, model snapshot, temperature, seed), so reruns
  skip finished jobs. Analysis reads only from `results/raw`.
- Responses are validated against a JSON schema. Malformed responses are retried once, then logged
  as failures and reported, not silently dropped. Retry is logged per row.
- **Pilot first** (about 20 jobs, excluded from inference) measures: input, output and reasoning
  tokens per call and the cost per configuration-repeat at Zen's price for the exact model id;
  failure and truncation rate; whether temperature and seed change outputs; the provider-default
  temperature behaviour; the model id reported per response.
- **Failures and truncation.** A `max_tokens` cap is set from the pilot so truncation is rare;
  truncation or reasoning exhaustion counts as failure. Cells are compared on the common-complete
  persona x policy set (primary); survivor-only means are secondary; a worst-case bound (failures
  imputed at 0 and 100) is reported. A cell above 10% failures is flagged and still analysed on the
  common-complete set.
- **Paraphrase integrity.** Paraphrase texts are frozen by hash before the pilot; meaning
  equivalence is checked by a second model and by the user's review; paraphrases that fail are
  replaced under a pre-stated rule before any data run, never afterward.
- **Drift.** The model id each response reports is tabulated per cell; B' tests for drift.

## 8. Stopping rules and budget

- Hard spend ceiling: `max_spend_usd = 15`, enforced in code. `submit` requires `--confirm` and
  refuses any job set whose estimated cost plus cumulative actual spend would exceed it. Confirm
  with the user before any paid call on a new provider.
- k_R and k_Q are not frozen: they are set from the pilot's measured cost, with an indicative floor
  of k_R >= 5 and k_Q >= 3.
- Priority order if the budget binds (fixed now): R with B', Q1, Q2a-c, Q4, Q3a-c, R-T, D2, D1, D3.
  A block runs only if its precomputed cost fits under the ceiling. Cells not run are reported as
  not run. If too expensive, drop Q3, R-T and D3 first.
- No configurations are added, dropped or re-run based on how their results look.

## 9. Adversarial arm (separate, labeled)

The smallest plausible change that moves a policy from top to bottom, searched separately. It lives
in its own directory, is reported in its own section labeled "adversarial", and is not pooled with
the main analysis. Its search procedure and budget are TODO and must be fixed before freezing.

## 10. Decisions log

- 2026-10-04 (user): named-economist personas from Appendix A (match the paper); results reported
  in aggregate only.
- 2026-10-04 (user): materiality margin M = 5 and the primary metric set accepted (called somewhat
  arbitrary but acceptable); rank metrics reported alongside as the paper's own decision basis.
- 2026-10-04 (user): evidence from a single source (Wikipedia), evidence-only, verbatim LLM
  extraction with attribution, published; union of two passes for all articles; the Wage insurance
  line kept under the union rule.
- 2026-10-04 (user): IGM panel levels dropped; synthetic trait panel kept as variation D2b.

## 11. Limitations

- Re-implementation from the public description, not the authors' materials; personas, evidence
  and prompts are stand-ins, so absolute levels are not the paper's.
- Simulated personas on one model are not independent raters; the effective number is reported.
  Named personas bring the model's memorised, possibly inaccurate, ideas of real people.
- One cheap model unless D3 runs; conclusions are conditional on it. One-at-a-time cannot show
  interactions. Criteria are scored together within a call, so criterion-level results are
  conditional on that.
- Evidence packets are uneven across policies (Wage insurance nearly empty; UBC rests on Baby
  bonds) and two extraction passes by one model do not prove completeness.
- No human economist anchor in this study.
- Model snapshots cannot be pinned on OpenCode Zen: it serves model ids (e.g. `glm-5.3-flash`) that
  the provider can repoint. The reported model id is stored per row and checked against the
  requested id; `status` warns and `submit` refuses if a row reports a different id or the id changes
  during the study. This detects a visible change but not a silent one behind an unchanged id, so
  rankings are conditional on the provider serving one model throughout.
- Budget caps the number of models, repeats and cells.

## 12. Open TODOs before freezing

1. Model id for the study (and for D3, if run).
2. Temperature levels for R-T; the default temperature is measured in the pilot.
3. k_R and k_Q, from the pilot's cost and failure measurements.
4. Paraphrase texts for Q2a-c and Q3a-c, hashed, equivalence-checked.
5. `max_tokens` cap, from the pilot.
6. Persona bootstrap resample count (secondary analysis).
7. Adversarial-arm procedure and budget.
8. Design file: the expander must produce one-at-a-time cells (the existing fractional expander is
   not used); regenerate and diff against the frozen copy before the full run.
9. Pipeline changes for one persona x policy calls with per-policy evidence packets and the named
   persona builder.

## 13. Amendments

None while DRAFT. After freezing, changes are recorded here with date and rationale, and analyses
affected are labeled as post-hoc.
