"""Claude arm descriptive report (TASK-35 criteria 4-6). Reads only subagent_arm/results/rows.jsonl.
Descriptive, no inference. Run: uv run python subagent_arm/report.py"""

# ruff: noqa: E501  (long report-text string literals)
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

from llm_panel.bootstrap.published_loader import load_published
from llm_panel.domain.analysis_baseline import (
    COMPOSITES,
    TABLE4_CRITERIA,
    compare,
    composite_scores,
)

ROOT = Path(__file__).resolve().parent.parent
rows = [json.loads(x) for x in (ROOT / "subagent_arm/results/rows.jsonl").open()]
CRIT = rows[0]["request"]["criterion_ids"]


def parse(text: str) -> dict[str, tuple[float, str]]:
    """The study's validated JSON reply (response.text, converted from the agent's lines on ingest)."""
    return {
        x["criterion"]: (float(x["score"]), x["rationale"]) for x in json.loads(text)["ratings"]
    }


ok = [r for r in rows if r["status"] == "ok"]
obs = {}  # (repeat, persona, policy) -> {crit: (score, rationale)}
for r in ok:
    q = r["request"]
    obs[(q["repeat"], q["persona_id"], q["policy_ids"][0])] = parse(r["response"]["text"])
assert all(set(v) == set(CRIT) for v in obs.values()), "incomplete criterion sets"
repeats = sorted({k[0] for k in obs})
personas = sorted({k[1] for k in obs})
policies = sorted({k[2] for k in obs})
print("jobs ok", len(obs), "repeats", repeats, "personas", len(personas), "policies", len(policies))
print("status rows", {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}})

L = []
w = L.append
w("# Claude subagent arm: descriptive report (separate arm, not pooled)\n")
w(
    "**Separate, labeled arm.** Claude Haiku 4.5 run as Claude Code subagents (restricted `rater` agent, "
    "alias `claude-haiku-4-5`, no temperature/seed control). Differences from any other model mix model, "
    "agentic harness and uncontrolled sampling. Descriptive only; no inference language. Instability of "
    "scores shows they lack the claimed precision, not that the recommendations are wrong.\n"
)

# ---- completeness
fail = [r for r in rows if r["status"] != "ok"]
w("## 0. Completeness and failures\n")
w(
    f"- {len(obs)} valid persona x policy calls: pass 1 = {sum(k[0] == 0 for k in obs)}, "
    f"UBC repeats = {sum(k[0] > 0 for k in obs)}."
)
w(
    f"- {len(fail)} invalid first attempts out of {len(rows)} rows ({len(fail) / len(rows):.1%} of rows); every one "
    "was retried and passed. 2 of them were caused by a driver-side typo in the agent prompt (task file not "
    "found), not by the rater; discards are logged in the store.\n"
)

# ---- stability UBC
ubc = "ubc"
w("## 1. Stability (UBC, the repeated policy)\n")
pm = {c: [st.mean(obs[(r, p, ubc)][c][0] for p in personas) for r in repeats] for c in CRIT}
w("Panel mean (51 personas) per pass, and pass-to-pass spread:\n")
w("| criterion | pass 1 | pass 2 | pass 3 | SD across passes | range |")
w("|---|---|---|---|---|---|")
for c in CRIT:
    v = pm[c]
    w(
        f"| {c} | "
        + " | ".join(f"{x:.1f}" for x in v)
        + f" | {st.stdev(v):.2f} | {max(v) - min(v):.1f} |"
    )
