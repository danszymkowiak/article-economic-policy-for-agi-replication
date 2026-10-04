# Reconstruction of the setup from the public paper and essay

**STATUS: DRAFT.** Companion to `prereg.md`; frozen together with it. This study is a
**re-implementation from the public description, not a replication**. The authors released no
prompts, persona data, survey responses or literature text. Everything below is either taken from
the paper or essay (marked *paper*, *essay*) or is our own stand-in (marked *stand-in*). No
stand-in is the authors' original, and write-ups must say so wherever one is used.

Sources:
- *paper*: "Economic Policy for AGI", Jacobs and Imas, 15 Sep 2026 (SSRN version in
  `docs/economic-policy-for-agi-ssrn.pdf`, added 2026-10-04). It has the methods, the full tables
  and the persona roster, and governs where it differs from the essay.
- *essay*: the DeepMind Institute essay of 2026-09-16 (snapshot in
  `docs/economic-policy-for-agi.html`, retrieved 2026-10-03). Same numbers; it alone reports the
  Political Support, Administrative Capacity and Speed scores.

## 1. What the paper and essay tell us

| Item | What they say |
|---|---|
| Raters | 51 simulated economist personas modelled on named U.S. panelists of the Clark Center (formerly IGM) panel; the roster of 51 names is in the paper's Appendix A, Table 7 (*paper*). EDSL builds each persona from biographical traits, institutional affiliations, research histories and the person's actual IGM survey responses (*paper*) |
| Input per rating | each agent receives a policy description, relevant economic literature and a structured scoring rubric (*paper*, Figure 2); 51 personas x 25 policy proposals = 1,275 structured evaluations returning a 0-100 score and a rationale |
| Aggregation | panel means over the 51 personas (*paper*) |
| Scale | 0 to 100 per criterion; composites per dimension; score tiers (High >= 70, Moderate 55-69, Mixed 42-54 or 40-54, Low < 42 or < 40) (*essay*) |
| Public support | measured by a separate survey of 2,019 Americans (net approval), not rated by agents (*paper*) |
| Not stated | model, temperature, number of runs, prompt text, literature text, whether the literature was identical across personas; "it is impossible to perfectly replicate results, even with identical prompting" (*paper*) |
| Published targets | Table 4 and Appendix B (12 panel numbers per policy plus net approval); the essay's tables add the Political Support and Administrative Capacity and Speed columns |

## 2. Policies (*paper* Table 3; essay uses near-identical definitions)

Eleven redistributive policies. Panel A, targeted and work-conditioned: EITC; Unemployment
Insurance (UI); Active Labour-Market Policies (ALMP); Wage Insurance; Directed Industrial Policy;
Federal Jobs Guarantee (FJG). Panel B, universal floors, services and ownership: Universal Basic
Income (UBI); Negative Income Tax (NIT); Universal Basic Services (UBS); Universal Basic Capital
(UBC); Sovereign AI Fund / Dividend (SAWF).

Choice: the Table 3 names and definitions are the *named* labels. The paper also scores 14 revenue
and governance mechanisms (25 proposals in total) on a different rubric; they are out of scope.
Status: decided.

## 3. Criteria (*paper* Table 1, Table 4 and Appendix B; essay for two columns)

| Dimension | Criteria rated by the panel |
|---|---|
| Welfare and Macroeconomic Resilience | Standards of Living; Meaning and Human Value; Macroeconomic Stabilisation |
| Economic Agency and Democratic Empowerment | Economic Agency and Mobility; Ownership of Gains; Democratic Voice |
| Feasibility and Implementation | Economic Feasibility; Implementation Readiness (daggered); Political Support and Administrative Capacity and Speed (essay columns only) |
| Durability Across Scenarios | Mild Disruption; Moderate Disruption; Full Transformation |

Popular Support is survey data in the paper and is not rated by us. The operational definitions
follow paper Table 1 and the scenario definitions follow Figure 1. The essay's naming differs
(Economic Participation, Broad Displacement, AGI Transformation, Speed and Readiness as separate
columns); the paper's names are used.

