# Study design spec v2.1 (folded into prereg.md on 2026-10-04)

**STATUS: FOLDED.** The design below was accepted by the user and now lives in `prereg.md`, which
governs; `reconstruction.md` holds the stand-ins. This file is kept as the record of the proposal
and as the home of the red-team resolution log (section 10). Basis: the SSRN paper (Jacobs and
Imas, 15 Sep 2026, `docs/economic-policy-for-agi-ssrn.pdf`).

## 1. Questions

The paper reports panel-mean scores to one decimal, with no model, temperature, repeat count or
prompt text, and concedes results cannot be replicated exactly "even with identical prompting".

- **Q1 (repeat stability).** Rerun the same panel with identical inputs: how much do scores,
  ranks, tiers and the headline recommendation move?
- **Q2 (small variations).** How much do they move when a small, defensible input detail changes,
  chiefly replacing policy names with the policy descriptions, relative to Q1?

Not goals: reproducing the published numbers, or judging whether the recommendations are right.
Instability of scores shows they lack the claimed precision, not that the recommendations are
wrong. This sentence accompanies every headline claim in the write-up, not only this section.

## 2. Inference target and uncertainty (fixed first)

- **Target population: the 51 fixed personas.** They are a fixed design, not a sample of
  economists. The primary uncertainty is **repeat variance**: would the same panel give the same
  answer again. Both Q1 and Q2 are answered against it.
- A persona bootstrap ("would other personas agree") is **secondary**, reported only as a
  generalisation caveat, never mixed into a Q1/Q2 comparison.
- **Single-run metrics are reported alongside repeat-mean metrics.** The paper's situation was
  effectively one run, so the single-run flip rate is the practically relevant number.
- Repeat noise is modelled once: persona x policy x criterion ratings with a repeat-level variance
  fitted from block R, propagated to panel means. Effects are reported in score units and as a
  multiple of the repeat-noise standard error of a panel mean.
- The reference band for "what repeats do" is the contrast of a 3-run mean against the remaining
  5-run mean over R's splits (size-matched to V-vs-B). It is a **descriptive band, not a test**:
  the splits overlap and are not independent.

## 3. Baseline configuration B

Items marked (inf) are our inference from the paper, not stated by it.

- **Unit of call (inf):** one persona x one policy, all criteria returned in one JSON object (score
  0-100 + one-sentence rationale each). The paper says 51 x 25 = 1,275 evaluations "across
  multiple dimensions" (Figure 2), which supports a persona-by-policy unit; "all criteria in one
  JSON" is our reading. 51 x 11 = 561 calls per configuration-repeat.
- **Policy presentation:** the policy's Table 3 name **and** definition.
- **Policies:** the paper's 11 redistributive policies. The paper also scores 14 revenue and
  governance mechanisms (25 in total) on a different rubric; they are out of scope.
- **Criteria:** all 13 panel criteria in the paper's Table 4 / Appendix B: Standards of Living,
  Meaning, Macro Stabilisation; Economic Agency, Ownership, Democratic Voice; Economic Feasibility;
  Implementation Readiness; Mild, Moderate, Full Transformation. Plus Political Support and
  Administrative Capacity and Speed (named in Table 1 but not reported in Table 4; essay only).
  Popular Support is survey data in the paper and is not rated. Wording follows paper Table 1.
  Readiness carries an unexplained dagger on every Appendix B profile (no footnote exists in the
  paper); the essay calls it "author-coded". We rate it, and its published comparison is
  lower-confidence.
- **Evidence (inf; user decision 2026-10-04):** the paper says agents are "prompted with extensive
  literature reviews"; it does not say whether the text was identical across personas, or what it
  said. We use one fixed packet per policy, identical across personas, taken from a single
  third-party source (Wikipedia, pinned by revision ID with fetch date logged) so we do not write
  the evidence ourselves.
  - **Evidence only.** A packet holds what the source says exists empirically: studies, pilots,
    programme outcomes, measured effects, figures, and documented criticisms backed by data. It
    excludes definitions, history, philosophy, advocacy and commentary. Scenario framing is not
    evidence and stays in the criterion definitions, not the packet.
  - **Selection rule fixed before any article is read for content:** verbatim excerpts only, no
    model rewriting; section types included and excluded are listed in advance; the policy-to-article
    mapping (with stand-in articles for UBC and Sovereign AI Fund / Dividend) is fixed in advance.
    Policies whose article has little or no evidence get a short or empty packet, with a note saying
    so. Unequal evidence is a real property of the sources, so packets are not padded or trimmed to
    equal length; token count per packet is recorded and its association with scores is reported.
  - **Public.** Packets are published for inspection with revision links and CC BY-SA attribution
    (share-alike applies to the excerpts).
