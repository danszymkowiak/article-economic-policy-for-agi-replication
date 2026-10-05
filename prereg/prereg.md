# Preregistration: stability of the "Economic Policy for AGI" panel ratings

**STATUS: FROZEN (2026-10-04), binding from the git tag `prereg-v1`, which the user places.**
Before the tag this file is still a draft and no paid API calls may be made, except labeled
non-inference runs (smoketest, pilot) the user has approved. After the tag, changes are recorded
only in section 13 (Amendments) with date and rationale, and analyses affected are labeled post-hoc.
Section 9a (the Claude subagent arm) is frozen with the rest.

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
- **Model:** one cheap pinned study model on OpenCode Zen, provider-default temperature: `glm-5.3-flash`
  (a Zen alias, so the model id each response reports is logged; the temperature is recorded).
- **Aggregation:** unweighted mean over personas; composites are unweighted means of sub-criteria
  (checked against the published composites in the baseline-comparison task).

## 5. Design

One-at-a-time from B. Not a fractional factorial: with a small budget it would spread runs too
thin to separate effects from noise. All cells use the same 51 personas (paired). Run order is
randomised and cells and repeats are interleaved over time.

**Block R, noise floor (Q1).** B repeated k_R times; **R-T**: B at temperature 0 and one higher
level (0.0 and 1.0); **B'**: one more B repeat at the very end, as a provider-drift control.

**Block Q, small variations (Q2), k_Q repeats each, nothing else changed:**

| Cell | Change |
|---|---|
| Q1 description-only | policy name, label and acronym removed (prompt, evidence packet; labels use neutral codes P1..P11); the definition is the only identifier. Real-world programme names inside the packets (e.g. Alaska Permanent Fund, Baby bonds) are kept, as accepted in section 10 |
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

1. **Flip counts:** the four recommendation clauses below, flipped or not in each single run
   and in the repeat-mean. (Tier changes are not a metric: the paper defines no usable tiers, and
   the essay's cut-offs are inconsistent, e.g. Mixed 42-54 or 40-54.)
2. **Materiality shifts:** the number of policy x criterion panel means, over the 11 Table 4
   criteria, whose |shift| from B exceeds **M = 5 points** (about one-third of a tier width and far above the paper's one-decimal
   precision; set now, not from data), with the repeat-noise multiple. Sensitivity to M (3 and 8)
   is shown descriptively and is not used to pick M. The two added criteria (Political Support,
   Administrative Capacity and Speed) are counted separately and descriptively, never in the primary
   count.

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
- (c) NIT in the top 3 on Moderate durability (published rank 2; margin to UI at rank 4 is 3.9);
- (d) UI and EITC both in the top 4 on Mild durability (published ranks 3 and 4; EITC margin 5.9)
  and both below UBC on Full Transformation durability.

The paper's Mild-scenario recommendation also names employer-led retraining, but ALMP scores 42.5 on
Mild in Table 4, so the published data do not support that part; it is excluded from the clauses and
reported as such. Also reported, recomputed per cell: the paper's r(public net approval, Full
Transformation durability) = -0.57 (recomputed -0.569 from Table 4; approvals are fixed survey
inputs) and r(Readiness, Full Transformation durability) = -0.51.

**Secondary descriptives:** persona-level SD across repeats and the effective number of raters
(primary ICC: per policy x criterion cell; the per-criterion agreement across policies is
secondary);
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

**Prompt and paraphrase hashes** (sha256, copied from `prompts/manifest.yaml` on 2026-10-04 after the user
confirmed the wording, except the last two rows, copied from `subagent_arm/manifest.yaml`; `tests/bootstrap/test_prompt_files.py` fails if a file and the manifest disagree):