Readiness carries a † on every Appendix B profile but the paper has no footnote for it; the essay
calls Speed and Readiness "author-coded". We rate Readiness with the agents and treat its
comparison with the published numbers as lower-confidence. Status: decided.

`designs/inputs/criteria.yaml` holds these 13 rated criteria (the 11 Table 4 columns plus Political
Support and Administrative Capacity and Speed), with Table 1 names and descriptions and the Figure 1
scenario definitions, reviewed by the user 2026-10-04. Implementation Readiness has no Table 1
definition; its description is our wording, built from the paper's own phrases. Status: decided.

## 4. Choices we must make ourselves (stand-ins)

| # | Choice | Decision | Basis | Status |
|---|---|---|---|---|
| R1 | Unit of one call | one call per persona x policy, all criteria returned in one JSON object, policies scored independently (51 x 11 = 561 calls per configuration-repeat) | paper Figure 2 (51 x 25 evaluations "across multiple dimensions"); "all criteria in one JSON" is our reading | decided |
| R2 | Persona representation | a traits dictionary rendered in EDSL's format as `Your traits: {...}` after "You are answering questions as if you were a human. Do not break character." (section 5) | EDSL's default rendering | decided |
| R3 | The 51 baseline personas | the 51 named economists of paper Appendix A Table 7, with traits limited to name, institution and primary field; the model's memorised knowledge supplies the rest. John Cochrane is named in the paper's text but is not in Table 7, so he is excluded | user decision 2026-10-04 (match the paper); the biographies and IGM responses the paper used are not available | decided; builder to write |
| R3b | Synthetic personas | our 51 synthetic trait personas (`designs/inputs/personas/reconstructed.yaml`, section 4a) are kept as variation D2b only | earlier design | decided |
| R4 | Evidence packet | one verbatim, evidence-only packet per policy from pinned English Wikipedia revisions, two LLM extraction passes (union), section 4b; the "none" level is the Q4 variation | the paper says agents are "prompted with extensive literature reviews" but not what they said; user decisions 2026-10-04 | decided |
| R5 | Rating prompt wording | our own: baseline `prompts/persona_policy/baseline.txt` (B), instruction paraphrases `prompts/persona_policy/para_1..3.txt` (Q3a-c), joint template `prompts/joint/baseline.txt` (D1), definition paraphrases `designs/inputs/description_paraphrases/para_1..3.yaml` (Q2a-c); sha256 and equivalence records in `prompts/manifest.yaml`. The persona preamble (R2) and block headings are fixed in code, not paraphrased | not published | decided: reviewed by the user 2026-10-04; hashes copied into the prereg at freezing |
| R6 | Order | the baseline presents one policy per call, so policy order does not arise; criteria order within the JSON is fixed | not published | decided |
| R7 | "Deliberation" | single structured call per rating, no multi-turn deliberation or subagents | project rule; the paper's "deliberative" scoring is not specified | decided |
| R8 | Composite score | unweighted mean of the sub-criteria in a dimension | the paper shows composites in the essay but not the weights; spot checks (EITC welfare 68.8; EITC feasibility 79.8) match the unweighted mean; remaining composites checked in the baseline-comparison task | decided, to be verified |
| R9 | Temperature | recorded for every run; provider default for B, plus temperature 0 and one higher level in R-T | not published | levels TODO in prereg |
| R10 | Repeats | k_R repeats of B for the noise floor, k_Q per variation cell, set from the pilot's cost | user requirement 2026-10-03 | counts TODO in prereg |
| R11 | Popular Support | not rated; the paper uses survey net approval | paper Table 4 | decided |
| R12 | Implementation Readiness | rated by the agents; comparison lower-confidence | paper Table 4 (daggered, unexplained) | decided |

### 4a. The synthetic persona panel (stand-in, built 2026-10-04; now variation D2b)

