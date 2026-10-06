# How stable are LLM-panel policy scores? A preregistered sensitivity study of "Economic Policy for AGI"

**DRAFT (TASK-24), 2026-10-06.** Shared with the authors on 2026-10-06. Every number below is
read from the analysis reports in `analysis/`, `subagent_arm/reports/`, `scale_probe/` and
`adversarial/`, which are regenerated from the append-only raw stores.

## Summary

We re-implemented, from its public description, the simulated-economist panel of "Economic Policy
for AGI" (Jacobs and Imas, 2026) and asked how stable its scores are. This is a re-implementation,
not a replication: the authors' prompts, persona data and literature text are not public, so ours
are stand-ins, and our absolute scores are not the paper's. Nothing in our method is new: it
applies to a policy-ranking panel what work on LLM survey responses has already shown, that small
changes in prompt wording, format and persona can move LLM answers a long way (see Related work).

- **Repeat noise is far larger than the paper's printed precision.** Running our baseline panel
  five times with identical inputs, the median standard deviation of a policy x criterion panel
  mean across runs is 0.67 points (up to 1.8; `analysis/variance/variance.md`), against the
  one-decimal (0.05-point) precision of the published tables. Rankings are nevertheless largely stable run to run, and no panel mean moved
  by more than 5 points between a single run and the mean of the others.
- **Small input changes move scores well beyond repeat noise.** Removing policy names (definitions
  only) moved 15 of 121 Table 4 panel means by more than 5 points; removing the evidence packet
  moved 19. In five repeats of the baseline, the corresponding count was 0 in every split. Removing
  names also flipped the headline rank claim that UBC leads on Full Transformation durability, in
  all three runs.
- **The 51 personas behave almost as one rater.** Persona identity explains under 1% of the
  variance of a single rating; the effective number of independent raters, by agreement across
  policies, is 1.0 to 1.4 of 51.
- **A different model moves scores much more again.** Claude Haiku 4.5 on the same prompts moved
  72 of 121 panel means by more than 5 points against our baseline model (a separate, labeled arm;
  a model-and-harness difference, not a clean model effect).
- **The recommendations held up better than the scores.** Three of the paper's four rank claims
  that we tested held in our baseline and in most variations; the fourth (NIT in the top three on
  Moderate disruption) failed in every run of every condition, including our baseline, so it
  reflects our reconstruction rather than instability.
- **A deliberate search found no top-to-bottom reversal.** The adversarial arm tried 27 small
  changes and pairs on a 5-persona panel; none moved the top policy below third of 11.

**Instability of the scores shows they lack the claimed precision, not that the recommendations
are wrong.** That caveat applies to every result in this report.

## Related work: this study applies known ideas

A growing literature uses LLMs as stand-ins for human survey respondents and shows how fragile
their answers are. We came to most of it after the preregistration was frozen, so the prereg does
not cite it, but our design is an application of its ideas to an expert policy panel rather than
a contribution to them.

- **Simulated respondents and personas.** Argyle et al. (2023, *Political Analysis*) proposed
  conditioning a language model on respondents' backstories to produce "silicon samples" of human
  subgroups. Hu and Collier (2024, ACL) found that persona variables explain under 10% of the
  variance in annotations of existing subjective NLP datasets, and that persona prompting gives
  modest gains. Our finding that persona identity explains under 1% of rating variance, and that
  51 named personas behave almost as one rater, is in line with this.
- **Sensitivity of synthetic survey data.** Bisbee et al. (2024, *Political Analysis*) found that
  persona-prompted ChatGPT reproduces average survey scores but has too little variance for
  inference, shifts under small wording changes, and gives different results to the same prompt
  months apart. Dominguez-Olmedo, Hardt and Mendler-Dünner (2024, NeurIPS) found that LLM survey
  answers are driven by ordering and labeling biases, and trend toward uniform once those are
  randomised. Röttger et al. (2024, ACL) found that models' political-survey answers change when
  the fixed-choice format is relaxed and are not robust to paraphrase.
- **Perturbations and response biases.** Tjuatja et al. (2024, TACL) found that LLMs generally do
  not show human-like response biases in survey design, yet are sensitive to perturbations that do
  not move human answers. Rupprecht, Ahnert and Strohmaier (2026, NLP+CSS workshop) applied ten
  perturbations of question phrasing and answer structure to World Values Survey items across nine
  models and found sensitivity to paraphrasing and combined perturbations, and a recency bias
  toward the last-listed option. Outside surveys, Sclar et al. (2024, ICLR) showed that formatting
  changes alone can move few-shot accuracy by up to 76 points.
