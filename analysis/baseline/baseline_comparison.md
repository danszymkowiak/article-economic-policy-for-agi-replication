# Baseline B versus the paper's published scores

- Store: `results/raw/rows.jsonl`; cell B ok jobs 2803, not ok 2 (failed 2), deferred 0, duplicate rows 0.
- Repeats 5; persona x policy pairs complete in every repeat 559 (dropped 2). Scores are repeat means of the unweighted panel mean.
- Counts: not ok = failed, awaiting retry, or stored ok but no longer parsing (failed = terminal failures among them); deferred = retry withheld, rerun later; duplicate rows = usage-only rows for jobs already finished (not outcomes).
- Published source:
  Published panel scores from "Economic Policy for AGI" (Jacobs and Imas, 15 Sep 2026), SSRN abstract 7470000.
  Source: Table 4 (p. 14) and Appendix B profiles B.1-B.11 (pp. 35-38) of docs/economic-policy-for-agi-ssrn.pdf
  (sha256 329f21d42fa4cceb999f91f1e765b1d8e1f801271bc4869858e87508f4f436b8), retrieved 2026-10-04.
  Table 4 and Appendix B carry the same numbers; tests/test_published_table4.py checks every value against both.
  Panel criteria are 0-100 means of N = 51 simulated economists; public_net_approval_pct is survey data
  (% support minus % oppose, N = 2,019), not a panel rating. Column ids are our criterion ids
  (designs/inputs/criteria.yaml); implementation_readiness is the paper's daggered "Ready" column.

## Agreement (rank correlation, not exact match)

| Composite | Policies | Spearman | Kendall tau-b | Mean abs. difference |
|---|---|---|---|---|
| standards_of_living | 11 | 0.65 | 0.53 | 12.3 |
| meaning_human_value | 11 | 0.01 | 0.02 | 12.8 |
| macro_stabilisation | 11 | 0.50 | 0.38 | 17.5 |
| economic_agency_mobility | 11 | -0.12 | -0.09 | 12.1 |
| ownership_of_gains | 11 | 0.80 | 0.64 | 12.9 |
| democratic_voice | 11 | 0.44 | 0.31 | 7.3 |
| economic_feasibility | 11 | 0.46 | 0.35 | 13.4 |
| implementation_readiness | 11 | 0.88 | 0.75 | 8.9 |
| mild_disruption | 11 | 0.40 | 0.31 | 18.3 |
| moderate_disruption | 11 | 0.50 | 0.31 | 12.1 |
| full_transformation | 11 | 0.87 | 0.71 | 23.7 |
| welfare_resilience | 11 | 0.39 | 0.35 | 9.7 |
| agency_voice | 11 | 0.51 | 0.35 | 7.2 |
| feasibility | 11 | 0.83 | 0.71 | 6.8 |
| scenario_durability | 11 | 0.65 | 0.42 | 11.2 |

## How to read this

- Agreement is reported as rank correlation, not exact match: the paper makes its recommendations by rank order, and our setup is a reconstruction, so equal scores are not expected. The mean absolute difference (score points) is descriptive only.
- Any gap between our baseline and the published numbers may come from our reconstruction as well as from instability of the panel scores. Prompts, evidence packets, personas, model and aggregation are our stand-ins (prereg/reconstruction.md); this comparison cannot tell the two sources apart.
- Agreement does not validate our procedure either: Table 4 has many round values (65.0 three times, 50.0, 27.0, 30.0, 78.0, 68.0) that a mean of 51 continuous scores would rarely produce, so the paper's aggregation is uncertain.
- Instability of the scores, where present, shows they lack the claimed precision, not that the recommendations are wrong.
- Composites are unweighted means of Table 4 columns. Feasibility is Economic Feasibility and Implementation Readiness only, the two columns in Table 4's Feasibility block (our reading; Table 1 also names Political, Popular and Administrative criteria, which the paper never publishes per policy). Scenario Durability is the mean of the three scenarios.
- Implementation Readiness carries an unexplained dagger in the paper (the essay calls it author-coded); its comparison is lower-confidence.
- Not compared: Political Support and Administrative Capacity & Speed (rated by us, not in Table 4) and Public Net Approval (survey data, not a panel rating).

## Dimension composites per policy (ours / published)

| Policy | welfare_resilience | agency_voice | feasibility | scenario_durability |
|---|---|---|---|---|
| eitc | 63.6 / 68.8 | 34.1 / 47.2 | 78.7 / 89.2 | 41.8 / 51.0 |
| ui | 71.7 / 66.7 | 44.0 / 43.7 | 71.7 / 86.9 | 47.7 / 62.0 |
| almp | 44.4 / 36.9 | 40.4 / 37.0 | 58.7 / 57.5 | 42.2 / 23.0 |
| wage_insurance | 56.1 / 47.4 | 39.0 / 44.7 | 62.3 / 51.3 | 42.7 / 35.9 |
| directed_industrial_policy | 44.8 / 49.1 | 32.1 / 52.1 | 43.3 / 54.5 | 39.0 / 51.4 |
| fjg | 78.2 / 44.4 | 48.2 / 46.2 | 34.8 / 32.5 | 50.5 / 35.0 |
| ubi | 65.8 / 51.2 | 59.1 / 53.1 | 41.7 / 39.4 | 65.4 / 57.7 |
| nit | 73.6 / 69.8 | 50.8 / 53.7 | 64.0 / 68.4 | 54.4 / 69.6 |
| ubs | 67.0 / 60.7 | 50.9 / 41.9 | 43.1 / 54.7 | 60.6 / 75.0 |
| ubc | 48.7 / 62.0 | 75.6 / 76.3 | 47.2 / 42.5 | 67.2 / 74.2 |
| sawf | 57.6 / 53.7 | 71.2 / 55.2 | 48.9 / 49.8 | 64.7 / 63.5 |

## Essay composite tables (reconstruction R8)

The essay prints a composite per policy for Welfare, Agency and Durability. First check (R8): the unweighted mean of the published Table 4 columns against the essay's composite. Second: our baseline B against the same essay composites.

| Composite | Policies | R8: max abs. diff | R8: Spearman | B vs essay: Spearman | B vs essay: Kendall tau-b | B vs essay: mean abs. diff |
|---|---|---|---|---|---|---|
| welfare_resilience | 11 | 0.03 | 1.00 | 0.39 | 0.35 | 9.7 |
| agency_voice | 11 | 0.03 | 1.00 | 0.51 | 0.35 | 7.2 |
| scenario_durability | 11 | 0.03 | 1.00 | 0.65 | 0.42 | 11.2 |

- Feasibility is not compared: the essay's composite averages six columns, including Popular Support (survey data) and Admin. Capacity and Speed as two columns, which our panel does not rate separately; it is transcribed for reference only.
- R8 differences below 0.1 are rounding of the printed one-decimal values.
