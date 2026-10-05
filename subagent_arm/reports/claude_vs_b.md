# Claude subagent arm versus the main arm's B (separate arm, not pooled)

**Separate, labeled arm (prereg s9a).** Claude Haiku 4.5 as Claude Code subagents against glm-5.3-flash's baseline B on the same rendered prompts. A difference is a difference between two model-and-harness bundles (model, agentic wrapper, line reply format, uncontrolled sampling), not a clean model effect: it shows that scores depend on which model is used, not that either is right. Descriptive only. Instability of scores shows they lack the claimed precision, not that the recommendations are wrong.

- Compared on 7267 persona x policy x criterion keys (51 personas) present in every B repeat and in Claude's pass 1. B: repeat mean of its 5 repeats; Claude: pass 1 (one run) unless stated.

## Between models: panel means shifted by more than M = 5

- Table 4 units (policy x criterion, 121): **72** beyond M = 5 between Claude pass 1 and B.
- Reference, what one run of the same model does: each B repeat against the mean of the other four, units beyond M = 5: 0, 0, 0, 0, 0 (min 0, max 0).
- Added criteria (Political Support, Administrative Capacity and Speed; descriptive, not in the count): 13 beyond M.

Largest Table 4 shifts (Claude - B):

wage_insurance x macro_stabilisation +28.2; ubs x full_transformation +25.0; almp x standards_of_living +24.9; fjg x full_transformation +22.9; ubi x economic_feasibility +21.1; eitc x economic_agency_mobility +21.0; ubc x standards_of_living +21.0; almp x implementation_readiness +20.3; almp x macro_stabilisation +19.7; ubi x macro_stabilisation +19.6; sawf x implementation_readiness +18.7; sawf x full_transformation +18.6; fjg x economic_feasibility +16.9; almp x ownership_of_gains +16.3; wage_insurance x moderate_disruption +16.1; wage_insurance x standards_of_living +15.9; wage_insurance x full_transformation +15.8; eitc x macro_stabilisation +15.7; sawf x macro_stabilisation +15.5; ubs x macro_stabilisation +15.3

## UBC: between-model shift beside each model's repeat noise

| criterion | B mean | B SD (5 runs) | Claude passes | Claude mean | Claude SD (3 passes) | shift (Claude mean - B) |
|---|---|---|---|---|---|---|
| standards_of_living | 51.2 | 0.30 | 72.2 / 71.9 / 71.8 | 72.0 | 0.22 | +20.8 |
| meaning_human_value | 62.4 | 0.89 | 60.5 / 61.8 / 60.0 | 60.8 | 0.92 | -1.6 |
| macro_stabilisation | 32.7 | 0.71 | 46.8 / 46.1 / 44.1 | 45.7 | 1.41 | +13.0 |
| economic_agency_mobility | 72.1 | 0.40 | 75.2 / 75.8 / 74.8 | 75.3 | 0.49 | +3.1 |
| ownership_of_gains | 90.1 | 0.55 | 85.8 / 85.4 / 85.9 | 85.7 | 0.24 | -4.3 |
| democratic_voice | 64.7 | 0.70 | 68.9 / 68.8 / 68.0 | 68.6 | 0.46 | +3.9 |
| economic_feasibility | 47.3 | 0.35 | 50.0 / 52.5 / 50.8 | 51.1 | 1.27 | +3.8 |
| implementation_readiness | 47.1 | 0.64 | 54.9 / 56.4 / 57.0 | 56.1 | 1.07 | +9.0 |
| mild_disruption | 64.0 | 0.64 | 67.1 / 67.0 / 67.1 | 67.1 | 0.08 | +3.1 |
| moderate_disruption | 69.5 | 0.65 | 75.8 / 74.7 / 74.6 | 75.0 | 0.63 | +5.6 |
| full_transformation | 68.1 | 1.51 | 81.9 / 80.6 / 82.4 | 81.6 | 0.96 | +13.5 |
| admin_capacity_speed | 50.5 | 0.38 | 62.4 / 60.9 / 62.2 | 61.8 | 0.79 | +11.4 |
| political_support | 54.5 | 0.62 | 60.3 / 62.4 / 59.9 | 60.8 | 1.33 | +6.4 |

## Recommendation clauses

Holds or fails with its margin (prereg s6). Claude per pass: (a) and (b) with that pass's UBC means and pass 1's means for the other policies.

| clause | B (repeat mean) | Claude pass 1 | Claude UBC pass 1 | Claude UBC pass 2 | Claude UBC pass 3 |
|---|---|---|---|---|---|
| (a) UBC rank 1 on Full Transformation durability | holds (3.1) | holds (6.1) | holds (6.1) | holds (4.7) | holds (6.6) |
| (b) UBC rank 1 on Ownership of Gains | holds (3.0) | holds (1.1) | holds (1.1) | holds (0.7) | holds (1.2) |
| (c) NIT in the top 3 on Moderate durability | fails (-12.5) | fails (-15.4) |  |  |  |
| (d) UI and EITC in the top 4 on Mild, both below UBC on Full Transformation | holds (6.3) | holds (2.3) |  |  |  |
| (sequence) three-stage sequence UI/EITC -> NIT -> UBC: (a), (c) and (d) all hold | fails (-12.5) | fails (-15.4) |  |  |  |

## Ranks: Kendall tau-b, Claude pass 1 against B

| composite | tau-b |
|---|---|
| standards_of_living | 0.71 |
| meaning_human_value | 0.71 |
| macro_stabilisation | 0.75 |
| economic_agency_mobility | 0.24 |
| ownership_of_gains | 0.75 |
| democratic_voice | 0.71 |
| economic_feasibility | 0.38 |
| implementation_readiness | 0.71 |
| mild_disruption | 0.75 |
| moderate_disruption | 0.75 |
| full_transformation | 0.78 |
| welfare_resilience | 0.75 |
| agency_voice | 0.93 |
| feasibility | 0.71 |
| scenario_durability | 0.78 |

B's own repeat-noise taus are in `analysis/ranks/rank_stability.md` (pairwise minimum 0.88 to 0.96 by composite).

## Distribution of single ratings (B repeat 1 against Claude pass 1)

| criterion | B mean | B SD | B % mult. of 5 | Claude mean | Claude SD | Claude % mult. of 5 |
|---|---|---|---|---|---|---|
| standards_of_living | 66.3 | 15.0 | 60% | 73.4 | 7.0 | 50% |
| meaning_human_value | 62.5 | 10.0 | 55% | 61.3 | 11.1 | 51% |
| macro_stabilisation | 54.4 | 21.0 | 67% | 66.0 | 14.5 | 48% |
| economic_agency_mobility | 65.3 | 11.9 | 52% | 67.6 | 10.1 | 42% |
| ownership_of_gains | 31.6 | 28.4 | 67% | 38.4 | 23.3 | 55% |
| democratic_voice | 51.8 | 12.1 | 68% | 56.9 | 10.7 | 45% |
| economic_feasibility | 51.9 | 12.9 | 56% | 54.3 | 9.5 | 43% |
| implementation_readiness | 56.4 | 18.5 | 65% | 64.0 | 17.4 | 41% |
| mild_disruption | 71.7 | 10.0 | 52% | 72.2 | 7.2 | 39% |
| moderate_disruption | 52.6 | 13.9 | 56% | 61.3 | 12.0 | 42% |
| full_transformation | 33.0 | 22.8 | 60% | 47.3 | 24.5 | 42% |
| admin_capacity_speed | 54.9 | 16.7 | 64% | 67.8 | 14.0 | 42% |
| political_support | 60.7 | 13.8 | 61% | 64.5 | 10.7 | 41% |
