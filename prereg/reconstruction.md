# Reconstruction of the setup from the public essay

**STATUS: DRAFT.** Companion to `prereg.md`; frozen together with it. This study is a
**re-implementation from the public description, not a replication**. The authors released no
prompts, persona data, survey responses or evidence packet. Everything below is either taken
from the essay (marked *essay*) or is our own stand-in (marked *stand-in*). No stand-in is the
authors' original, and write-ups must say so wherever one is used.

Source: "Economic policy for AGI", Jacobs and Imas, DeepMind Institute, 2026-09-16
(snapshot in `docs/economic-policy-for-agi.html`, retrieved 2026-10-03).

## 1. What the essay tells us (essay)

| Item | What the essay says |
|---|---|
| Raters | 51 AI agent raters, each built from one of 51 real economists' survey answers, "capturing a diversity of economic and political attitudes". Tables say "N = 51 EDSL personas" |
| Method | "Pioneered by John Horton"; persona prompts built with EDSL; agents "rate" interventions "based on the available evidence and their own deliberative process" |
| Scale | 0 to 100 per sub-criterion; composite score per dimension; score tiers (High >= 70, Moderate 55-69, Mixed 42-54 or 40-54, Low < 42 or < 40) |
| Policies | 11 (section 2) |
| Criteria | 4 dimensions, 15 sub-criteria (section 3) |
| Published targets | One table per dimension with sub-criterion scores to one decimal and a composite (used only for the baseline comparison, task "Baseline comparison to published tables") |

## 2. Policies (essay, definitions paraphrased from the essay's taxonomy table)

Panel A, labour-market and wage interventions: Active Labour Market Policies and Retraining;
Wage Insurance; Earned Income Tax Credit (EITC); Federal Jobs Guarantee; Unemployment
Insurance (UI). Panel B, universal floors, services and structural assets: Negative Income Tax
(NIT); Universal Basic Income (UBI); Sovereign AI Dividend (the result tables call it "Sovereign
AI Fund / Dividend"); Universal Basic Capital (UBC); Universal Basic Services (UBS); Industrial
Policy (the tables say "Directed Industrial Policy").

Choice: use the taxonomy-table names and definitions as the *named* labels. The essay uses two
names for three policies; we use the taxonomy-table names. Status: decided.

## 3. Criteria (essay)

| Dimension | Sub-criteria |
|---|---|
| Welfare and Resilience | Standards of Living; Meaning and Human Value; Macroeconomic Stabilisation |
| Agency and Voice | Economic Participation; Ownership of Gains; Democratic Voice |
| Durability across scenarios | Mild Disruption; Broad Displacement; AGI Transformation |
| Feasibility and Efficiency | Political Support; Economic Feasibility; Popular Support; Administrative Capacity; Speed; Readiness |

15 sub-criteria. The essay gives one-line definitions for each (table footnotes and the
dimension definitions); the criterion descriptions in our inputs are those lines, lightly
reworded to stand alone. Status: decided.

Note: the essay says Speed and Readiness are "author-coded policy operational maturity", so
they may not have been rated by the agents. We rate all 15 with the agents, and treat the
Speed and Readiness comparison with the published scores as lower-confidence. Status: decided.

## 4. Choices we must make ourselves (stand-ins)

| # | Choice | Decision | Basis | Status |
|---|---|---|---|---|
| R1 | Unit of one call | one call per persona x criterion, all 11 policies in one prompt, scored 0-100 with a short rationale | `prereg.md` section 2; the essay does not say how many policies per prompt | decided |
| R2 | Persona representation | a `traits` dictionary per persona, rendered as `Your traits: {...}` after the instruction "You are answering questions as if you were a human. Do not break character." | EDSL's own default persona rendering, checked in section 5 | decided |
| R3 | The 51 baseline personas | 51 synthetic trait dictionaries written by us, spread over field, ideology and views on redistribution, AI and labour; labelled a stand-in everywhere. IGM Clark Center and IGM Europe stay separate persona-source levels | the survey of 51 economists is unpublished; user decision 2026-10-03 | decided |
| R4 | Evidence packet | neutral, balanced summaries of the evidence the essay cites (UI in Denmark, EITC, retraining, Alaska fund), written without the essay's conclusions to avoid circularity; the "balanced" and "none" levels remain | the essay says agents rate "based on the available evidence" but the packet is unpublished; user decision 2026-10-03 | decided |
| R5 | Rating prompt wording | our own; the baseline is one fixed wording, paraphrases come from the prompt-templates task | not published | decided (wording drafted later) |
| R6 | Policy order in a prompt | fixed in the baseline | not published | decided |
| R7 | "Deliberation" | single structured call per prompt, no multi-turn deliberation or subagents | project rule; the essay's "deliberative process" is not specified | decided |
| R8 | Composite score | unweighted mean of sub-criteria in a dimension | the essay shows composites but not the weights; we check that the published composites equal the mean of the published sub-criteria in the baseline-comparison task | decided, to be verified |
| R9 | Temperature | recorded for every run; levels set in `prereg.md` | not published | open in prereg |
| R10 | Repeats | several seeds per cell with otherwise identical prompts, to measure sampling stability; seed-stability cells use fixed order (random order is seeded by the same seed and would change the prompt) | user requirement 2026-10-03 | count TODO in prereg |

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

## 6. What stays unknowable

The authors' exact prompts, persona traits, evidence text, model(s), temperature and any
aggregation beyond the published tables cannot be recovered from the essay. Agreement with the
published tables therefore measures how well a plausible reconstruction reproduces them, not
whether we reproduced the authors' procedure.
