# Cleaning plan - written before implementation

Author: Yixiang Lu, with Codex assistance. Project: AI Workforce Investment Planner,
Vision A (confirmed by the student). This is an individual submission; team
reconciliation is pending. Rules are proposed analytical choices for student review.

## Question and scope

Which California OEWS area-occupation combinations have substantial published
employment and merit further review alongside California occupation-level Claude
usage? Compare employment, median annual wages, and published AI-use shares
separately. Do not produce an investment score, ROI, or job-loss prediction.

Use both original June 26, 2026 Anthropic CSVs, the original May 2025 BLS metro
and nonmetro ZIP, and four original OpenAI Signals tables (all-message IWA,
work-message IWA, state rankings, state topic shares). Other Signals demographic
tables are outside this question. Inspect every row of each selected source.

## Initial observations

- Claude.ai has 1,636,573 rows; API has 491,705. Neither has exact duplicate rows
  or empty fields. Claude.ai contains 5,122 California rows; API is global only.
- AEI includes multiple periods, geography levels, metrics, and hierarchy levels.
  Repeated occupation IDs alone are valid, not duplicate records.
- Signals selected tables have 3,960, 3,960, 51, and 357 rows, respectively;
  no exact duplicates or empty fields were observed.
- BLS has separate metro/nonmetro workbooks, detailed occupations and aggregate
  occupational groups. IDs, NAICS, and ownership codes are identifiers.

## Rules and reasons

1. Read sources without modifying them. Record file sizes and SHA-256 hashes;
   original download dates are unknown. Identify fixed releases and inspection date.
2. Read CSV fields as strings, recognizing only empty strings as missing.
   Trim boundary whitespace, preserve capitalization and identifier punctuation.
   Never convert identifier strings to numbers. Record changed cells and examples.
3. Check exact duplicates separately from full logical-key repetitions. Stop on
   duplicate logical keys; do not silently deduplicate or select a first record.
4. Parse explicit date formats and numeric fields. Record each failed conversion,
   preserve raw values, and fail on unexpected parse failures. Published BLS
   `*`, `**`, `#`, and blank markers become missing numeric values with raw markers
   retained; a top-coded wage is not its threshold and missing is not zero.
5. Retain full selected AEI occupation rows for CA, USA, and GLOBAL for Claude.ai,
   and GLOBAL for API; retain all their metrics and both published periods.
   Preserve product, geography, hierarchy, unit, and period explicitly.
   Percentage values remain percentages. Do not average or sum different metrics.
6. BLS scope: PRIM_STATE=CA, O_GROUP=detailed, NAICS=000000,
   OWN_CODE=1235, from both metro and nonmetro files. Retain all source columns.
   Flag cross-state area names. Exclude aggregate occupation rows to avoid
   double-counting. One row is one published area x detailed occupation.
7. Keep all rows of the four selected Signals tables, including `Other IWA`.
   Shares remain fractions in [0,1], ranks remain ordinal; never add ranks.
   Keep these as contextual tables rather than fabricate an occupation crosswalk.
8. Produce a separate, explicitly provisional join of May 2026 California leaf
   occupation Claude shares to BLS. Aggregate published leaf shares to the first
   seven characters (six-digit SOC) with contributing-code counts. Left join
   to every selected BLS row, requiring many-to-one cardinality. This code-prefix
   mapping is not a verified historical taxonomy crosswalk. Export unmatched keys;
   do not fill absent AI cells with zero or infer metro-specific usage.
9. Check numeric ranges; retain and flag unusual observations rather than cap
   or remove them. AEI mean units differ, so do not apply percent bounds to means.
10. Reconcile selected/excluded rows, numeric totals and nonmissing denominators;
    do not claim published detailed employment sums equal a complete state total.
    Do not sum repeated state-level Claude shares over BLS areas.
11. Deterministically select up to 50 complete cleaned joined rows: include
    suppressed employment, suppressed/top-coded wage, unmatched AI, and
    multi-code aggregation cases if present, then fill in sorted key order.
    This is an inspection sample, not a representative statistical sample.
12. Independently trace five original-to-cleaned records, including difficult
    cases. Run twice in separate processes; compare output hashes. Execute
    the notebook from a fresh kernel. Report unresolved issues honestly.

## Revision log

- Initial plan: above. No cleaning transformations had run when this file was written.
- Any later revision must be appended here with its reason and effect.
- Implementation-only correction: simplified the excluded-non-CA count expression
  without changing any selected rows or analytical rules.
- Post-run observation: BLS retained 11,847 rows, with 215 missing employment and
  169 missing annual median wages. The provisional join has 5,387 unmatched rows.
  These were retained as planned; no rule was changed to improve match rates.
