# Cleaning decision log

Each entry states the rule, why it is appropriate, and how the pipeline checks it.

## General controls

### G1 - Preserve sources

- **Rule:** Keep original source files unchanged; write outputs to separate folders.
- **Reason:** Preserves provenance and recovery.
- **Check:** The script only reads the four source paths and writes under the selected output root.

### G2 - Explain row removal

- **Rule:** Do not drop rows without naming the filter and reporting before/after counts.
- **Reason:** A removed row may be a valid observation.
- **Check:** `cleaning_audit.json` records source, filtered, removed, and final counts.

### G3 - Preserve meaning

- **Rule:** Do not silently change units, identifiers, geography, or categories.
- **Reason:** Undocumented recoding changes the phenomenon being measured.
- **Check:** Raw BLS symbol fields are retained, codes stay strings, and standardized fields have new names.

### G4 - Flag before changing

- **Rule:** Flag suspicious values before deciding whether to remove or modify them.
- **Reason:** Unusual does not necessarily mean incorrect.
- **Check:** Range failures, invalid codes, special symbols, and multistate MSAs receive counts or flags.

## Anthropic and occupation rules

### A1 - Select one comparable slice

- **Rule:** Keep 2026-05-01 through 2026-06-01, U.S. `subregion`, `soc_occupation`, hierarchy 0, and `pct` rows.
- **Reason:** Prevents mixing periods, countries, taxonomies, hierarchy levels, and metrics.
- **Check:** The audit records the retained filter values, 7,294 rows, 52 subregions, and 462 occupations.

### A2 - Name the metric conservatively

- **Rule:** Rename `value` to `claude_usage_pct` and call it Claude usage share.
- **Reason:** It is not a worker adoption rate or causal AI-exposure measure.
- **Check:** Require numeric values from 0 through 100 and review output labels.

### A3 - Do not manufacture unpublished cells

- **Rule:** Do not generate missing state-occupation combinations or fill them with zero.
- **Reason:** Publication thresholds make absence different from zero.
- **Check:** Report the published occupation count and published percentage sum for every state.

### O1 - Map exact O\*NET codes

- **Rule:** Join Anthropic `node_external_id` to O\*NET-SOC Code by exact eight-digit code.
- **Reason:** Codes are more stable than occupation titles.
- **Check:** Validate many-to-one; all 7,294 rows must match.

### O2 - Derive six-digit SOC only after validation

- **Rule:** Preserve the eight-digit O\*NET code and derive `soc6` only from a valid `XX-XXXX.XX` code.
- **Reason:** BLS uses six-digit SOC while O\*NET adds detailed extensions.
- **Check:** Every derived code must match `XX-XXXX`.

### AG1 - Aggregate extensions within state and SOC

- **Rule:** Sum `claude_usage_pct` by `state + soc6` and count contributing extensions.
- **Reason:** Multiple O\*NET extensions may map to one six-digit BLS occupation.
- **Check:** Require a unique aggregate key and reproduce the CA 11-3031 sum in record check 2.

## BLS and merge rules

### B1 - Keep comparable detailed BLS records

- **Rule:** Label MSA as metropolitan and BOS as nonmetropolitan; retain cross-industry, all-ownership, detailed occupations.
- **Reason:** Avoids mixing detailed rows with totals or major occupation groups.
- **Check:** Reconcile 150,023 MSA rows to 141,015 retained and 48,689 BOS rows to 45,542 retained.

### B2 - Preserve unavailable values

- **Rule:** Treat `**` as unavailable employment and `*` as unavailable wage; convert to missing with flags.
- **Reason:** These symbols are not zeros.
- **Check:** Reconcile original symbol counts to the resulting flags and missing numeric values.

### B3 - Preserve top coding

- **Rule:** Convert `#` to a top-coded wage flag and do not invent an exact wage.
- **Reason:** BLS defines it as a value at or above its publication threshold.
- **Check:** Require numeric wage to be missing whenever `wage_topcoded=True`.

### M1 - Use a validated left join

- **Rule:** Left-join BLS to AI on `PRIM_STATE + OCC_CODE = state + soc6` with many-to-one validation.
- **Reason:** Many areas may share one state-occupation AI signal, while all BLS rows must remain available.
- **Check:** Reconcile 186,557 rows before and after; report 49,866 matched and 136,691 unmatched rows; require zero duplicate final keys.

### M2 - Flag multistate approximations

- **Rule:** Use BLS `PRIM_STATE` for multistate MSAs and set `is_multistate_msa=True`.
- **Reason:** BLS workforce estimates cover the entire MSA but the AI signal is state-level.
- **Check:** Count multistate MSA rows and include them in the sample.

## Validation and output rules

### V1 - Audit every major transformation

- **Rule:** Report row counts, missingness, duplicates, and numeric ranges.
- **Reason:** Code running without an error does not establish correctness.
- **Check:** Save `reports/cleaning_audit.json` after the full run.

### V2 - Enforce the final key

- **Rule:** Require `area_category + AREA + OCC_CODE` to be unique.
- **Reason:** This is the dashboard row definition.
- **Check:** Stop the pipeline if any duplicate final-key rows remain.

### V3 - Retain unmatched BLS rows

- **Rule:** Keep BLS rows without an Anthropic match and leave `claude_usage_pct` missing.
- **Reason:** An unmatched cell may be unpublished rather than invalid.
- **Check:** Preserve the BLS row count and report match status by area type and state.

### V4 - Submit difficult cases

- **Rule:** Create a sample of at most 50 unique records, emphasizing difficult cases.
- **Reason:** Gives the instructor inspectable evidence without submitting the full large result.
- **Check:** Include matched, unmatched, suppressed, top-coded, metropolitan, nonmetropolitan, and multistate cases.
