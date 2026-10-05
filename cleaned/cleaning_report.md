# Dataset cleaning report

## Output and method

Cleaned copies are in this `cleaned` folder. All four original files were preserved unchanged. The files were profiled for exact duplicate rows, empty cells, malformed CSV row widths, date/numeric parse failures, and leading/trailing whitespace. Only safe whitespace trimming and exact-duplicate removal were in scope. No such changes were needed, so the source-specific files are faithful copies of their originals.

## Results

| File | Data rows | Exact duplicates removed | Findings / treatment |
|---|---:|---:|---|
| `aei_claude_ai_2026-06-26.csv` | 1,636,573 | 0 | No empty cells, malformed rows, boundary whitespace, or invalid dates/numeric values found. |
| `BOS_M2025_dl.xlsx` | 48,689 | 0 | No duplicate rows or boundary whitespace in the data sheet. Blank fields and status markers were preserved. |
| `MSA_M2025_dl.xlsx` | 150,023 | 0 | No duplicate rows or boundary whitespace in the data sheet. Blank fields and status markers were preserved. |
| `Occupation Data.xlsx` | 1,016 | 0 | No duplicate rows, blank cells, or boundary whitespace found. |

## Preserved values

The BOS and MSA files have expected unpopulated fields: `PCT_TOTAL` and `PCT_RPT` are blank in all data rows; `ANNUAL` is blank in 46,145 BOS / 142,176 MSA rows; `HOURLY` is blank in 48,675 BOS / 149,761 MSA rows. These were not imputed or deleted. OEWS markers such as `*`, `**`, `#`, and `TRUE` were preserved as meaningful nonnumeric/status values rather than coerced.

Workbook sheets and source structure were copied without modification.

`bls_combined.csv` is a derived file that appends the BOS and MSA data sheets and
adds a `SOURCE_WORKBOOK` column to retain provenance. It contains 198,712 data rows;
no occupation or AI-activity join was attempted.