- **Tooling.** QSTN (Kreutner et al., 2026, EACL system demonstrations) is an open-source framework
  for exactly this kind of work: questionnaire presentation, prompt perturbations and response
  generation methods as modular, swappable parts, evaluated on more than 40 million generated
  responses. It would have been a natural basis for this study had we known it at the start.

What this study adds is narrow: the same checks (repeat runs, one-at-a-time input changes, a
second model, a bounded worst-case search), preregistered and applied to a published expert-panel
ranking whose recommendations are stated as rank claims, so that score instability can be weighed
against whether those claims change.

## 1. What we did

**Re-implementation from the public description.** The paper's panel is 51 simulated economists,
modelled on named members of the Clark Center (IGM) panel, each scoring 11 redistributive
policies on 0-100 criteria after reading a policy description and "extensive literature reviews".
The paper reports panel means to one decimal and does not report the model, temperature, prompt
text, literature text or number of runs. We rebuilt the setup from the paper and essay
(`prereg/reconstruction.md` lists every choice):

| Element | Paper | Ours (stand-in where marked) |
|---|---|---|
| Raters | 51 named economists (Appendix A, Table 7), with biographies, research histories and actual IGM responses | the same 51 names, institutions and fields; the model's own knowledge of each person fills the rest (stand-in) |
| Policies | 11 redistributive policies, Table 3 names and definitions | the same |
| Criteria | 11 Table 4 criteria (plus Political Support and Administrative Capacity and Speed in the essay) | the same 13, Table 1 wording; Implementation Readiness has no Table 1 definition, so its wording is ours |
| Evidence | "extensive literature reviews" | one packet per policy of verbatim excerpts from pinned English Wikipedia revisions (stand-in) |
| Prompt | not published | our wording, one persona x one policy per call, all 13 criteria in one JSON reply (stand-in) |
| Model | not stated | `glm-5.3-flash` on OpenCode Zen, provider-default temperature (stand-in) |
| Aggregation | panel means | unweighted mean over personas; composites as unweighted means of criteria |

**Preregistration.** The design, metrics, stopping rules and analysis were frozen in
`prereg/prereg.md` (git tag `prereg-v1`, 2026-10-04) before any study data. Every later change is
recorded with its date and reason in prereg section 13, and the ones made after seeing results are
labeled post-hoc below. Every run is logged, failures included, in an append-only store; analysis
reads only from it.

**Design.** One-at-a-time variations from the baseline B, each changing one input, on the same 51
personas:

- **Block R (repeat noise):** B run 5 times (2,805 calls), plus one more run at the end (B') as a
  provider-drift check.
- **Block Q (small variations, 3 runs each):** Q1, policy names removed (definitions and neutral
  codes only); Q4, no evidence packet; Q2 and Q3 (paraphrased definitions and instructions) were
  planned.
- **Block D (design changes, read separately):** D2, no persona at all (51 runs of 11 calls).

**What ran, and what did not.** The budget was a hard 15 USD, enforced in code. After block R the
preregistered stopping rule would have stopped the study after Q1, because Q2 did not fit. Before
any later unit ran, and on cost and priority alone, we amended the rule (prereg s13, 2026-10-05) to
skip units that do not fit rather than stop at them. Run: R (B x5, B'), Q1, Q4, D2, and 100 calls
of Q3c (one instruction paraphrase; a partial cell, 10 personas). Not run, for budget: Q2a-c, the
rest of Q3, the temperature cells R-T, D2b (synthetic personas), D1 (joint scoring) and D3 (a
second API model). This is a post-freeze deviation: in particular, the label hypothesis H3 rests
on Q1 and Q4 alone, without the paraphrase cells.

| Cell | Change | Calls ok / failed |
|---|---|---|
| B | baseline, 5 runs | 2,803 / 2 |
| B' | baseline repeated at the end | 561 / 0 |
| Q1 | policy names removed | 1,683 / 0 |
| Q4 | no evidence packet | 1,683 / 0 |
| Q3c | instruction paraphrase (partial: 100 calls) | 100 / 0 |
| D2 | no persona (design change) | 555 / 6 |

Main-study spend: 11.95 USD; with the pilots, the adversarial arm (1.97) and the probe, 14.14 of the 15 USD ceiling. All failure rates were under 2%. Under survivor-only means and under
imputation of every failed call at 0 and at 100 (`analysis/missing/missing_data.md`), every clause
result is unchanged and the counts of shifted panel means change by at most one (Q1 15 to 16, Q4
18 to 19), except the partial Q3c cell (2 to 4) and D2 (8 to 15).

## 2. Results: the full range

Every cell that ran is reported, with ranges across all cells, not only the largest changes.
Numbers are from `analysis/` (materiality, recommendations, ranks, variance, missing).

### 2.1 Repeat noise (Q1 of the study: same inputs, run again)

- **Precision (H1, holds).** The median SD of a Table 4 panel mean across B's five runs is 0.67
  points (minimum 0.12, maximum 1.79; range across runs up to 4.8). The paper's tables print one
  decimal.
- **Materiality.** Comparing any split of B's runs (one run against the other four, or three
  against two), 0 of 121 Table 4 panel means moved by more than M = 5 points. B' (run last) moved
  0, with a maximum shift of 2.9, so we see no provider drift.
- **Ranks.** Kendall tau between two single B runs: median 0.91 to 1.00 by composite, minimum
  0.88 (Moderate disruption, where several policies are near-tied).
- **Recommendation clauses (H2, holds).** Clause (a), UBC first on Full Transformation durability,
  failed in 1 of 5 single B runs: its margin in B's mean is 3.1 points, against 15.5 in the paper.
  Clauses (b) and (d) held in every run; clause (c) failed in every run (section 2.4).

### 2.2 Small variations (Q2 of the study)

Table 4 panel means moved by more than M = 5 points from B (121 units), with B's repeat-noise
reference for the same number of runs:

| Cell | Change | Runs | Beyond M = 5 | B split band | Beyond 3 / 8 | Largest shift |
|---|---|---|---|---|---|---|
| B' | drift check | 1 | 0 | 0 to 0 | 0 / 0 | 2.9 |
| Q1 | names removed | 3 | 15 | 0 to 0 | 36 / 6 | 14.5 |
| Q4 | no evidence | 3 | 19 | 0 to 0 | 38 / 1 | 8.9 |
| Q3c | instruction paraphrase (partial) | 1 | 2 | 2 to 7 | 21 / 0 | 6.8 |
| D2 | no persona (design change) | 51 | 12 | n/a | 30 / 2 | 10.6 |

- **Removing names (Q1)** moved Directed Industrial Policy on 9 criteria (up to +14.5 on
  Democratic Voice), NIT's Implementation Readiness by -12.5 and UBS's Full Transformation score by
  +10.6. Its policy-specific shifts are 21 times the repeat-noise variance. Ranks moved below B's
  repeat band on every composite (tau 0.75 to 0.93). With names removed, UBI rather than UBC led on
  Full Transformation, so clause (a) failed in all 3 runs (margin -3.0).
- **Removing evidence (Q4)** moved 19 units, mostly by 5 to 9 points, spread over SAWF, Directed
  Industrial Policy, UI and others. All four clauses kept their baseline result.
- **The instruction paraphrase (Q3c)** is a partial cell of 10 personas and one run; its 2 units
  beyond M sit inside the band of a single B run against the rest (2 to 7), so it shows nothing
  beyond noise.
- **Labels (H3, mixed).** Removing names moved 15 units beyond M, but not the pair the hypothesis
  named: the gap between UBC and SAWF on Ownership of Gains narrowed from 3.0 to 0.2 points (UBC
  -1.8, SAWF +1.0, both within M). In our baseline that gap is already 3.0 points, against 40.0 in
  the paper.
- **Recommendations across cells.** Over the five non-baseline cells, the repeat-mean margin of
  clause (a) ranged from -3.0 to 7.2, of (b) from 0.2 to 4.6, of (c) from -15.3 to -11.9 and of
  (d) from 2.8 to 7.5. The three-stage sequence (UI/EITC, then NIT, then UBC) never held, because
  clause (c) never held.

### 2.3 Panel independence (H4, holds)

In B, persona terms explain 0.9% of the variance of a single rating; repeat noise explains 7.3%;
which policy and which criterion explain 91.8%. Two personas' ratings of the same criterion across
policies agree almost perfectly (icc 0.70 to 0.98), so the effective number of independent raters
is 1.0 to 1.4 of 51. Removing the personas altogether (D2) moved 12 panel means by more than M and
left every clause's repeat-mean result unchanged, though single no-persona runs flipped clause (a)
in 18 of 45 runs and (d) in 26 of 45.

### 2.4 Comparison with the published tables (supporting only)

Our baseline agrees with Table 4 on ranks for some criteria and not others: Kendall tau 0.75 on
Implementation Readiness, 0.71 on Full Transformation and on the Feasibility composite, 0.64 on
Ownership of Gains, but near zero or negative on Meaning and Human Value (0.02) and Economic Agency
(-0.09). Mean absolute differences are 7 to 24 points. This comparison cannot separate our
reconstruction from instability, and agreement would not validate it: Table 4 has many round
values that a mean of 51 continuous scores rarely produces. Clause (c) failing in every run is the
clearest reconstruction gap: in our baseline UBC, not NIT, leads on Moderate disruption.

### 2.5 A second model (separate arm, not pooled)

To show how much depends on the model, we ran the baseline once with Claude Haiku 4.5 as Claude
Code subagents (prereg s9a; 561 calls, plus two more passes over UBC only). This arm is labeled
separately and never pooled with the analysis above. A difference here is a difference between two
model-and-harness bundles (model, agentic wrapper, reply format, uncontrolled sampling), not a
clean model effect (`subagent_arm/reports/claude_vs_b.md`).

- 72 of 121 Table 4 panel means differ by more than 5 points between Claude's single pass and our
  baseline's five-run mean, against 0 when a single baseline run is compared with the other four.
  Claude scores higher almost everywhere (UBC: +20.8 on Standards of Living, +13.5 on Full
  Transformation), while each model's own repeat SD on UBC is 0.1 to 1.5 points.
- Rank agreement with the baseline is tau 0.24 to 0.93 by composite, against a minimum of 0.88
  between two baseline runs.
- The recommendation clauses come out the same as in our baseline: (a), (b) and (d) hold, (c)
  fails; (a) and (b) hold in all three Claude passes over UBC.

### 2.6 Reversed scale (exploratory, not pooled)

A post-freeze exploratory probe (prereg s13, TASK-38; `scale_probe/report.md`) changed one sentence
of the baseline prompt so that 0 is best and 100 is worst, ran it once on a 5-persona panel (55
calls), converted the scores with 100 - x and compared them with the same panel's normal run. A
second normal run at another seed is the noise reference.

- The model followed the reversed scale: raw scores correlate -0.91 with the normal run, and 1 of
  36 classifiable calls looks unconverted (19 calls sat too close to 50 to classify).
- After conversion, scores are 1.5 points lower on average, and 32 of 121 panel means differ from
  the normal run by more than 5 points, against 12 for the second normal run. Rank agreement is
  similar to the second run's (median tau 0.85 against 0.88). All four clauses kept the normal
  run's result.
- Read with care: one run of 5 personas per condition, where single ratings swing 15 to 30
  points between runs. It shows that the direction of the scale matters somewhat beyond noise, not
  how much.

## 3. Adversarial arm (separate, labeled; not pooled with the main analysis)

**ADVERSARIAL.** A pre-specified, bounded search (prereg s9; `adversarial/report.md`) for the
smallest plausible change that moves the top policy on Full Transformation durability to last
place. It is a worst-case search by design, not an estimate of stability. It used a 5-persona
search panel, one run per candidate, a fixed 14-entry catalogue (five one-sentence wording edits,
four edits of the target's evidence packet, dropping the persona most favourable to the target,
temperature 0 or 1, two criterion orders), greedy combinations up to depth 2 and its own 2.50 USD
budget (1.97 USD spent).

- **Target.** In the search panel's baseline run the top policy was UBI (mean 59.4), not UBC. That
  run is itself noisy: all five personas rated UBC 15 to 30 points lower there than in the arm's
  seed-1 rerun, in which UBI is already second. The target rests on one 5-persona run, the
  winner's-curse risk recorded in prereg s14.
- **Result.** None of the 27 candidates (14 single changes, 13 pairs) moved UBI to last place. The
  largest move was to third of 11: from the wording edit "does better" to "performs better", from
  dropping the last excerpt or reversing the excerpts of UBI's evidence packet, and from several
  pairs built on the wording edit. A rerun with no change at all moved it to second. The search
  stopped at depth 2, as preregistered, after 27 of the 30 allowed candidates.
- **Reading.** Within this catalogue, top-to-bottom reversals did not occur; movements of one or
  two places near the top are of the same size as repeat noise on a 5-persona panel. The search
  covers only the listed edits, applied to one target on a small panel, so it does not show that
  no small change could reverse a ranking.

## 4. Limitations

- **Instability does not show the recommendations are wrong.** Scores that move under repeats or
  small input changes lack the precision the published tables imply; that says nothing about
  whether UBC, NIT or UI are good policy for each scenario. Several of the paper's rank claims held
  across most of our conditions despite score shifts far larger than the printed precision.
- **Re-implementation, not replication.** Personas, evidence, prompts and model are our stand-ins,
  so absolute levels are not the paper's and any gap to the published tables mixes reconstruction
  with instability.
- **One cheap model.** The main results are conditional on `glm-5.3-flash`; the Claude arm shows
  that the model choice alone moves scores far more than any variation we tested. Zen serves model
  ids the provider can repoint; the reported id was checked on every row and never changed, which
  does not rule out a silent change behind the same id.
- **Not every planned cell ran.** The paraphrase cells (Q2, most of Q3), temperature, synthetic
  personas, joint scoring and a second API model were not run (budget; prereg s13). One-at-a-time
  variations cannot show interactions.
- **Staged runs.** Cells ran in priority order, not interleaved over time, so time is confounded
  with cell; B' at the end showed no drift.
- **Uneven evidence.** Packets from Wikipedia are uneven across policies (Wage Insurance is nearly
  empty; UBC rests on Baby bonds), so cross-policy ranks and the no-evidence effect are partly
  about packet content.
- **No human anchor.** We did not survey human economists. A small survey of real economists on a
  subset of the policies and criteria would anchor the panel's levels and show whether the panel's
  sensitivity to names and evidence is larger than human raters'. We note it as a possible next
  step; it was not done here.
- **Post-freeze changes.** The stopping-rule deviation, the D2 missing-data rule, the survivor-only
  and worst-case views, and the reversed-scale probe were all added after the freeze (prereg s13);
  the post-freeze red-team findings are in prereg s14.

## References

- Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C. and Wingate, D. (2023). Out of
  One, Many: Using Language Models to Simulate Human Samples. *Political Analysis*.
- Bisbee, J., Clinton, J. D., Dorff, C., Kenkel, B. and Larson, J. M. (2024). Synthetic
  Replacements for Human Survey Data? The Perils of Large Language Models. *Political Analysis*.
- Dominguez-Olmedo, R., Hardt, M. and Mendler-Dünner, C. (2024). Questioning the Survey Responses
  of Large Language Models. *NeurIPS 2024*.
- Hu, T. and Collier, N. (2024). Quantifying the Persona Effect in LLM Simulations. *ACL 2024*.
- Jacobs and Imas (2026). Economic Policy for AGI. SSRN, 15 September 2026.
- Kreutner, M., Rupprecht, J., Ahnert, G., Salem, A. and Strohmaier, M. (2026). QSTN: A Modular
  Framework for Robust Questionnaire Inference with Large Language Models. *EACL 2026 System
  Demonstrations*. arXiv:2512.08646.
- Röttger, P. et al. (2024). Political Compass or Spinning Arrow? Towards More Meaningful
  Evaluations for Values and Opinions in Large Language Models. *ACL 2024*.
- Rupprecht, J., Ahnert, G. and Strohmaier, M. (2026). Prompt Perturbations Reveal Human-Like
  Biases in Large Language Model Survey Responses. *Seventh Workshop on NLP and Computational
  Social Science*. arXiv:2507.07188.
- Sclar, M., Choi, Y., Tsvetkov, Y. and Suhr, A. (2024). Quantifying Language Models' Sensitivity to
  Spurious Features in Prompt Design. *ICLR 2024*.
- Tjuatja, L., Chen, V., Wu, T., Talwalkar, A. and Neubig, G. (2024). Do LLMs Exhibit Human-like
  Response Biases? A Case Study in Survey Design. *TACL* 12.

## 5. Data and code

Code, prereg, prompts, evidence packets and analysis reports are in this repository. Raw model
responses are kept locally for now; redistribution is decided after checking the provider's terms.
Results are reported in aggregate only, never per named economist.
