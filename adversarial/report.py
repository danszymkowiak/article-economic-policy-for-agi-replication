"""ADVERSARIAL ARM report: every candidate tried, the stop reason and the smallest change found.
Rendering only; the numbers come from arm.py."""

from __future__ import annotations

import csv
import io

from adversarial.arm import BASELINE_PENDING, ArmSettings, ArmState, Submission
from adversarial.catalogue import CATALOGUE, CATALOGUE_VERSION
from adversarial.search import Outcome, Tried

HEADER = "# ADVERSARIAL ARM — not pooled with the main analysis"
CSV_FIELDS = (
    "order", "depth", "candidate", "change", "target_rank", "rank_drop", "top_to_bottom",
    "winner", "n_edits", "prompt_chars", "prompts_changed", "personas", "target_mean",
    "failed_jobs",
)  # fmt: skip
_DESCRIPTION = {p.id: p.description for p in CATALOGUE}


def _change(t: Tried) -> str:
    return "; ".join(_DESCRIPTION[p.id] for p in t.candidate.perturbations)


def _num(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _outcome_line(o: Outcome | None, target: str) -> str:
    if o is None:
        return "not evaluable (a policy has no ratings)"
    return (f"target rank {o.ranks[target]:.1f} of {o.n_policies}, panel mean "
            f"{o.means[target]:.1f} ({o.n_personas} personas)")  # fmt: skip


def render_csv(state: ArmState) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_FIELDS)
    s = state.search
    for i, t in enumerate(s.tried if s else (), start=1):
        o = t.outcome
        w.writerow([
            i, t.candidate.depth, t.candidate.key, _change(t), _num(t.target_rank),
            _num(t.rank_drop), "yes" if t.top_to_bottom else "no",
            "yes" if s.winner is t else "no", t.size.n_edits, t.size.max_prompt_chars,
            t.size.prompts_changed, o.n_personas if o else "", _num(o.means[state.target]) if o
            else "", state.failed_jobs.get(t.candidate.key, 0),
        ])  # fmt: skip
    return buf.getvalue()


def render_markdown(
    sub: Submission, settings: ArmSettings, store_label: str, ceiling: float
) -> str:
    state = sub.state
    lines = [
        HEADER,
        "",
        "This is the adversarial arm (prereg s9). It searches on purpose for the smallest change "
        "that moves the top policy to the bottom of the ranking. It is a worst-case search, not "
        "an estimate of how stable the rankings are, and none of it enters the main analysis. "
        "Instability of scores shows they lack the claimed precision, not that the "
        "recommendations are wrong.",
        "",
        f"- Store: `{store_label}` (the arm's own store; never `results/raw`).",
        f"- Catalogue `{CATALOGUE_VERSION}` ({len(CATALOGUE)} entries); caps: depth "
        f"{settings.max_depth}, {settings.max_candidates} candidates; spend ceiling "
        f"${ceiling:.2f} for this ledger, inside the global $15.",
        f"- Search panel: {state.panel_size} personas of `{settings.baseline.persona_source}` "
        f"drawn with seed {settings.panel_seed}; one run per candidate at seed {settings.seed}; "
        f"model `{settings.baseline.model.snapshot}`; primary composite "
        f"`{settings.primary_composite}`.",
        f"- Status: **{sub.status}**",
    ]
    if state.status == BASELINE_PENDING:
        lines += ["", "The search-panel baseline is not complete yet; no candidate has run.", ""]
        return "\n".join(lines)
    s, target = state.search, state.target
    lines += [
        f"- Target policy: `{target}` (first in the search-panel baseline: "
        f"{_outcome_line(state.baseline, target)}).",
        f"- Baseline rerun at seed {settings.noise_seed} (repeat-noise reference): "
        f"{_outcome_line(state.noise, target)}.",
        f"- Candidates tried: **{len(s.tried)}**. This is the multiple-comparisons denominator: "
        "a winner is the most extreme of these single runs, so part of its movement can be "
        "repeat noise.",
        f"- Greedy path: {', '.join(f'`{k}`' for k in s.path) or 'none'}.",
    ]
    if s.capped:
        lines.append(f"- Left out by the candidate cap: {s.capped}.")
    if sub.unaffordable:
        lines.append(
            f"- Not run for lack of budget: {', '.join(f'`{k}`' for k in sub.unaffordable)}."
        )
    if sub.waiting or sub.keys:
        lines.append(
            f"- Still to collect or submit: {', '.join(f'`{k}`' for k in sub.waiting + sub.keys)}."
        )
    w = s.winner
    if w is not None:
        lines += [
            f"- Smallest change found: `{w.candidate.key}` ({_change(w)}); edit size "
            f"{w.size.n_edits} perturbation(s), at most {w.size.max_prompt_chars} characters "
            f"changed in one prompt, {w.size.prompts_changed} prompt(s) changed; "
            f"{_outcome_line(w.outcome, target)}.",
        ]
    else:
        lines.append("- No candidate moved the target from top to bottom.")
    lines += [
        "",
        "## Every candidate tried",
        "",
        "| # | Depth | Candidate | Change | Target rank | Drop | Top to bottom | Edits | Chars "
        "| Prompts | Failed jobs |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, t in enumerate(s.tried, start=1):
        mark = " (smallest)" if t is w else ""
        lines.append(
            f"| {i} | {t.candidate.depth} | `{t.candidate.key}`{mark} | {_change(t)} "
            f"| {_num(t.target_rank)} | {_num(t.rank_drop)} | {'yes' if t.top_to_bottom else 'no'} "
            f"| {t.size.n_edits} | {t.size.max_prompt_chars} | {t.size.prompts_changed} "
            f"| {state.failed_jobs.get(t.candidate.key, 0)} |"
        )
    lines += [
        "",
        "Edit size is compared in order: perturbations, then the largest number of characters "
        "changed in one prompt, then prompts changed. Temperature and the persona drop change no "
        "characters; weigh them as you see fit.",
        "",
    ]
    return "\n".join(lines)