rng = [max(pm[c]) - min(pm[c]) for c in CRIT]
w(
    f"\nLargest pass-to-pass range in a panel mean: {max(rng):.1f}; median {st.median(rng):.1f}; "
    f"cells with range above the materiality margin M = 5: {sum(x > 5 for x in rng)} of {len(CRIT)}.\n"
)
# decomposition
w(
    "Persona-level noise and variance decomposition (per criterion, one-way on personas, 3 passes):\n"
)
w(
    "| criterion | persona SD (of 3-pass means) | within-persona run SD | run share of single-rating variance |"
)
w("|---|---|---|---|")
shares = []
for c in CRIT:
    within = [st.pvariance([obs[(r, p, ubc)][c][0] for r in repeats]) * 3 / 2 for p in personas]
    s2run = st.mean(within)
    pmeans = [st.mean(obs[(r, p, ubc)][c][0] for r in repeats) for p in personas]
    s2p_obs = st.variance(pmeans)
    s2persona = max(s2p_obs - s2run / 3, 0.0)
    share = s2run / (s2run + s2persona) if s2run + s2persona else float("nan")
    shares.append(share)
    w(f"| {c} | {s2persona**0.5:.1f} | {s2run**0.5:.1f} | {share:.0%} |")
w(
    f"\nMedian run share of single-rating variance: {st.median(shares):.0%}. Single ratings from the same "
    "persona on the same policy differ across passes by roughly the within-persona run SD shown; the "
    "51-persona panel mean averages most of that out.\n"
)
# recommendation clauses: rank of UBC among policies per pass (others from pass 1)
w(
    "UBC rank among the 11 policies on each Table 4 criterion, with UBC from each pass and the other "
    "policies' pass-1 means (1 = highest):\n"
)
p1 = {c: {p: st.mean(obs[(0, q, p)][c][0] for q in personas) for p in policies} for c in CRIT}
w("| criterion | pass 1 | pass 2 | pass 3 |")
w("|---|---|---|---|")
for c in TABLE4_CRITERIA:
    cells = []
    for i in range(len(repeats)):
        mine = pm[c][i]
        others = [p1[c][p] for p in policies if p != ubc]
        cells.append(str(1 + sum(o > mine for o in others)))
    w(f"| {c} | " + " | ".join(cells) + " |")
w("")

# ---- distribution
w("## 2. Distribution of responses (pass 1, all 561 calls)\n")
w("| criterion | mean | SD | p10 | median | p90 | % multiple of 5 | % in 0-10 | % in 90-100 |")
w("|---|---|---|---|---|---|---|---|---|")
p1obs = {k: v for k, v in obs.items() if k[0] == 0}
for c in CRIT:
    x = sorted(v[c][0] for v in p1obs.values())

    def q(f, x=x):
        return x[min(int(f * len(x)), len(x) - 1)]

    w(
        f"| {c} | {st.mean(x):.1f} | {st.stdev(x):.1f} | {q(0.1):.0f} | {q(0.5):.0f} | {q(0.9):.0f} | "
        f"{sum(a % 5 == 0 for a in x) / len(x):.0%} | {sum(a <= 10 for a in x) / len(x):.0%} | {sum(a >= 90 for a in x) / len(x):.0%} |"
    )
allx = [v[c][0] for v in p1obs.values() for c in CRIT]
w(
    f"\nAll ratings: mean {st.mean(allx):.1f}, SD {st.stdev(allx):.1f}; share multiples of 5 "
    f"{sum(a % 5 == 0 for a in allx) / len(allx):.0%}; share of 10s multiples {sum(a % 10 == 0 for a in allx) / len(allx):.0%}.\n"
)
# persona spread: SD across personas of each persona's mean over policies x criteria
pmean = {q: st.mean(v[c][0] for k, v in p1obs.items() if k[1] == q for c in CRIT) for q in personas}
w(
    f"Persona spread: SD of persona means (each over all policies and criteria) = {st.stdev(pmean.values()):.2f}; "
    f"range {min(pmean.values()):.1f} to {max(pmean.values()):.1f}."
)
# within-policy persona SD per criterion (mean over policies)
wsd = {
    c: st.mean(st.stdev([v[c][0] for k, v in p1obs.items() if k[2] == p]) for p in policies)
    for c in CRIT
}
w(
    f"Mean across policies of the between-persona SD per criterion: min {min(wsd.values()):.1f}, "
    f"median {st.median(wsd.values()):.1f}, max {max(wsd.values()):.1f}.\n"
)


