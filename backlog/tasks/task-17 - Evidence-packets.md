---
id: TASK-17
title: Evidence packets
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-03 06:03'
updated_date: '2026-10-04 07:07'
labels:
  - phase3
dependencies:
  - TASK-16
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Part of the LLM-panel sensitivity study (re-test of "Economic Policy for AGI"). Python, layered architecture (domain / ports / adapters / application / bootstrap), cron-friendly CLI entry points. Tasks are worked in order; run the tests and stop for user review after each. Global spend ceiling: max_spend_usd = 15.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Evidence mapping (policy to pinned Wikipedia revisions) and the evidence-only include/exclude rule are fixed and committed before any article text is read for content
- [ ] #2 Each article is fetched at its pinned revision, converted to plain text with section headings, and stored under evidence/raw with fetch date and sha256
- [ ] #3 A verifier rejects any extracted span that is not an exact substring of the pinned text; covered by tests
- [ ] #4 One verbatim packet per policy, produced by a subagent that sees only article text and the rule; extractor model id, prompt hash and run date logged; empty packets carry a note
- [ ] #5 Packets are published-ready: article titles, revision links, CC BY-SA 4.0 attribution and extractor identity in each header; packet token counts recorded
- [ ] #6 A none option (no packet) exists for the evidence factor; sources documented in prereg/reconstruction.md
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Tests then verifier (exact-substring span check) in a small pure module. 2. Fetch script: MediaWiki parse at oldid, HTML to text with headings, store raw + sha256 + fetch date. 3. Extraction prompt file (rule only), hashed. 4. Run the extractor subagent per policy, verify spans, write packets with headers. 5. Record token counts, update docs. Stop for user review.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carried over from TODO.md: replaces the placeholder prompt template (domain/rendering.py) and fake inputs (designs/fake_inputs/) for its part of the setup. Point config.yaml paths.inputs_dir at the real inputs when done.

2026-10-04: mapping + extraction prompt (sha256 8ba97f22...) fixed; 13 pinned Wikipedia revisions fetched to evidence/raw (manifest.json); 13 extractor subagents (claude-sonnet-5-5) each saw only its article file; all spans verified as exact substrings (0 rejected); 11 packets built in evidence/packets. Open: recall of extraction not audited; some spans lack antecedents; isolation of extractors from project files is instructed, not enforced; none/alt-packet option and reconstruction.md sources not done. Awaiting user review.

2026-10-04 recall audit (second independent pass, same prompt, on UBI and UI): UBI pass1 11 / pass2 12 spans, character overlap 96% (pass2 adds Bolsa Familia passage only). UI pass1 13 / pass2 23 spans, overlap 66% of union (pass1-only 851 chars, pass2-only 656 chars). Second-pass outputs in evidence/extracted_pass2; packets NOT yet changed. Decision pending: union of passes for all packets vs single pass.

2026-10-04 (user chose option 1): second independent pass run on all 13 articles; packets rebuilt as union of two passes via merge_passes (overlaps merged to contiguous source slices); per-article pass agreement stored in packet headers. Agreement by article: ALMP 98%, Wage ins 0% (pass1 1 span, pass2 0), EITC 93%, Job guarantee 91%, UI 66%, NIT 87%, UBI 96%, UBS 100%, Industrial 100%, Asset-based egal 100% (both empty), Baby bonds 89%, SWF 97%, Alaska 74%. 0 spans rejected across 26 passes. Pass-2 raw outputs in evidence/extracted_pass2. Still open: none option, reconstruction.md sources, user review.
<!-- SECTION:NOTES:END -->