| File | Role | sha256 |
|---|---|---|
| `prompts/joint/baseline.txt` | D1 joint scoring (all 11 policies, one criterion per call) | `686c1224cb45f57888e88149a1c9f0231129f14163531975b769c4057a2e4f04` |
| `prompts/persona_policy/baseline.txt` | B baseline instruction wording (also used by Q1, Q2a-c, Q4) | `e1dcf123fba8fd358e1ea4bf16b424614ae49e545ae9ce3cfe6dcb4b3c6587e8` |
| `prompts/persona_policy/para_1.txt` | Q3a instruction paraphrase of persona_policy/baseline.txt | `6e5611d02ffd54e9e147c8dd3dfe0c48423903f5dcaa321aaae3954dc10746ed` |
| `prompts/persona_policy/para_2.txt` | Q3b instruction paraphrase of persona_policy/baseline.txt | `d49cd789bce35cd271477506b370b6a5372b6fa6ca2f1875e964c1a82394d0e6` |
| `prompts/persona_policy/para_3.txt` | Q3c instruction paraphrase of persona_policy/baseline.txt | `18070f211d4d698d8c47d867f35f570dc18543f7d584b2d74ad79f339c8676fa` |
| `designs/inputs/description_paraphrases/para_1.yaml` | Q2a paraphrase of the Table 3 definitions (designs/inputs/policies.yaml) | `6e3f059abe3062ed86fa8edf5457c34c097dc087d111a01889e8b312b8e372e9` |
| `designs/inputs/description_paraphrases/para_2.yaml` | Q2b paraphrase of the Table 3 definitions (designs/inputs/policies.yaml) | `8ad9f3f14524efa686a867e1457790e3bc3f58587bf2b8d0d9dd69878ad1a143` |
| `designs/inputs/description_paraphrases/para_3.yaml` | Q2c paraphrase of the Table 3 definitions (designs/inputs/policies.yaml) | `506f86b37e8ba451a438e3fa70e27335c373ee09b6a3882d8f07666baa422dfd` |
| `.claude/agents/rater.md` | Claude arm harness (s9a): rater agent type (system prompt, Read and Write tools only, model haiku) | `7a924873e1c1d53b114f2f4b9d272054cf2d26e57790b1283910bbe7de2abdb7` |
| `subagent_arm/arm.py` | Claude arm harness (s9a): driver code holding the agent prompt wrapper (agent_prompt), the line-to-JSON conversion (lines_to_json), the tool-use rule and the one-retry ingest | `42532cedb214f3ebaef34832d85356f3f9cb908901404386ef2a0ca828ffb108` |

## 8. Stopping rules and budget

- Hard spend ceiling: `max_spend_usd = 15`, enforced in code. `submit` requires `--confirm` and
  refuses any job set whose estimated cost plus cumulative actual spend would exceed it. Confirm
  with the user before any paid call on a new provider.
- Repeats: B gets k_R repeats and B' one; D2 gets 51 repeats (11 x 51 = 561 calls, one B
  repeat's worth, so it works as an independent noise estimator); each R-T cell, each Q cell and
  D1, D2b and D3 get k_Q repeats. k_R = 5 and k_Q = 3 (the floors, frozen
  2026-10-04 by the user). Call counts per unit are
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
in its own directory (`adversarial/`), is reported in its own section labeled "adversarial", and is
not pooled with the main analysis. It is a worst-case search by design, not an estimate of
stability. Procedure and budget (TASK-22; reviewed and accepted by the user, frozen with this file):

- **Catalogue** `adv-catalogue-v1` (`adversarial/catalogue.py`), fixed before any adversarial
  data; any change is a new version, and the code refuses a config naming another. Fourteen
  entries: five meaning-preserving one-sentence wording edits of `prompts/persona_policy/
  baseline.txt`; four edits of the target policy's evidence packet (drop its last excerpt, drop its
  first, reverse the excerpt order, keep the first half); dropping, at evaluation, the search-panel
  persona who rated the target highest (no new calls); temperature 0 or 1; criteria in reverse
  order or the primary composite's criteria first.
- **Search panel**: 5 of the 51 named personas drawn with seed 20261004, every policy, B's
  persona x policy prompt and model, one run per candidate at seed 0. A baseline rerun at seed 1
  is the repeat-noise reference for the target's rank.
- **Target and outcome**: the policy ranked first on Full Transformation durability (clause (a))
  in the search-panel baseline; success is that policy in strictly last place.
- **Greedy search, depth <= 2**: depth 1 runs every entry alone. If any succeeds, the smallest
  success wins. Otherwise the entry with the largest rank drop of the target is kept (ties: the
  smaller edit, then catalogue order), and depth 2 runs it combined with every entry of a
  different slot; the smallest success wins. The search stops at the first success, when no entry
  lowers the target, at depth 2, at 30 candidates, or when the budget is exhausted.