# halo: mean pairwise correlation of criteria within-policy-centred across calls
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


cen = {}
for p in policies:
    ks = [k for k in p1obs if k[2] == p]
    for c in CRIT:
        m = st.mean(p1obs[k][c][0] for k in ks)
        for k in ks:
            cen.setdefault(c, {})[k] = p1obs[k][c][0] - m
keys = sorted(p1obs)
cs = [
    corr([cen[a][k] for k in keys], [cen[b][k] for k in keys])
    for i, a in enumerate(CRIT)
    for b in CRIT[i + 1 :]
]
w(
    f"Halo: mean pairwise correlation among the 13 criteria across calls, after centring each policy's "
    f"ratings on its panel mean (so it is persona-driven co-movement): {st.mean(cs):.2f} "
    f"(min {min(cs):.2f}, max {max(cs):.2f}). Same without centring: "
    f"{st.mean([corr([p1obs[k][a][0] for k in keys], [p1obs[k][b][0] for k in keys]) for i, a in enumerate(CRIT) for b in CRIT[i + 1 :]]):.2f}."
)
rl = [len(v[c][1]) for v in p1obs.values() for c in CRIT]
w(
    f"Rationale length (characters): mean {st.mean(rl):.0f}, median {st.median(rl):.0f}, max {max(rl)}.\n"
)

# ---- Table 4
w("## 3. Agreement with published Table 4 (pass 1 panel means; UBC also with 3-pass mean)\n")
pub = load_published(ROOT / "analysis/published/paper_table4.csv")
ours = {c: p1[c] for c in TABLE4_CRITERIA if all(p in pub.scores[c] for p in policies)}
ours_comp = composite_scores(ours)
pubs = {c: {p: v for p, v in pub.scores[c].items() if p in policies} for c in TABLE4_CRITERIA}
pub_comp = composite_scores(pubs)
w(f"Policies compared: {sorted(set(policies))}\n")
w(
    "| composite | n | Spearman | Kendall tau-b | mean abs diff | mean signed diff (ours - published) |"
)
w("|---|---|---|---|---|---|")


def f(v):
    return "n/a" if v is None else f"{v:.2f}"


for a in compare(ours_comp, pub_comp, list(COMPOSITES)):
    sd = st.mean(a.differences.values()) if a.differences else float("nan")
    w(
        f"| {a.composite} | {a.n_policies} | {f(a.spearman)} | {f(a.kendall_tau_b)} | {a.mean_abs_diff:.1f} | {sd:+.1f} |"
    )
w("\nUBC cells, Claude pass 1 / 3-pass mean / published:\n")
w("| criterion | pass 1 | 3-pass mean | published | diff (3-pass - published) |")
w("|---|---|---|---|---|")
for c in TABLE4_CRITERIA:
    m3 = st.mean(pm[c])
    w(
        f"| {c} | {pm[c][0]:.1f} | {m3:.1f} | {pub.scores[c][ubc]:.1f} | {m3 - pub.scores[c][ubc]:+.1f} |"
    )
big = sum(abs(st.mean(pm[c]) - pub.scores[c][ubc]) > 5 for c in TABLE4_CRITERIA)
w(
    f"\nUBC cells where Claude's 3-pass mean differs from the published value by more than 5: {big} of {len(TABLE4_CRITERIA)}.\n"
)

w("## 4. Not computed here\n")
w(
    "The Claude-versus-B comparisons (cells shifted by more than M = 5 against B, B's repeat noise "
    "beside Claude's, rank and clause comparison against B) need the main arm's baseline B store "
    "(`results/raw`), which is empty: the preregistered main run has not been made. They are left until "
    "it exists. The published-Table 4 comparison above is the only between-source comparison available now."
)
(ROOT / "subagent_arm/reports/claude_arm_report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
