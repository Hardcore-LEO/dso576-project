# AI Workforce Investment Planner

**Student:** Hehua (Leo) Liu - confirmation pending  
**Branch:** `Leo`  
**Branch URL:** [https://github.com/Hardcore-LEO/dso576-project/tree/Leo](https://github.com/Hardcore-LEO/dso576-project/tree/Leo)  
**Submitted commit:** `4993964fc785f73b9c518b49223af6b6d6192f68`

## Project goal

This project cleans the supplied AI-use, occupational exposure, employment,
wage, and employment-projection data. The final analysis supports this business
question:

> Which California occupation x region combinations should be prioritized for
> AI upskilling and workforce-transition support?

The result is a screening shortlist for human review. It is not an automatic
funding decision and does not assume that a job with higher AI exposure should
be automated.

## Data sources and versions

- `aei_claude_ai_2026-06-26.csv`: Anthropic Economic Index snapshot dated
  2026-06-26.
- `job_exposure.csv`: course-provided occupation AI-exposure file; the supplied
  file does not state a separate version or download date.
- `MSA_M2025_dl.xlsx`: BLS OEWS metropolitan estimates, May 2025.
- `BOS_M2025_dl.xlsx`: BLS OEWS nonmetropolitan estimates, May 2025.
- `occupation.XLSX`: BLS Employment Projections, 2025-2035 projection period.

All five files were supplied in the course project folder. Their sizes and
SHA-256 hashes are saved in `outputs/source_manifest.json` so the submitted
versions can be verified.

## Submission files

```text
module6_submission/
|-- cleaning_assignment.ipynb       Executed, template-style cleaning notebook
|-- README.md                       Project structure and instructions
|-- final_cleaned_sample.csv        28-row sample of the final cleaned data
|-- clean_data.py                   Reproducible cleaning functions
|-- execute_notebook.py             Builds and executes the notebook
|-- plan.md                         Cleaning rules written before coding
|-- record_expectations.json        Expected results for five record checks
|-- requirements.txt                Python dependencies
|-- test_clean_data.py              Automated validation tests
|-- assignment_report.md            Supporting checklist and evidence text
`-- outputs/
    |-- analysis_california_occupation_region.csv.gz
    |-- shortlist_top25_by_region.csv
    |-- region_summary.csv
    |-- cleaned_claude_metrics.csv.gz
    |-- cleaned_job_exposure.csv
    |-- cleaned_oews.csv.gz
    |-- cleaned_sample_max_50.csv
    |-- projections/
    `-- validation and audit files
```

## Data flow

```text
Original files
    -> inspect columns and types
    -> clean each source separately
    -> keep missing-value markers and suspicious-value flags
    -> select California detailed occupations
    -> join exposure and employment projections by SOC occupation code
    -> calculate the four-component screening score within each region
    -> validate row counts, joins, totals, duplicates, and five records
    -> save the final analysis and sample
```

## Main cleaning methods

The notebook uses common pandas methods suitable for an introductory Python
course:

- `pd.read_csv()` and `pd.read_excel()` to load the files.
- `.str.strip()` to remove outside spaces from display text.
- `pd.to_numeric()` to convert employment, wage, exposure, and projection data.
- `.replace()` and status columns to preserve special missing-value meanings.
- `pd.concat()` to append metropolitan and nonmetropolitan OEWS records.
- `.merge()` to join tables by exact SOC occupation code.
- `.groupby()` and `.rank()` to calculate within-region percentiles and ranks.
- `.isna()`, `.duplicated()`, and `assert` statements to validate the results.

No raw source file is overwritten. Suspicious records are flagged before a
decision is made, and rows are not removed without a documented reason.

## Screening score

The score is calculated only when all four components are present:

- 40% observed AI exposure
- 30% regional employment
- 15% lower annual wage as a transition-support proxy
- 15% weaker national employment outlook as a transition-support proxy

The components are converted to percentiles within each California region.
Rows with missing components remain in the final analysis but do not receive a
score.

## Final cleaned sample

`final_cleaned_sample.csv` contains the top-ranked complete-data occupation in
each of the 28 California regions. This provides a small, readable sample of the
final occupation x region table. It is not a replacement for the full analysis.

Important columns:

| Column | Meaning |
| --- | --- |
| `AREA`, `AREA_TITLE` | California region identifier and name |
| `area_class` | Metropolitan or nonmetropolitan area |
| `OCC_CODE`, `OCC_TITLE` | SOC occupation code and occupation name |
| `observed_exposure` | Observed AI exposure from the supplied exposure file |
| `TOT_EMP` | May 2025 regional employment estimate |
| `A_MEAN` | May 2025 annual mean wage in dollars |
| `projected_employment_change_pct_2025_35` | National projected employment change in percentage points |
| four percentile columns | Within-region score components |
| `screening_score` | Weighted score from 0 to 100 |
| `screening_rank_within_region` | Rank within the selected region |
| `screening_status` | Whether all four score components were available |

## Key results

- Claude metrics retained: 1,636,573 rows
- Occupation exposure retained: 756 rows
- Malformed exposure codes flagged: 32 rows
- OEWS records retained: 198,712 rows
- California occupation x region records: 11,847 rows
- Records eligible for a screening score: 9,829 rows
- Records retained without a score: 2,018 rows
- California regions: 28
- Predeclared record checks passed: 5 of 5

## How to run

Run the following commands from the `module6_submission` folder:

```powershell
python -m pip install -r requirements.txt
python execute_notebook.py
python -m unittest -v test_clean_data.py
```

`execute_notebook.py` rebuilds the notebook, runs every code cell in order, and
saves the displayed tables inside `cleaning_assignment.ipynb`. Each source
section follows the same pattern: original-data checks, cleaning rules, cleaned
examples, row-count reconciliation, and a short summary. The detailed cleaning
functions stay in `clean_data.py` so the notebook remains easy to read.

## Limitations

- The 32 malformed occupation codes are preserved and flagged because the
  supplied data do not provide enough information for a reliable correction.
- AI exposure and employment projections are national occupation context, not
  California-specific causal estimates.
- Missing, unavailable, and censored OEWS values are not treated as zero.
- The screening weights are transparent planning assumptions and can be changed
  after human review.