- **Smallest** means the lowest edit size, compared in order: number of perturbations; the most
  characters changed in any one rendered prompt (each perturbation's changed span, summed); the
  number of prompts changed. Temperature and the persona drop change no characters, and the report
  shows each component.
- **Reporting**: every candidate tried is reported, with its target rank, rank drop and edit size,
  not only the winner; their number is the multiple-comparisons denominator. The report
  (`adversarial/report.md`) is headed "ADVERSARIAL ARM — not pooled with the main analysis".
- **Budget**: 2.50 USD (`adversarial/config.adversarial.yaml`), with its own store and ledger
  under `adversarial/results/`. It counts toward the global 15 USD cap in both directions
  (`counts_spend_from`). Candidates are submitted whole, in search order, through the study's
  `--confirm` and ceiling guards. A candidate whose estimate does not fit waits (no cheaper later
  candidate is sent ahead of it) until collected spend frees room; when nothing fits and nothing
  is in flight, the search stops as budget exhausted. At the pilot's measured cost (about
  0.0015 USD per call, 55 calls per candidate) the budget covers the noise rerun, depth 1 and a full depth 2 (about 2.40
  USD in all).

## 9a. Claude cross-model arm (separate, labeled; TASK-35)

Purpose: a second model on the baseline only, so the report can show how much of the variation in
section 6 is due to the choice of model and how that compares with run-to-run noise. It is not a
battery: none of the Q, R-T or D variations are run on it. It is a user-approved exception to the
"single structured batch calls, not agentic subagents" rule, so it is labeled, kept in its own
directory (`subagent_arm/`) and store, never pooled with the main analysis, and its rows never
enter the main inference. It is also not D3: D3 is a second API model through the same batch
path and is not run (no second model approved).

