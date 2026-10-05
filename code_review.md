# Completed code review

Reviewed `clean_source_data.py`, `write_cleaning_report.py`, `validate_cleaned_data.py`, and `tests/test_clean_source_data.py` after the first full source-data run. The review was performed by the same coding assistant, followed by a separate validation program; this was not an independent human or second-agent review.

## Findings and corrections

1. Corrected backslash escaping in generated PowerShell instructions and compiled the Python files with syntax warnings treated as errors.
2. Added explicit rejection of missing BLS keys/titles and fractional hierarchy levels, so invalid identifiers cannot slip into joins through permissive conversions.
3. Required the expected April and May 2026 dates before assigning month labels. This prevents a different two-month input from being mislabeled.
4. Counted unmatched AI identifiers by distinct full code, rather than distinct code/title pairs.
5. Checked that `#` wages are stored as lower bounds with a missing exact value; unknown numeric tokens raise an error. No zero-filling or averaging of incompatible occupational percentages is performed.
6. Verified the output grain: the main table is unique on area × published BLS occupation, while O*NET extensions remain in a separate bridge and AI table. Many-to-one joins preserve employment row counts and values.
7. Reviewed metric semantics against the supplied fields and release documentation: work use is not task change, usage share is not job exposure, and global measures are labeled global. No task-importance or exposure values were fabricated.
8. Confirmed all original source rows are retained in the full clean tables. Geographic/occupation filters apply only to analytical subsets. Source files are fingerprinted before and after processing.

## Verification performed

- Reran the complete pipeline after corrections against all four supplied raw files.
- Ran 9 regression tests for censoring, missingness, identifier preservation, unknown/invalid numeric values, duplicate conflicts, and geographic/period keys.
- Ran 46 independent output checks, including raw-file hashes, per-cell employment/wage reconciliation, independent recomputation of work-use ranges from the long AI data, preservation of nulls, and CSV/Parquet identifier consistency.
- Compiled all four Python files with syntax warnings treated as errors.
- Checked local links in the generated assignment answers and dictionary.

The completed run passed these checks. The detailed validation results are in [validation_results.json](data/cleaned/validation_results.json).

## Remaining analytical limitations

The four inputs do not contain O*NET task importance, a task-to-occupation bridge, the separate observed-exposure dataset, employment projections, an official taxonomy crosswalk, RPU-compatible employment, or Accenture internal records. Prefix matches are documented as provisional context links. These limitations cannot be fixed by code or inferred values; they are described in [cleaning_answers.md](cleaning_answers.md). Passing validation does not certify upstream data accuracy or make the descriptive tables causal evidence.
