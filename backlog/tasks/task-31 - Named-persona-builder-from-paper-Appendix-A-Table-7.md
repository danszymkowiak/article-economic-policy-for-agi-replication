---
id: TASK-31
title: Named-persona builder from paper Appendix A Table 7
status: Done
assignee:
  - '@claude'
created_date: '2026-10-04 07:16'
updated_date: '2026-10-04 07:23'
labels:
  - phase3
dependencies:
  - TASK-15
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user decided to match the paper: the 51 baseline personas are the named economists in the paper's Appendix A Table 7. The existing builders (TASK-15) make synthetic trait personas and IGM-respondent personas, not these. Persona content is limited to name, institution and primary field because that is all the paper publishes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 personas/named.yaml holds 51 personas with traits name, institution, primary_field taken from Table 7, with a provenance block (source, table, retrieval date)
- [x] #2 John Cochrane, named in the paper text but absent from Table 7, is excluded and the mismatch is recorded in the provenance
- [x] #3 A tested builder command regenerates the file deterministically and fails if the roster is not 51 unique names
- [x] #4 Rendering uses the EDSL-style Your traits format; tests show persona text contains no reported results or opinions beyond the three traits
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented build_named_panel + 'build-personas named' CLI; roster at personas/sources/table7_roster.csv; generated personas/named.yaml (2026-10-04). 275 tests pass.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added build_named_panel, 'build-personas named' CLI, committed Table 7 roster CSV (verified 51 unique rows against paper text) and personas/named.yaml with provenance (Cochrane exclusion). 275 tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