- **Model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`), run as Claude Code subagents with the
  model set to haiku. Whether the subagent reports a snapshot is checked and recorded per run;
  if only an alias is available, that is stated in the report. Temperature and seed cannot be set
  (recorded as "not controllable"), so job ids are not comparable to the main store's and runs
  are not reproducible by seed.
- **Design:** the baseline B configuration unchanged (named personas, Wikipedia evidence, the
  baseline instruction wording, 13 criteria), one fresh subagent per persona x policy call, given
  the exact rendered B prompt (561 calls per pass) as the content of a task file. The agent's own
  instruction is a fixed wrapper (see Reply format and Tool use below). The only tool use allowed
  is one Read of that task file and one Write of its answer file; a run showing any other tool use
  is discarded and logged as a failure, so that no run can see published scores.
- **Passes (changed 2026-10-04, user):** one pass over every persona x policy call (561 agents),
  then two further passes over a single policy, Universal Basic Capital (UBC), with all 51
  personas (51 agents per pass): 3 passes on UBC in all, 663 agents. The cost was measured in the
  pilot (about 0.055 USD-equivalent per agent in Claude Code usage; 3 full passes, 1,683 agents,
  is not affordable). UBC was chosen as the policy the paper's headline recommendations rest on
  (clauses (a), (b) and (d) of section 6; its Table 4 cells are the most-cited). It is fixed now,
  not from data. Each Table 4 cell is a mean over the 51 personas, so the repeated unit is a whole
  policy with the full panel: Claude's repeat noise is measured on the 13 UBC panel means and on
  persona-level SDs, not on all 143 policy x criterion cells. Passes run in full, in order; a
  partial pass is reported as such and not used in repeat-mean quantities. No other cells.
- **Reply format (changed after the pilot, 2026-10-04):** agents write one line per criterion,
  `criterion_id | score | rationale`, instead of hand-written JSON, because in the pilot 11 of 36
  first attempts at JSON failed the syntax check (mostly a stray closing brace) and 3 of 7 retries
  failed again. `ingest` converts the lines to the study's JSON mechanically (it never changes a
  score or rationale; a rationale may contain a pipe) and the agent's own text is kept in the row.
  The task text is otherwise exactly B's prompt; the wrapper tells the agent to ignore its JSON
  reply instruction. With lines, 20 of 20 first attempts passed (pilot, 2026-10-04).
- **Tool use:** a valid run shows 3 tool uses (Read, Write and the harness hand-back); any other
  count is discarded, logged and retried once. The restricted `rater` agent type (Read and Write
  only, Haiku; `.claude/agents/rater.md`) is used for every run. The agent definition and the
  driver code that holds the agent prompt wrapper and the line conversion are pinned by hash
  (`subagent_arm/manifest.yaml`, in section 7 above); a change after the tag is an amendment and the arm is
  then labeled post-hoc. Measured on 20 pilot agents: 20 of 20 valid first attempts, all with 3
  tool uses.
- **Validation and logging:** replies go through the same JSON schema check as the main arm;
  malformed ones are retried once, then logged as failures. Every run is logged, including
  failures and discards, with a null temperature and seed.
- **Comparison 1, stability** (descriptive): for UBC only (the repeated policy), repeat-to-repeat
  noise of the panel mean per criterion, persona-level SD across the three passes, and the
  persona-versus-run-noise variance decomposition and n_eff. Rank stability across passes cannot be
  computed on Claude (ranks need every policy repeated); instead recommendation clauses (a) and (b)
  are evaluated per pass with that pass's UBC means against pass 1's means for the other policies.
  Then between models: the number of policy x criterion panel means shifted from B by more than
  M = 5 (all 143 cells from pass 1; the UBC cells also shown beside Claude's and B's repeat noise),
  and the same recommendation clauses and ranks from pass 1.
- **Comparison 2, distribution of responses** (descriptive): the distribution of single ratings
  per criterion (mean, SD, quantiles, share of round values and of the extreme 0-10 and 90-100
  bands), the spread of persona means, within-call correlation among criteria (halo), failure and
  discard rates, rationale length, and agreement with published Table 4 for each model.
- **Reading:** B repeats (k_R = 5) give glm-5.3-flash's repeat noise; the Claude UBC repeats give
  Haiku's, for UBC only (so the repeat-noise comparison is limited to UBC cells). A between-model shift is read against both. A difference between the models is a
  difference between two model-and-harness bundles (model, agentic wrapper, uncontrolled
  sampling), not a clean model effect; it shows that scores depend on which model is used, not
  that either is right. There is no inference language and no Holm correction here.
- **Budget:** no spend through the ledger or the 15 USD ceiling; it uses Claude Code usage, so
  the user is told the agent count (663: 561 + 2 x 51) before the run starts and approves it.

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
- 2026-10-04 (implementer, TASK-33; for user review): (a) D1's evidence is all 11 packets
  concatenated in Table 3 order, each under its own header, so D1 shows the same evidence text as
  B, in one prompt. (b) Q1 de-names packet text by fixed rules (`domain/denaming.py`): the header
  and the source-article titles in the packet's metadata become the neutral code ("P11 source 1"),
  and every policy's names, acronyms and listed variants (e.g. EIC, SWF) become that policy's
  code anywhere in the text. Descriptive wording and real-world programme names (e.g. Alaska
  Permanent Fund, Mincome, Baby bonds, Canada's EI) stay, because they are content, not policy
  labels; the definition already describes the policy. (c) The per-call output-token estimate
  and the `max_tokens` cap scale with ratings per call (13 for a persona x policy call), so the
  estimate is an upper bound until the pilot calibrates it.
- 2026-10-04 (user, TASK-34): tier-change metric (old s6 item 1b) dropped; effective number of
  raters uses the per policy x criterion ICC as primary; the primary materiality count covers the
  11 Table 4 criteria, with the 2 added criteria a separate descriptive count; s6 clause (c) margin
  corrected to 3.9 (NIT 69.8 minus UI 65.9 at rank 4).
- 2026-10-04 (user, TASK-34): adversarial arm accepted as drafted (14-entry catalogue, 5-persona
  search panel, Full Transformation composite, target rule, edit-size order); budget raised from
  1.50 to 2.50 USD (full depth 2 at pilot prices is about 2.40), still inside the 15 USD global cap.
- 2026-10-04 (implementer, TASK-34, user delegated the choice; for review): k_R = 5 and k_Q = 3
  (the floors; the full plan is about 24,400 calls, roughly 37 USD actual at the pilot's 0.0015
  USD per call, so it runs in stages). R-T temperatures 0.0 and 1.0 (the pilot did not establish
  the provider default, so the two natural bounds). `max_tokens` 400 per rating (5,200 per
  13-rating call, 1.5x the pilot maximum of 3,471 output tokens; median 2,626). Bootstrap
  resamples 2,000 (conventional, seeded; secondary analysis only). D3 not run (no second model).
  The code's cost estimate uses the cap as the output size, so it is about 2x actual (72.7 vs
  about 37 USD for the full plan) and the ceiling guard is correspondingly conservative.
- 2026-10-04 (implementer, TASK-34; user suggested using Claude): independent equivalence check of
  the 3 instruction and 3 definition paraphrases by a fresh Claude instance that saw only the
  originals and paraphrases (no checklist, prereg or results; not study data, no study spend).
  All six PASS, no meaning changes or connotation shifts. Minor nuances noted, none acted on:
  Q3a "proposed as one way" and Q3b "might use" vs the baseline's "could help"; Q2a SAWF "a publicly
  owned wealth fund" adds ownership (the original says "public wealth fund"; the user kept it as written, 2026-10-04); Q2c UBS "including" vs "such as". This is a Claude check of text written with
  Claude's help, not an independent model family; the user's own review stands alongside it.
- 2026-10-04 (user, TASK-35): the Claude subagent arm covers model variability only: a repeat of
  the baseline with Claude Haiku 4.5, compared with B on stability and on the distribution of
  responses; no variation battery. Written up as section 9a; the one-agent-per-call design is the implementer's choice, for review. Passes: see section 9a
  (user, 2026-10-04: one full pass plus two more over UBC only).
- 2026-10-04 (user, TASK-34): keep the conservative guard (estimate from the cap) and raise the
  ceiling in stages, in the section 8 priority order; the code ceiling changes only when the user
  edits `config.yaml` explicitly, and the account budget is topped up by the user between stages.
- 2026-10-04 (user, TASK-35 and freeze): the Claude arm runs one full pass (561 agents) plus two
  more passes over UBC only with all 51 personas (663 agents in all; section 9a); its harness
  (rater agent definition, driver code) is pinned by hash. k_R = 5 and k_Q = 3 are frozen. The
  prereg is frozen at the git tag `prereg-v1`, placed by the user.

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

## 12. Pre-freeze checklist (all settled at freezing, 2026-10-04)

1. Model id for the study: `glm-5.3-flash` on OpenCode Zen (D3 not run: no second model approved).
2. Temperature levels for R-T: set 2026-10-04 to 0.0 and 1.0 (`designs/study.yaml`; decisions log).
3. k_R and k_Q: set 2026-10-04 to the floors, k_R = 5 and k_Q = 3 (decisions log).
4. Paraphrase texts for Q2a-c and Q3a-c: written, hashed in `prompts/manifest.yaml`, reviewed by
   the user 2026-10-04, independently checked (section 10); hashes copied into section 7 on
   2026-10-04 after the user confirmed the wording.
5. `max_tokens` cap: set 2026-10-04 to 400 tokens per rating, 5,200 for a 13-rating call
   (`config.yaml`; decisions log).
6. Persona bootstrap resample count (secondary analysis): set 2026-10-04 to 2,000, seeded.
7. Adversarial-arm procedure and budget: drafted in section 9 (TASK-22); reviewed and accepted by the user
   2026-10-04 (decisions log).
8. Design file: the one-at-a-time expander exists (`domain/oat_design.py`, TASK-32; the fractional
   expander is not used). The study design file `designs/study.yaml` exists (k_R 5, k_Q 3, D3
   omitted: no second model is approved); regenerate and diff against the frozen copy before the
   full run. Equivalence check done 2026-10-04 (decisions log); paraphrase hashes are in section 7.
9. Pipeline changes: done. Named persona builder (TASK-31), templates and renderer (TASK-16), and
   job building (TASK-33): `plan` and `submit` read the one-at-a-time design file and build jobs
   in its recorded run order, with each policy's packet from `evidence/packets` (de-named for
   Q1), a per-criterion response schema, and call counts and cost per cell.

## 13. Amendments

Changes after the tag `prereg-v1` (commit 5a30367) are recorded here with date and rationale;
analyses affected are labeled post-hoc. No inference data existed at the time of any entry below.

- 2026-10-04, post-freeze red-team (fresh read-only reviewer on the locked design files; user
  directed: fix actual errors, record methodological issues as found after the freeze). Errors
  corrected, no design change: (1) section 9a Design no longer says agents use no tools; it now
  matches Tool use (one Read, one Write, nothing else); (2) section 6: M = 5 is about one-third
  of a tier width (tiers are 13-15 points wide), not one-sixth; (3) section 6: stray "(a)" label
  removed; (4) section 5 Q1 row now says labels, names and acronyms are removed while real-world
  programme names in packets are kept, as already accepted in section 10; (5) section 7: the two
  harness hash rows are sourced from `subagent_arm/manifest.yaml`, and 9a points to section 7;
  (6) stale text in companion files: `reconstruction.md` (status, TODO notes, 11 vs 12 panel
  numbers), `spec-v2-draft.md` (superseded-figures note), `designs/study.yaml` and
  `prompts/manifest.yaml` (draft and cost comments). No hashed file changed.

- 2026-10-04, user decisions on three red-team ambiguities (no design change, no data yet):
  (a) B' (the drift control) runs at the very end of the first priority unit, R: all k_R repeats
  of B first, then B'. (b) Budget checks are made per unit, in the section 8 priority order, with
  the remaining cost estimated by the code's conservative `plan` estimate against the budget left
  under the ceiling; the run is batched by unit and a unit runs whole or not at all. (c) A
  recommendation clause "flips" when its outcome differs from the published Table 4 result (the
  published data pass all four clauses), so a flip is a failed clause; B's own clause results are
  reported alongside. The drop order in section 8 (Q3, R-T, D3) is unchanged; its mismatch with
  the reverse priority order stays recorded in section 14 (A2).

- 2026-10-04, execution mechanics (user approved; no design, prompt, seed or data change): `plan` and
  `submit` gained `--cells IDS` (one-at-a-time designs only) so the section 8 priority units can run
  one at a time: it keeps only the named cells and their slots of the recorded run order, in the
  same relative order (B' stays last). Job ids do not depend on the design file, so jobs finished
  this way are skipped when the full design is run. Before this existed, the first paid study call
  (user-confirmed, 2026-10-04) submitted the first 100 jobs of the recorded run order, which are all
  cell Q3c (100 jobs, 0.17 USD actual against 0.29 estimated). Those rows are kept as study data for
  Q3c; no other cell has been run at the time of writing.

- 2026-10-05, deviation from the section 8 stopping rule (user decision, made after unit R had run
  and before any later unit; chosen on cost and priority order only, not on results). R (B x 5, B')
  finished on 2026-10-05 at 5.12 USD actual against 8.76 estimated (ratio 0.58; Q3c's first 100
  jobs gave 0.59). Spend at that point: 5.87 USD actual plus 0.13 USD in other ledgers, leaving about
  9.00 USD under the ceiling, of which 2.50 USD stays reserved for the adversarial arm (section 9).
  Under the frozen rule Q1 runs and Q2 (one unit, 14.63 USD estimated) does not fit, so the study
  would stop after Q1. Instead the priority order is walked skipping, not stopping at, units that do
  not fit, with unit costs taken as the plan estimate times the observed ratio 0.58: Q1 (about 2.85
  USD), then Q4 (about 2.70 USD), then D2 (about 0.95 USD). D2 runs only if, after Q4, actual spend
  plus D2's ratio-adjusted cost still leaves the 2.50 USD reserve; otherwise it is reported as not
  run. Q2, Q3 (apart from the 100 Q3c jobs already run, reported as a partial cell of a dropped
  unit), R-T, D2b, D1 and D3 are not run, with budget as the reason. The main study stops there.
  Reports must cite this as a post-freeze deviation: skipping Q2 means H3 rests on Q1 and Q4 alone.

- 2026-10-05, analysis amendments after the first full analysis run (user approved; TASK-37; no
  data, prompt or design change). (1) D2 missing data: D2 had 6 failed calls of 561 (ubi 3, sawf 2,
  ubc 1). The section 7 common-complete rule, as coded for persona cells, keeps a triplet only if it
  is present in every repeat, so it dropped ubi, sawf and ubc from D2 entirely and left clauses
  (a), (b) and (d) undefined there. In D2 the repeat plays the persona role (51 x 11 = 561 calls,
  one B repeat), so the analogue of the persona x policy pair is the single call: a failed D2 call
  now drops only that repeat x policy, repeat means average the surviving repeats per policy, and
  analyses that need a balanced array (variance components, the repeat-noise SE, single runs) use
  the 45 repeats with no failed call. Persona cells are unchanged; every non-D2 number in the
  reports is identical before and after. D2's results before the change (88 units, 5 beyond M; the
  clause (c) result on 8 policies) are superseded and must not be reported as primary.
  (2) Section 7 promised survivor-only means and a worst-case bound (failures imputed at 0 and at
  100) that the analysis code did not yet produce; `analyze missing` now reports them, per cell,
  for the primary materiality count and the recommendation clauses. (3) Section 12 item 6 (2,000
  resamples) is now the code default; reports no longer call it open. Both (1) and (2) were
  written after seeing results, so cite them as post-freeze analysis amendments.

- 2026-10-05, adversarial arm run (user go-ahead, TASK-24; execution only, no change to section
  9). `opencode` added to the arm's `approved_providers`. Its baseline and seed-1 rerun ran first
  (110 calls, 0.19 USD actual; one invalid reply retried and passed). The search-panel target on
  Full Transformation is UBI, not UBC. The arm's config sets 600 output tokens per rating (the
  pilot's value; config comment says "as config.yaml", which has 400), so its `max_tokens` cap is
  7,800 against B's 5,200: recorded as found, not changed, since the arm config predates any arm
  data and the cap only bounds truncation.
  The search then ran to its end (status "depth exhausted"): 27 candidates, no success, 1.97 USD
  actual; the three depth-2 candidates that first did not fit the budget waited, as section 9
  says, and ran once collected spend freed room.

- 2026-10-05, EXPLORATORY reversed-scale probe (user suggestion, TASK-38; written before any probe
  data; not part of the preregistered analysis, the adversarial arm or the Claude arm, and never
  pooled with them). Question: does the study model give the mirror image when asked to rate with
  0 = best and 100 = worst? It is not an adversarial catalogue entry, because if the model ignored
  the reversal the converted scores would push the top policy to the bottom and the arm would count
  that as a success. Design: B's persona x policy template with one sentence changed
  (`scale_probe/prompts/reversed_scale.txt`, sha256
  `1d7a319d1ff61d4dac589ca87b3c41acd2abe41047a87b559daece21a95814cd`), run once on the adversarial
  arm's 5-persona search panel with every other setting of the arm's baseline run (55 calls; own
  store, ledger and 0.30 USD ceiling inside the global cap). Raw scores are converted with 100 - x.
  Comparison: the arm's baseline run (seed 0); reference: the arm's rerun (seed 1) against the same
  baseline. Measures, all descriptive: Pearson r, mean signed and mean absolute difference of single
  ratings and of policy x criterion panel means; Table 4 units beyond M = 5; Kendall tau-b per
  composite; the arm target's rank on Full Transformation; clauses (a)-(d); and per call, "looks
  unconverted" when the raw call mean is nearer the baseline call mean m_b than 100 - m_b,
  "undecidable" when |m_b - 50| < 5. Every comparison is repeated without the unconverted calls
  (secondary). At the time of writing the arm's baseline and rerun had been collected and only its
  target (UBI) had been looked at; no probe call had been made.

## 14. Findings after the freeze (not fixed; recorded for posterity)

All of the following were found by the post-freeze red-team review of 2026-10-04, after the
prereg was frozen and before any inference data. They are not changes to the design. Reports
should cite them as limitations discovered after the freeze.

**Ambiguities left as written (the user decides before the first staged run; any resolution is
an amendment in section 13):**
- A1 (resolved in section 13, 2026-10-04). Section 5 says B' is "one more B repeat at the very end", but section 8 makes "R with B'" the
  first priority unit and a unit runs whole. The run order of B' is therefore not fixed.
- A2 (cost basis resolved in section 13: the conservative estimate; the drop order below stays open).
  Section 8 stopping rule: "precomputed unit costs" did not say whether the code's
  conservative estimate (about twice actual) or actual cost applies. The drop order (Q3, R-T, D3)
  also differs from the reverse of the priority order, so with a full plan above the ceiling Q3
  and R-T are dropped before D2, D2b and D1.
- A3 (resolved in section 13: against the published result). Section 6 did not state the reference against which a recommendation clause "flips" (the
  published pass, B's repeat-mean or R); "three durability composites" means three scenario
  criteria.
- A4. Section 7 promises replacement of failing paraphrases "under a pre-stated rule" that is not
  stated; the manifest's equivalence note says "nothing is added" while section 10 records that the
  Q2a SAWF wording adds ownership (kept by the user); the second-model check is described
  differently in the manifest ("author check") and section 10 (fresh instance).
- A5. Section 9: "the smallest success wins" and "stops at the first success" conflict, and "slot"
  is undefined in the prereg.
- A6. Section 9a pilot counts (11 of 36 first attempts failed; 3 of 7 retries) are not explained
  and were not rechecked.
- A7. The essay's feasibility columns do not map one to one onto the study's Administrative
  Capacity and Speed criterion, and no mapping rule is given for the essay comparison.

**Methodological issues (severity from the reviewer; none change the frozen design):**
- High. The 15 USD ceiling funds roughly R, B' and Q1 plus the adversarial arm; under the stopping
  rule Q2a-c and later units may never run unless the ceiling is raised, so H3 and most of Q2
  would rest on the Q1 cell alone.
- High. Staged execution in priority order breaks the claim that cells are interleaved over time:
  time is confounded with cell, B' tests drift only at the end, and the ceiling is raised between
  stages after the user has seen results.
- High. With k_Q = 3 each Q cell has three single runs (flip rates 0, 1/3, 2/3, 1). Clauses (a)
  and (b) have margins of 15.5 and 40 and will almost never flip, so H2 and the flip metric rest
  on (c) and (d). The reference band (3-run mean against the remaining 2-run mean) is wider than
  the actual contrast (3 against 5 runs) and uses only 10 overlapping splits.
- Medium. Claude arm: repeat noise is measured on UBC only (13 cells, 3 passes) against glm's 5
  repeats of all 143 cells, and the between-model shift uses one Haiku pass; a difference is a
  bundle of model, agent wrapper, changed reply format and uncontrolled sampling.
- Medium. Claude arm validity: "3 tool uses" does not show which file was read; whether subagents
  inherit the project CLAUDE.md (which describes the study) is unchecked; `rater.md` names the
  alias `haiku`, not a snapshot; calls are not reproducible by seed.
- Medium. Adversarial arm: search on 5 personas with one run per candidate, no confirmation on the
  51-persona panel, so a "strictly last place" success is exposed to winner's curse; evidence
  edits apply only to the target policy.
- Medium. Q1 and Q2: paraphrases are not guaranteed meaning-preserving (SAWF "publicly owned"),
  Q1 keeps programme names, and the equivalence checks come from the same model family that
  helped write the text; a Q1 or Q2 shift can be a meaning change, which affects H3 for SAWF and
  UBC.
- Medium. Evidence packets are uneven (Wage Insurance nearly empty; UBC rests on Baby bonds) and
  were extracted by one Claude model; cross-policy ranks and the Q4 effect are confounded with
  packet size and content.
- Medium-low. Published comparisons for Readiness and Administrative Capacity and Speed are weak
  (the essay codes Speed and Readiness by the authors); Popular Support is not rated, so the
  four-criterion feasibility composite cannot match the paper's six-criterion composite.
- Medium-low. D2 (no persona) is called an independent noise estimator but lacks persona x policy
  variance, so it need not match B's noise; D1's per-call cost is likely understated because it
  carries all 11 evidence packets.
- Low. H1 "exceeds 0.05 by a wide margin" has no threshold; the Holm family and any test for flips
  are undefined.
- Low. Repeat r uses seed base_seed + r in every cell, so if Zen honours seeds, Q and B noise may
  be correlated; R-T at T = 1.0 may equal the provider default, and reasoning models may ignore
  temperature.
- Low. Hash freezing covers prompts, paraphrases and the Claude arm harness only; policies,
  criteria, personas, evidence packets and `designs/study.yaml` are not hash-pinned, and section
  12 item 8 refers to a "frozen copy" of `study.yaml` with no recorded hash.
