# Data-cleaning plan

## Goal

Create a reproducible table for ranking metropolitan or nonmetropolitan area by six-digit SOC occupation combinations using state-level Claude usage and local BLS workforce measures.

## Intended grains and keys

- Anthropic filtered table: one published state by O\*NET-SOC occupation row.
- AI aggregate: one state by six-digit SOC row; key `state + soc6`.
- Final table: one area type by BLS area by six-digit SOC row; key `area_category + AREA + OCC_CODE`.

## Planned stages

1. Verify the four expected source files and keep them read-only.
2. Read the Anthropic CSV in chunks; inventory source rows, missing values, dates, and exact duplicates.
3. Filter one period, U.S. subregions, `soc_occupation`, hierarchy level 0, and `pct`.
4. Read O\*NET Occupation Data; validate and join exact eight-digit codes.
5. Derive six-digit SOC and aggregate Claude usage within state and six-digit SOC.
6. Read BLS MSA and BOS tables; label area type and retain cross-industry, all-ownership, detailed occupations.
7. Preserve BLS special symbols as flags before numeric conversion.
8. Left-join BLS to AI with many-to-one validation using `PRIM_STATE + OCC_CODE` to `state + soc6`.
9. Reconcile before/after counts, duplicate keys, missingness, ranges, and unmatched records.
10. Run five record checks written as original, expected, actual, and pass/fail.
11. Create a deterministic sample of no more than 50 difficult cases.
12. Save the audit, sample, checks, and reproducible full outputs.

## Non-negotiable controls

- Do not modify or overwrite raw files.
- Do not drop a row without reporting the rule and count.
- Do not silently alter identifiers, units, geography, or categories.
- Do not treat missing or suppressed values as zero.
- Flag suspicious values before deciding how to handle them.
- Stop the pipeline if declared merge relationships or unique keys fail.