- **Personas (user decision 2026-10-04: match the paper):** 51 named economists from the paper's
  Appendix A, Table 7 (name, institution, primary field). The paper's EDSL personas also drew on
  biographies, research histories and each economist's actual IGM survey responses; we do not
  have those, so ours are name + institution + field, and the model's memorised knowledge of each
  person supplies the rest. This is a stand-in for the paper's personas, stated wherever used.
  Discrepancy: the paper's text (line 453) names John Cochrane as a modelled economist, but he is
  not in the 51-row Table 7; we use Table 7 and record the mismatch. Our synthetic trait panel
  becomes a variation (D2b).
- **Model:** one cheap pinned study model on OpenCode Zen, provider-default temperature (recorded,
  and measured in the pilot).
- **Aggregation:** unweighted mean over personas; composites as unweighted mean of sub-criteria.

## 4. Design

One-at-a-time from B, in three blocks. Not a fractional factorial: it would spread a small budget
too thin to separate effects from noise.

**Block R: noise floor (Q1).** B repeated k_R times; plus **R-T**: B at temperature 0 and one higher
level (the noise level itself, so it belongs to Q1, not Q2); plus **B'**: one more B repeat run
at the very end as a provider-drift control.

**Block Q: small variations (Q2), each k_Q repeats, nothing else changed:**

| Cell | Change |
|---|---|
| Q1 description-only | name removed everywhere (prompt, evidence packet, rationale labels use neutral codes P1..P11); the definition is the only identifier |
| Q2a-c description wording | three meaning-preserving paraphrases of the Table 3 definitions |
| Q3a-c instruction wording | three paraphrases of the instruction/rubric text (existing `para_*` templates, adapted) |
| Q4 evidence | no packet (the "none" level; an alternate packet is not currently planned) |

**Block D: design changes (Q2', reported separately, not "small variations"):** D1 joint scoring,
all 11 policies in one prompt per persona x criterion (612 calls per repeat); D2 no persona (11
policies x many repeats, 11 calls per repeat; also an independent noise estimator); D2b our
synthetic trait panel in place of named economists; D3 a second pinned model, if budget allows.

All cells use the same 51 personas (paired). Run order is randomised and cells and repeats are
interleaved across time. If Zen ignores `seed` (to be checked in the pilot), repeats are not
reproducible by seed, which is logged.

## 5. Metrics

**Primary (fixed in advance), per Q cell and for each R-T cell versus B:**

1. **Flip counts relative to R:** (a) the four recommendation-survival clauses (below), each as
   flipped/not in each single run and in the repeat-mean; (b) tier changes among the paper's tiers
   for the composites reported in Table 4; compared with the same flip rates in R.
2. **Materiality shifts:** number of policy x criterion panel means whose |shift| from B exceeds
   the pre-set margin **M = 5 points** (about one-sixth of a tier width and an order of magnitude
   above the paper's one-decimal precision; the margin is set now, not from data), reported with
   the repeat-noise multiple.
3. **Rank metrics (secondary, but reported for every cell because the paper makes its
   recommendations by rank order):** Kendall tau on the three durability composites and on each
   dimension composite between V and B; per-policy rank shift; top-3 and bottom-3 set changes.
   Rank is secondary to flips because tau moves only when near-ties swap and Table 4 has many
   near-ties (UBC 66.0 vs UI 65.9 on Moderate; three scores exactly 65.0 on Full Transformation).
   Ties are broken by average rank, a rule fixed now.

Holm correction applies to the primary set only, and only if inference language is used. All else
(each criterion x cell, descriptive heatmap, variance decomposition) is descriptive and
unthresholded; exploratory results are labelled as such.

**Recommendation-survival clauses.** These restate the paper's own claims, with cut-offs chosen
from Table 4; the published data pass them, so the baseline is not a test of the paper. Reported
with the continuous margin (score gap to the next policy) per clause:
(a) UBC rank 1 on Full Transformation durability (published margin 15.5);
(b) UBC rank 1 on Ownership of Gains (margin 40.0);
(c) NIT in the top 3 on Moderate durability (published rank 2; margin to rank 4 is 3.8);
(d) UI and EITC both in the top 4 on Mild durability (published ranks 3 and 4; EITC margin 5.9) and
both below UBC on Full Transformation durability.
The paper's Mild-scenario recommendation also names employer-led retraining; ALMP scores 42.5 on
Mild in Table 4, so the published data do not support that part. It is excluded from the clauses
and reported as such, not silently dropped.
Also: the paper's r(public net approval, Full Transformation durability) = -0.57 (published
approvals are fixed inputs; recomputed -0.569) and r(Readiness, Full Transformation durability)
= -0.51, recomputed per cell.

**Secondary descriptives:** persona-level SD across repeats and the effective number of raters
(panel-mean variance vs the independence benchmark); within-call correlation among criteria
(halo); variance decomposition with persona x policy crossed random effects and cells as fixed
effects.

**Comparison target:** the paper's Appendix B per-policy profiles (the same 12 numbers as Table 4,
one block per policy) are the clearest statement of what each persona-by-policy evaluation
returns, so our JSON output schema and the comparison table mirror them (Political Support and
Administrative Capacity and Speed appear only in the essay).

