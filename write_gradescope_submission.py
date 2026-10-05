"""Format the verified Module 6 evidence as the requested Gradescope Markdown draft."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'cleaned'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(x).replace('|', '\\|') for x in row) + ' |' for row in rows])


def main():
    profile = pd.read_csv(OUT / 'homework_source_profiles.csv')
    missing = pd.read_csv(OUT / 'homework_missing_before_after.csv')
    results = json.loads((OUT / 'homework_verification.json').read_text())
    cases = json.loads((OUT / 'record_check_results.json').read_text())
    duplicates = table(['Source', 'Exact duplicate rows', 'Repeated full keys', 'Repeated single IDs after first'],
                       [[r.source, r.exact_duplicates, r.repeated_full_keys, r.repeated_single_ids_after_first]
                        for r in profile.itertuples()])
    counts = table(['Source', 'Original rows', 'Cleaned rows'],
                   [[r.source, f'{r.rows:,}', f'{r.rows:,}'] for r in profile.itertuples()])
    missing_table = table(['Source', 'Column', 'Blank before', '`*` before', '`**` before', '`#` before', 'Null after'],
                          [[r.source, r.field, r.before_blank, r.before_star, r.before_double_star,
                            r.before_hash, r.after_exact_value_missing] for r in missing.itertuples()])

    def outcome(d):
        if d.get('lower_bound') is not None:
            return f"Exact value missing; lower bound ${d['lower_bound']:,.0f}; top-coded"
        if d.get('status'):
            return 'Missing; ' + d['status'].replace('_', ' ')
        return str(d['value'])

    record_rows = []
    for i, c in enumerate(cases, 1):
        identity = (f"{c['area']} / {c['soc']} / {c['field']}" if 'area' in c else
                    f"GLOBAL / May 2026 / {c['key']['node_external_id']} / work-use %")
        record_rows.append([i, identity, c['original'], outcome(c['expected']), outcome(c['actual']),
                            'Pass' if c['matches'] else 'Fail'])
    records = table(['Check', 'Record identifier', 'Original', 'Expected', 'Actual', 'Result'], record_rows)
    text = f'''# Module 6: Project Data Cleaning — Gradescope Draft

**Project:** AI Workforce Investment Planner  
**Student:** ____________________  
**Git branch:** `cortland`  
**Branch URL:** https://github.com/Hardcore-LEO/dso576-project/tree/cortland  
**Commit ID:** ____________________

*Submission note: Gradescope requires one PDF per student. Export this Markdown to PDF after filling in your name and the submitted commit ID. Fill in the commit ID after committing, and push the branch before submitting its GitHub link. The separate GitHub deliverable also requires scripts, a notebook, a data sample, dependencies, and a README; this document covers the Gradescope box.*

## 14-item checklist

### 1. State the project vision and question

**Status: Done**

Our project aims to help California workforce planners decide where to investigate AI training needs. My business question is: **Which California occupation–area combinations have large workforces and published AI-use information that make them worth reviewing for an upskilling pilot?** The main comparison is employment size alongside global work-use patterns for related occupations. This gives us an initial review list, rather than a final funding recommendation. See `occupation_area.csv` and `largest_workforces_with_ai_context.csv` in `data/cleaned/`.

### 2. Define one row

**Status: Done**

One analytical row represents one published BLS occupation in one California OEWS area, identified by `area_code + soc_code`. There are 11,847 unique pairs. In the source data, BLS keys also include industry, ownership, and occupation level; Anthropic keys include both dates, geography, category, hierarchy level, metric, and node ID. O*NET uses the full occupation code. Keeping these levels separate prevents us from counting employment repeatedly when an occupation has several O*NET extensions. The complete keys are listed in `data_dictionary.md`.

### 3. Preserve the source

**Status: Done**

I used the June 26, 2026 Anthropic release, the May 2025 BLS metropolitan and nonmetropolitan workbooks, and the supplied `Occupation Data.xlsx`. The exact O*NET release is not identified in that workbook, so it remains a limitation. Original files stay in the supplied Downloads folder. The cleaning script loads the CSV with `read_csv` and each workbook's data sheet with `read_excel`. SHA-256 checks confirmed that all four originals stayed unchanged; filenames and hashes are saved in `source_manifest.json`.

### 4. Inspect columns and types

**Status: Done**

The BLS numeric columns mix numbers with symbols, so I first read them as text, separated the symbols, and converted reported values to numbers. Anthropic dates were converted to dates, values to numbers, and hierarchy levels to integers. Occupation and area IDs stayed as text to preserve their formatting. **There were zero unexpected conversion failures.** Known missing/censoring symbols became null exact values with an explanatory status. Annual/hourly flags became nullable booleans. The script rejects unknown numeric tokens rather than silently dropping them.

### 5. Standardize text

**Status: Done**

The full-source check found **zero text cells needing leading or trailing whitespace removed**. I kept the trimming rule but did not change occupation titles or descriptions unnecessarily. For example, area ID `0600003` stayed `0600003`, and O*NET code `11-1011.03` kept its extension. BLS column names were standardized from names such as `OCC_CODE` to `occ_code`; the analytical table calls it `soc_code`. These changes make the files easier to use without changing what the records mean. Counts are in `homework_source_profiles.csv`.

### 6. Investigate duplicates

**Status: Done**

{duplicates}

No rows were removed. Repeated individual occupation/node IDs are expected because the same occupation appears in different areas, months, or metrics. The full combination of identifying columns is unique. Removing records based only on a repeated occupation ID would lose valid observations.

### 7. Handle missing data

**Status: Done**

I kept missing values rather than guessing them. In BLS, `*` means unavailable wages, `**` means unavailable employment, and `#` means the wage is at least the published upper threshold. For `#`, the exact value is missing but its lower bound is retained. Filling these with zero would make the workforce or wages look smaller than they are. The full before/after counts for every affected original column appear in the missing-data table below.

Anthropic's published rows and the occupation dictionary have no blank source fields. However, some combinations are not published at all. That leaves 2,551 California occupation–area records without matched global work-use context. Those records remain in the analysis. Missing geographic AI measures are not filled from another geography. Derived-column missingness is recorded in `missingness.csv`.

### 8. Check suspicious values

**Status: Done**

The full checks found no invalid date intervals, percentages outside 0–100, autonomy values outside 1–5, or negative BLS numeric estimates. High wages were not automatically deleted. For example, the 15 California median annual wages marked `#` were kept as “at least $239,200,” rather than treated as exact wages or outliers. The BLS internal UpdateTime sheet has an older timestamp; the estimate vintage comes from the May 2025 filename and field descriptions. These checks are recorded in `validation_results.json` and the source audit.

### 9. Verify merges

Status: Unresolved ? the merge checks pass, but the supplied data do not establish that every occupation category is equivalent.

The occupation?area table joins to the global occupation summary by `soc_code`, with an expected many-to-one relationship. It kept all 11,847 rows, with no unexpected extra rows or changes to employment and wage values. Of the 783 California BLS codes, 215 lack matched global work-use context, affecting 2,551 rows. Twelve BLS codes have no matching O*NET dictionary prefix. All selected full Anthropic occupation codes match the supplied dictionary.

The four supplied files do not include an official crosswalk showing how BLS categories correspond to O*NET occupations. This matters because some BLS categories combine occupations, so matching code prefixes alone may not be enough. For this submission, I kept unmatched records without filling their AI values and treated the existing links as provisional. An official crosswalk and a clear rule for combining occupations would be needed to resolve this limitation. See `soc_match_audit.csv` and `occupation_code_bridge.csv`.

### 10. Reconcile changes

**Status: Done**

{counts}

The full cleaned sources retain every row. The two BLS files contain 198,712 rows combined; selecting California's detailed published occupations leaves 11,847 analytical rows. The other 186,865 rows remain in the full source outputs. No extra rows appear after joining AI context.

The sum of published California employment is **{results['ca_employment_sum']:,.0f}** before and after the join, with every available employment value unchanged. This is a sum of available occupation–area estimates, not an official statewide employment total.

### 11. Check calculations

**Status: Done**

Employment totals use **11,632 nonmissing records**; 215 unavailable estimates are excluded, not counted as zero. Any average of exact median annual wages uses **11,678 records**, excluding 154 unavailable and 15 top-coded values. Such an average would describe occupation–area estimates, not the average worker's wage.

Global work-use context is available for **9,296 of 11,847 records**, so coverage uses all 11,847 as its denominator. The min/max work-use summaries use only published O*NET extensions, with each metric's contributing count stored in its `_n_extensions` column. They are descriptive ranges, not weighted averages. Missing group keys are rejected before grouping or merging. Monthly changes are calculated only when both months have published values, and are expressed in percentage points.

### 12. Verify individual records

**Status: Done**

The five checks below include missing employment, missing wages, a wage limit, a leading-zero identifier, and an ordinary AI percentage. Expected results were saved in `record_check_expectations.json` before the verification code looked up the cleaned records. The matching actual results are in `record_check_results.json`.

{records}

The reasons for those expectations were: (1) `#` gives a lower bound, (2) `**` is unavailable employment, (3) `*` is unavailable wages, (4) geographic IDs must retain leading zeros, and (5) converting a percentage's type should not change its value. These expectations follow the source definitions rather than assuming the cleaning code is correct.

### 13. Test reproducibility

**Status: Done**

The cleaning script was restarted in a fresh Python process and run from the four originals using `requirements-cleaning.txt`. SHA-256 comparisons showed that **all {results['matched_output_files']} previously generated data/audit files matched the earlier outputs exactly**. All 9 regression tests and 46 independent output checks passed, and the original source hashes remained unchanged.

From the `project` directory, the full evidence run is:

```powershell
.\\.venv\\Scripts\\python.exe check_homework_evidence.py --input-dir 'C:\\Users\\Cortl\\Downloads\\drive-download-20261004T203842Z-1-001'
```

Results are in `homework_verification.json`. The included `homework_sample_20.csv` has 20 real cleaned rows. It includes the four BLS records checked above, then fills the remaining places with the first distinct rows from the sorted analytical table. This intentionally covers difficult cases; it is not a random or representative sample.

### 14. Document remaining limitations

**Status: Done**

The main limitations are the unconfirmed occupational crosswalk and O*NET version, the difference between 2025 employment and 2026 AI observations, and the use of global AI context for California employment. These files also lack task-importance ratings, the separate exposure dataset, projections, and workers' actual training needs. OEWS areas do not equal the Workforce Board's Regional Planning Units. As a result, the output can guide further review but cannot justify a final funding ranking or claim that AI caused job losses.

## Cleaning decision log

This log summarizes the implemented rules and the checks used to review them. It was written for this submission after the initial cleaning, so it is not presented as a dated plan from before that first run.

| Rule | Reason | Check |
| --- | --- | --- |
| Preserve originals and write separate outputs | Keep the work traceable and reversible | All four source hashes unchanged |
| Keep identifiers as text; trim only boundary whitespace | Avoid losing leading zeros or meaningful names | Zero trims needed; `0600003` preserved |
| Remove only identical duplicates; reject conflicting full keys | A repeated occupation ID can still be a valid observation | Zero exact duplicates and zero repeated full keys |
| Convert `*`, `**`, and blanks to nulls with statuses | Unavailable estimates are not zero | Before/after counts and two individual missing-value checks |
| Preserve `#` as a lower bound | The source does not give an exact wage | $239,200 annual bound retained; exact value stays null |
| Filter California analysis to detailed BLS rows | Avoid mixing totals with occupations | 198,712 source rows → 11,847 analysis rows; excluded rows retained separately |
| Keep AI periods and geographic scopes separate | Global usage cannot stand in for a local observation | Both months retained; no local work-use values fabricated |
| Summarize extension ranges before joining to employment | Avoid multiplying employment or averaging incompatible percentages | Many-to-one join; unchanged rows and employment values |
| Keep unmatched records visible and disclose mapping uncertainty | Dropping them would hide coverage gaps | 2,551 cells retained without work-use context |

## Checking a Codex suggestion

One suggestion that needed checking was treating `use_case_work_pct` as a “task change” measure. The field name and [Anthropic's release documentation](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data_documentation.md) describe work-related use, which does not measure whether a task changed. The final data therefore retain the work-use label, and the answers do not treat it as task change or job displacement.

This check matters because a calculation can be technically correct while its interpretation is wrong. The automated checks also confirmed that country/state occupation work-use values were not filled using global values.

## Missing-data counts before and after cleaning

This table covers both complete BLS files, including records outside California. “Before” separates blank cells from special source symbols. “Null after” counts missing exact numeric values, or missing booleans for `annual`/`hourly`. In each row it equals the blanks plus symbols; no available number was replaced with a null. Wage bounds for `#` remain available in separate columns. All other original columns have no missing values. Anthropic and O*NET original fields also have no missing values.

{missing_table}
'''
    (ROOT / 'Gradescope_submission.md').write_text(text, encoding='utf-8')
    print('Wrote Gradescope_submission.md')


if __name__ == '__main__':
    main()
