# EXPLORATORY: reversed-scale probe — not pooled with the main analysis

Exploratory, post-freeze (prereg s13, TASK-38). Not part of the preregistered analysis, not pooled with it or with the adversarial arm. B's persona x policy prompt with one sentence changed so that 0 is best and 100 is worst; raw scores are converted with 100 - x before comparison. Search panel, seed, model and every other setting are the adversarial arm's baseline run, which is the comparison; the arm's rerun at another seed is the repeat-noise reference. Instability of scores shows they lack the claimed precision, not that the recommendations are wrong.

- Probe store: `scale_probe/results/rows.jsonl` (ceiling 0.30 USD); comparison runs read from `scale_probe/../adversarial/results/rows.jsonl` (read-only).
- Status: complete. Search panel: 5 personas; probe jobs 55, ratings 715, failed 0; baseline failed 0, rerun failed 0.

target policy: ubi (top on Full Transformation in the adversarial baseline run)

## Did the model follow the reversed scale?

Each reversed call against the same persona x policy baseline call: unconverted when its raw mean is nearer the baseline mean than 100 minus it; undecidable when the baseline mean is within 5 of 50.

| call class | calls |
|---|---|
| converted | 35 |
| unconverted | 1 |
| undecidable | 19 |

Raw (unconverted) reversed ratings against the baseline: n 715, r -0.91 (a faithful mirror gives r near -1).

## Agreement with the baseline run

Signed difference = run minus baseline. Panel means are policy x criterion means over the search panel, all 13 criteria.

| run | level | n | r | mean signed diff | mean abs diff |
|---|---|---|---|---|---|
| reversed, converted (100 - x) | single ratings | 715 | 0.91 | -1.5 | 6.9 |
| reversed, converted (100 - x) | panel means | 143 | 0.97 | -1.5 | 3.9 |
| baseline rerun (noise) | single ratings | 715 | 0.92 | 0.1 | 5.9 |
| baseline rerun (noise) | panel means | 143 | 0.98 | 0.1 | 2.5 |
| reversed, without unconverted calls | single ratings | 702 | 0.91 | -1.4 | 6.8 |
| reversed, without unconverted calls | panel means | 143 | 0.97 | -1.4 | 3.8 |

## Ranks, materiality and clauses

Beyond M: Table 4 policy x criterion panel means with |shift from the baseline| > 5. Target rank on Full Transformation in the run (1 = highest).

| run | target rank | beyond M = 5 | min tau | median tau |
|---|---|---|---|---|
| reversed, converted (100 - x) | ubi rank 2.0 | 32 | 0.60 | 0.85 |
| baseline rerun (noise) | ubi rank 2.0 | 12 | 0.77 | 0.88 |
| reversed, without unconverted calls | ubi rank 2.0 | 31 | 0.64 | 0.85 |

Kendall tau-b against the baseline run, per composite:

| composite | reversed, converted (100 - x) | baseline rerun (noise) | reversed, without unconverted calls |
|---|---|---|---|
| standards_of_living | 0.81 | 0.92 | 0.81 |
| meaning_human_value | 0.60 | 0.77 | 0.64 |
| macro_stabilisation | 0.77 | 0.88 | 0.78 |
| economic_agency_mobility | 0.70 | 0.84 | 0.70 |
| ownership_of_gains | 0.92 | 0.82 | 0.92 |
| democratic_voice | 0.88 | 0.94 | 0.92 |
| economic_feasibility | 0.82 | 0.82 | 0.82 |
| implementation_readiness | 0.93 | 0.89 | 0.93 |
| mild_disruption | 0.93 | 0.85 | 0.96 |
| moderate_disruption | 0.75 | 0.91 | 0.71 |
| full_transformation | 0.88 | 0.88 | 0.88 |
| welfare_resilience | 0.96 | 0.96 | 0.96 |
| agency_voice | 0.89 | 1.00 | 0.89 |
| feasibility | 0.84 | 0.89 | 0.84 |
| scenario_durability | 0.85 | 0.85 | 0.85 |

Clauses in each run (holds, margin); on a 5-persona panel, descriptive only:

| clause | reversed, converted (100 - x) | baseline rerun (noise) | reversed, without unconverted calls |
|---|---|---|---|
| (a) UBC rank 1 on Full Transformation durability | yes (14.0) | yes (14.0) | yes (14.0) |
| (b) UBC rank 1 on Ownership of Gains | yes (2.4) | yes (1.8) | yes (2.4) |
| (c) NIT in the top 3 on Moderate durability | no (-18.0) | no (-13.8) | no (-18.0) |
| (d) UI and EITC in the top 4 on Mild, both below UBC on Full Transformation | yes (4.0) | yes (8.0) | yes (6.0) |
| (sequence) three-stage sequence UI/EITC -> NIT -> UBC: (a), (c) and (d) all hold | no (-18.0) | no (-13.8) | no (-18.0) |

## Units beyond M = 5

- reversed, converted (100 - x): ubc x full_transformation +20.8; ubi x economic_feasibility -12.6; ui x moderate_disruption -12.0; ubc x economic_feasibility -11.2; nit x full_transformation -10.8; eitc x macro_stabilisation -10.4; ubs x full_transformation -9.4; ubc x implementation_readiness -9.2; almp x moderate_disruption -9.2; directed_industrial_policy x democratic_voice -9.0; fjg x mild_disruption -8.6; sawf x macro_stabilisation -8.4; ubs x moderate_disruption -8.4; ubi x mild_disruption -8.0; wage_insurance x implementation_readiness +7.4; directed_industrial_policy x economic_feasibility -7.2; almp x democratic_voice +7.0; fjg x moderate_disruption -7.0; wage_insurance x democratic_voice +7.0; wage_insurance x macro_stabilisation +7.0; ubc x mild_disruption -6.8; directed_industrial_policy x standards_of_living -6.4; fjg x full_transformation -6.4; wage_insurance x meaning_human_value +6.4; fjg x economic_feasibility -6.2; ui x full_transformation -6.2; almp x standards_of_living -6.0; fjg x standards_of_living -5.8; ubi x macro_stabilisation -5.6; eitc x economic_agency_mobility -5.4; almp x full_transformation -5.2; almp x macro_stabilisation -5.2.
- baseline rerun (noise): ubc x full_transformation +17.0; ubs x full_transformation -8.8; ubc x moderate_disruption +8.4; sawf x full_transformation -7.2; ubs x moderate_disruption -7.2; fjg x implementation_readiness +7.0; fjg x ownership_of_gains -6.4; fjg x economic_agency_mobility -6.0; nit x ownership_of_gains -5.6; sawf x mild_disruption -5.4; almp x standards_of_living +5.2; ui x moderate_disruption -5.2.
- reversed, without unconverted calls: ubc x full_transformation +20.8; ubi x economic_feasibility -12.6; ui x moderate_disruption -12.0; ubc x economic_feasibility -11.2; nit x full_transformation -10.8; ubs x full_transformation -9.4; ubc x implementation_readiness -9.2; almp x moderate_disruption -9.2; directed_industrial_policy x democratic_voice -9.0; fjg x mild_disruption -8.6; sawf x macro_stabilisation -8.4; ubs x moderate_disruption -8.4; ubi x mild_disruption -8.0; eitc x macro_stabilisation -7.5; wage_insurance x implementation_readiness +7.4; directed_industrial_policy x economic_feasibility -7.2; almp x democratic_voice +7.0; fjg x moderate_disruption -7.0; wage_insurance x democratic_voice +7.0; wage_insurance x macro_stabilisation +7.0; ubc x mild_disruption -6.8; directed_industrial_policy x standards_of_living -6.4; fjg x full_transformation -6.4; wage_insurance x meaning_human_value +6.4; fjg x economic_feasibility -6.2; ui x full_transformation -6.2; almp x standards_of_living -6.0; fjg x standards_of_living -5.8; ubi x macro_stabilisation -5.6; almp x full_transformation -5.2; almp x macro_stabilisation -5.2.

## How to read this

- One run of 5 personas per condition: a probe of the response scale, not an estimate of the panel's stability. Compare every row with the rerun row, which changes only the seed.
- A shift after conversion mixes three things the probe cannot separate: calls that ignored the reversal, an asymmetric response to a reversed scale (e.g. avoiding 0), and ordinary run-to-run noise.
- The probe's prompts use the adversarial arm's settings, including its max_tokens cap (600 per rating), which differ from study cell B's (400).