**Baseline vs published (supporting only):** rank agreement of B with Table 4 and the essay. Table
4 has many round values (65.0 three times, 50.0, 27.0, 30.0, 78.0, 68.0) that a mean of 51
continuous scores would rarely produce, so the aggregation or hand adjustment in the paper is
uncertain, and exact agreement is not meaningful.

## 6. Data validity rules

- **Pilot first (about 20 jobs; excluded from inference)** must measure: mean input, output and
  reasoning tokens per call and the cost per configuration-repeat at Zen's price for the exact
  model id; failure and truncation rate; whether temperature and seed change outputs; the
  provider-default temperature behaviour; the model id reported per response.
- **Failures and truncation.** A `max_tokens` cap is set from the pilot so truncation is rare.
  Truncation or reasoning exhaustion counts as failure. Comparisons between cells use the
  **common-complete** persona x policy set (primary); survivor-only means are secondary; a
  worst-case bound (failures imputed at 0 and 100) is reported. A cell above 10% failures is
  analysed on the common-complete set and flagged. Retry-once is logged per row.
- **Paraphrase integrity.** Paraphrase texts are frozen by hash before the pilot; meaning
  equivalence is checked by a second model and by the user's review; paraphrases that fail are
  replaced under a pre-stated rule before any data run, never afterward.
- **Drift control.** Model id reported per response is tabulated per cell; B' tests for drift.
- No cell is added, dropped or re-run after seeing results.

## 7. Budget and priority

Ceiling 15 USD (code-enforced). **k_R and k_Q are not frozen yet**: they are set from the pilot's
measured cost, with an indicative floor of k_R >= 5 and k_Q >= 3. What is frozen: the priority
order and the stopping rule. Order: R (with B'), Q1, Q2a-c, Q4, Q3a-c, R-T, D2, D1, D3. The next
block runs only if its precomputed cost fits under the ceiling. Unrun cells are reported as not
run. If too expensive, drop Q3, R-T and D3 first.

## 8. Pending user decisions

1. Named personas: **decided yes** (2026-10-04). Handling rule proposed, needs your OK: results
   are reported only in aggregate, never per named economist, and no rationale text attributed to
   a named person is published (these are living people and the outputs are model fabrications).
   Reporting rule approved by the user 2026-10-04.
2. Materiality margin M = 5 and the primary set in section 5: approved 2026-10-04. The user
   called the margin somewhat arbitrary but acceptable; it is kept and the rank metrics are
   reported alongside as the paper's own decision basis. Sensitivity of conclusions to M (e.g. 3
   and 8) is shown descriptively, not used to pick M.

## 9. Known weaknesses stated up front

- Personas, evidence packet and prompts are our stand-ins; absolute levels are not the paper's.
- One cheap model unless D3 runs; conclusions are conditional on it.
- 51 synthetic personas on one model are not 51 independent raters (effective number reported).
- One-at-a-time cannot show interactions.
- Criteria are scored together within a call; criterion-level results are conditional on that.

## 10. Red-team resolution log

| # | Finding | Resolution |
|---|---|---|
| 1 | Null does not match V-vs-B contrast | Replaced by a variance model plus a size-matched 3-vs-5 band from R, called descriptive (s2) |
| 2 | "Beyond noise" is near-vacuous; tau is weak | Materiality margin M and flip counts are primary; tau secondary (s5) |
| 3 | Mixed uncertainty sources | Target is the fixed panel; repeat variance primary; persona bootstrap secondary; single-run alongside (s2) |
| 4 | Multiple comparisons | Primary set fixed; Holm only there; rest descriptive (s5) |
| 5 | Temperature, seed, drift unmeasured | Pilot measures them; randomised interleaved order; B'; V7 moved to R-T (s4, s6) |
| 6 | Failures bias | Max-tokens cap, common-complete primary, bounds (s6) |
| 7 | Survival rule post-hoc, margins thin | Declared as the paper's claims restated; margins reported; ALMP gap stated (s5) |
| 8 | Fidelity overstated | (inf) labels added; 25-policy note; Readiness rated, with the dagger described precisely; round-number caveat. **Rejected in part:** the critic said it found no Readiness dagger; the rendered PDF page 36 shows it on every Appendix B profile, with no footnote |
| 9 | V1 ambiguity, paraphrase drift, packet circularity, V5/V6/V8 not small | B defined as name + definition; packet de-named in Q1; paraphrases frozen and checked; D block separated; D2 made cheap (s3, s4, s6) |
| 10 | Budget unsubstantiated | k not frozen; pilot first; priority and stopping rule frozen (s7) |
| 11 | Variance decomposition fragile | Crossed random effects, cells fixed, descriptive (s5) |
| 12 | Persona fidelity | Named personas adopted per user; synthetic panel kept as D2b; effective raters reported (s3, s4, s5) |
| 13 | Wording | Caveat accompanies every headline claim (s1) |