`designs/inputs/personas/reconstructed.yaml` (moved from `personas/` on 2026-10-04 so the study
inputs live in one directory; content unchanged), built with
`llm-panel build-personas synthetic --n 51 --seed 2026`
before any result existed; the provenance block in the file records the method, seed and trait
space. Seven trait dimensions: field (8 levels), political leaning (5), view on redistribution (5),
view on AI and labour (4), view on the role of government (3), seniority (4) and country of origin
(8: US, UK, Germany, France, Canada, India, Brazil, Japan). Each dimension is balanced to within
one persona and assigned independently. Consequences, stated so they are not read as findings:
attitudes are not correlated with one another (real economists' views cluster), and the spread is
flat, which is wider than a real economist panel.

IGM panel levels are dropped from the design (user decision 2026-10-04). A builder exists for a
later extension (`llm-panel build-personas igm`); adding such levels after freezing would be a
recorded amendment.

### 4b. Evidence packets (built 2026-10-04, TASK-17)

Source: English Wikipedia, 13 articles at pinned revision ids (`evidence/mapping.yaml`,
`evidence/raw/manifest.json` with fetch times and sha256). The policy-to-article mapping and the
include/exclude rule (`evidence/extraction_prompt.md`, sha256 `8ba97f22...ce3`) were written and
approved before any article text was read for content (committed afterwards). UBC has no article of
its own ("Universal basic capital" redirects to Asset-based egalitarianism, which yielded no
evidence) so it rests on Baby bonds; Sovereign AI Fund / Dividend uses Sovereign wealth fund and
Alaska Permanent Fund.

Extraction: for each article, two independent passes by a fresh Claude Code subagent
(`claude-sonnet-5-5`) told to read only the article text; the isolation was instructed, not
enforced. Each span must be an exact substring of the pinned text (0 rejected across 26 passes).
The packet is the union of the two passes; overlapping spans are merged to the covering source
slice. Passes agreed on 66% (UI) to 100% of characters (UBS, Industrial policy); Wage insurance 0%
(one pass found one line about a 1995 Canadian project, the other found nothing; the line is kept
because the rule is union). Per-article agreement is in each packet header.

Known limits: two passes by one model do not prove completeness; verbatim sentences lose some
context; evidence is uneven across policies because the sources are (Wage insurance almost empty,
Alaska largest); packets are CC BY-SA 4.0 and shared alike. Packet size is recorded
(`evidence/packets/manifest.json`) and its association with scores is reported in the analysis.

## 5. EDSL reuse (checked 2026-10-03)

Checked `edsl` 1.0.8 (PyPI, MIT licence, Python 3.10-3.13, small core install) in a throwaway
environment, offline, with no model call. Findings:

- A persona is a plain dictionary of traits. Its prompt is the string
  `Your traits: {<dict>}` and the default instruction is "You are answering questions as if you
  were a human. Do not break character."
- Running surveys through EDSL would bypass this project's guards: the spend ceiling and
  ledger, job-hash deduplication, per-row logging of the full request, the model-id check, and
  the one-structured-call rule. It also composes its own prompt, which we would not control.

Decision: **reuse EDSL's persona format and wording, not its runtime.** Personas are stored as
trait dictionaries (compatible with `edsl.Agent(traits=...)`), and our own pipeline renders and
sends the prompt. EDSL is not a project dependency. Status: decided.

## 5a. Essay versus the paper (updated 2026-10-04)

The paper (15 Sep 2026) and the essay (16 Sep) carry the same tables. The paper's abstract and
Figure 2 give 11 household-facing policies plus 14 revenue and governance mechanisms; this study
follows the 11. The SSRN web abstract's "twenty-four" interventions does not appear in the PDF we
have, and is unexplained. Differences that matter: the paper defines the criteria in Table 1 and
the scenarios in Figure 1 (used here), treats popular support as survey data, and names the
personas; the essay reports two feasibility columns the paper's Table 4 omits. Status: decided.

## 6. What stays unknowable

The authors' exact prompts, the biographies and survey responses behind each persona, the
literature text, the model(s), temperature, number of runs and any aggregation beyond the published
tables cannot be recovered. Agreement with the published tables therefore measures how well a
plausible reconstruction reproduces them, not whether we reproduced the authors' procedure.
