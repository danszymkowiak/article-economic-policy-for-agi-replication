---
id: TASK-31
title: Named-persona builder from paper Appendix A Table 7
status: To Do
assignee: []
created_date: '2026-10-04 07:16'
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
- [ ] #1 personas/named.yaml holds 51 personas with traits name, institution, primary_field taken from Table 7, with a provenance block (source, table, retrieval date)
- [ ] #2 John Cochrane, named in the paper text but absent from Table 7, is excluded and the mismatch is recorded in the provenance
- [ ] #3 A tested builder command regenerates the file deterministically and fails if the roster is not 51 unique names
- [ ] #4 Rendering uses the EDSL-style Your traits format; tests show persona text contains no reported results or opinions beyond the three traits
<!-- AC:END -->
