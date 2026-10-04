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
  unit; "all criteria in one JSON" is our reading. 51 personas x 11 policies = 561 calls per
  configuration-repeat; each call returns 13 ratings, so 561 x 13 = 7,293 ratings.
- **Policies:** the paper's 11 redistributive policies, each shown by its Table 3 name and
  definition. The paper also scores 14 revenue and governance mechanisms on a different rubric;
  they are out of scope.
- **Criteria:** 13 rated criteria in total (user decision 2026-10-04): the 11 panel criteria of
  the paper's Table 4 and Appendix B (Standards of Living, Meaning, Macro Stabilisation; Economic
  Agency, Ownership, Democratic Voice; Economic Feasibility; Implementation Readiness; Mild,
  Moderate, Full Transformation) plus Political Support and Administrative Capacity and Speed
  (Table 1 criteria not reported in Table 4; compared with the essay only). They are in
  `designs/inputs/criteria.yaml`. Popular Support is survey data in the paper and is not rated. Wording follows
  paper Table 1 and Figure 1, except Implementation Readiness, which has no Table 1 definition:
  its description is our wording. Readiness carries an unexplained dagger on every Appendix B profile
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
| Q2a-c description wording | three meaning-preserving paraphrases of the Table 3 definitions (`designs/inputs/description_paraphrases/para_1..3.yaml`) |
| Q3a-c instruction wording | three paraphrases of the instruction/rubric text (`prompts/persona_policy/para_1..3.txt`; B uses `prompts/persona_policy/baseline.txt`) |
| Q4 evidence | no packet (the "none" level) |

Prompt wording is ours (`reconstruction.md` R5). Every template and paraphrase file is listed with
its sha256 and an equivalence record in `prompts/manifest.yaml`, reviewed by the user 2026-10-04;
the hashes are copied here at freezing.

**Block D, design changes (reported separately, not "small variations"):** D1 joint scoring, all 11
policies in one prompt per persona x criterion (`prompts/joint/baseline.txt`; 51 personas x 13
criteria = 663 calls per repeat, each returning 11 ratings: 663 x 11 = 7,293 ratings, the same as
B); D2 no persona (one call per policy, 11 calls per repeat, many repeats: 51 repeats x 11 = 561
calls, the same as one B repeat, so it serves as an independent noise estimator);
D2b our synthetic trait panel in place of the named economists; D3 a second pinned model, if
budget allows.

**Call counts.** A persona x policy configuration-repeat is 51 x 11 = 561 calls (B, B', R-T, every
Q cell, D2b, D3); a D1 repeat is 51 x 13 = 663 calls; a D2 repeat is 11 calls. With the repeat
counts of section 8 (k_R for B, one B', 51 for D2, k_Q for every other cell):

| Unit | Cells | Calls |
|---|---|---|
| R | B, B' | 561 x (k_R + 1) |
| R-T | 2 | 2 x 561 x k_Q = 1,122 k_Q |
| Q1, Q4 | 1 each | 561 k_Q each |
| Q2, Q3 | 3 each | 3 x 561 x k_Q = 1,683 k_Q each |
| D1 | 1 | 663 k_Q |
| D2 | 1 | 11 x 51 = 561 |
| D2b, D3 | 1 each | 561 k_Q each |

Full plan: 561 x (k_R + 1) + 561 + k_Q x (1,122 + 2 x 561 + 2 x 1,683 + 663 + 2 x 561) =
561 x (k_R + 2) + 7,395 k_Q calls. At the indicative floor k_R = 5, k_Q = 3: 561 x 7 = 3,927 plus
7,395 x 3 = 22,185, total 26,112 calls (D3's on a second model, priced separately). Cost per
call is measured in the pilot; section 8 applies it.

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
- Repeats: B gets k_R repeats and B' one; D2 gets 51 repeats (11 x 51 = 561 calls, one B
  repeat's worth, so it works as an independent noise estimator); each R-T cell, each Q cell and
  D1, D2b and D3 get k_Q repeats. k_R and k_Q are not frozen: they are set after the pilot from
  its measured cost, with an indicative floor of k_R >= 5 and k_Q >= 3. Call counts per unit are
  in section 5.
- Priority order if the budget binds (fixed now): R with B', Q1, Q2a-c, Q4, Q3a-c, R-T, D2, D2b,
  D1, D3.
- Stopping rule, applied to precomputed unit costs against the budget left under the ceiling
  (ceiling minus actual spend). A unit runs whole or not at all. If the full plan exceeds the
  budget, drop Q3, then R-T, then D3, in that order, until it fits. Then walk the priority order
  and stop at the first unit that does not fit; no cheaper lower-priority unit is run after it.
  Cells not run are reported as not run, with the reason.
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
- 2026-10-04 (user): 13 rated criteria (11 Table 4 columns plus Political Support and
  Administrative Capacity and Speed); call counts recomputed (section 5). Implementation Readiness
  has no Table 1 definition, so its wording is ours. The criteria, policy definitions, templates
  and paraphrases were reviewed as drafted (`prompts/manifest.yaml`, hashes unchanged). D2b sits
  right after D2 in the priority order; R-T cells and D1, D2b, D3 get k_Q repeats each, D2 gets 51
  (561 calls); the stopping rule
  reads as stated in section 8.
- 2026-10-04 (user): staged execution. The study runs in stages, and the user may raise the
  account budget between stages. The code ceiling `max_spend_usd = 15` stays until the user
  changes it explicitly in config.

## 11. Limitations

- Re-implementation from the public description, not the authors' materials; personas, evidence
  and prompts are stand-ins, so absolute levels are not the paper's.
- Simulated personas on one model are not independent raters; the effective number is reported.
  Named personas bring the model's memorised, possibly inaccurate, ideas of real people.
- One cheap model unless D3 runs; conclusions are conditional on it. One-at-a-time cannot show
  interactions. Criteria are scored together within a call, so criterion-level results are
  conditional on that.
- Implementation Readiness has no definition in the paper's Table 1; its criterion text is our
  wording, so its scores (already lower-confidence, section 4) rest partly on our phrasing.
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
4. Paraphrase texts for Q2a-c and Q3a-c: partly done. Written, hashed in `prompts/manifest.yaml`
   and reviewed by the user 2026-10-04 with the author's element checklists. Open: the
   second-model equivalence check (section 7) and copying the hashes into this file at freezing.
5. `max_tokens` cap, from the pilot.
6. Persona bootstrap resample count (secondary analysis).
7. Adversarial-arm procedure and budget.
8. Design file: the one-at-a-time expander exists (`domain/oat_design.py`, TASK-32; the fractional
   expander is not used). Open: the study design file with the pilot's k_R and k_Q; regenerate and
   diff against the frozen copy before the full run.
9. Pipeline changes: partly done. Named persona builder (TASK-31), templates and renderer for
   persona x policy and joint calls (TASK-16) exist, and the study config points at
   `designs/inputs`. Open (TASK-33): job building from the new renderer with per-policy evidence
   packets (names removed for Q1), and a response schema with one entry per criterion.

## 13. Amendments

None while DRAFT. After freezing, changes are recorded here with date and rationale, and analyses
affected are labeled as post-hoc.
