# Module 6 data-cleaning plan

Prepared from a read-only inspection of the six top-level files in
`C:\Users\Thinkbook\dso576\clean_data`. This plan is written before the
cleaning implementation.

## 1. Goal and project question

**Goal.** Preserve and clean the supplied AI-use, occupational exposure,
employment, wage, and projection data so they can support a reproducible
analysis and dashboard without changing the meaning of the published measures.

**Business question.** The Executive Director of the California Workforce
Development Board must decide which California occupation x region combinations
should be prioritized for AI upskilling and workforce-transition support.

The user selects a California region and sees occupations ranked using observed
AI exposure, employment size, wages, and labor-market outlook. The user can then
open an occupation to examine its AI-use pattern and the tasks that may be
appropriate for training, workflow redesign, or further human review.

The output is a transparent screening shortlist for workforce-planning review.
It is not an automatic funding decision and does not assume that higher AI
exposure necessarily means that a job should be automated.

**Main comparison.** Detailed occupation within each California OEWS region.
The ranking shows employment, annual mean wage, observed exposure, and national
2025-2035 projected employment change separately, as well as a documented
screening score. National projections and AI exposure are contextual evidence,
not measurements of a local causal effect.

## 2. Non-negotiable safeguards

1. Do not overwrite the five source datasets or the assignment PDF.
2. Do not drop a row silently. Every analytical exclusion must appear in an
   exclusion ledger with source file, source row, rule, reason, and count.
3. Do not change a unit or category silently. Retain source values/markers and
   document every derived representation.
4. Flag suspicious values before deciding whether to keep, correct, or exclude
   them. A flag alone is not evidence of an error.
5. Report after every major transformation: input/output rows, changed cells,
   missing values, duplicates, flags, exclusions, and reconciliation checks.
6. Preserve identifier strings and leading zeros. Do not let spreadsheet or CSV
   readers convert codes into dates, numbers, or missing values.
7. No blanket imputation, outlier removal, winsorization, or deduplication.
8. Source-specific missing markers retain their different meanings. A missing or
   censored estimate is never converted to zero.

## 3. Read-only inspection results

| Source | Observed grain and rows | Important findings |
|---|---|---|
| `aei_claude_ai_2026-06-26.csv` | Metric by period, geography, category/hierarchy node; 1,636,573 rows | 0 exact duplicates, 0 duplicate declared keys, 0 missing fields, 0 failed numeric/date parses; 303,138 valid zeros; 73,010 literal `-` node IDs; values 0 to 199.11 across 53 metrics |
| `job_exposure.csv` | Occupation exposure observation; 756 rows | 0 exact duplicates, 32 non-SOC/date-like codes, 17 repeated raw codes, no missing values; exposure 0 to 0.7451 |
| `BOS_M2025_dl.xlsx` | Nonmetropolitan area x industry x ownership x occupation level; 48,689 rows | 0 duplicate declared keys; 760 unavailable employment estimates; wage markers `*` and `#`; 45,542 detailed occupations |
| `MSA_M2025_dl.xlsx` | Metropolitan area x industry x ownership x occupation level; 150,023 rows | 0 duplicate declared keys; 2,939 unavailable employment estimates; wage markers `*` and `#`; 141,015 detailed occupations |
| `occupation.XLSX` | 11 BLS projection tables with different grains | Table 1.2 has 1,112 data rows; other tables are separate selected lists, links, industry data, separations, STEM summary, or occupation-industry narratives; title/footer rows are not observations |
| `Module_6_Homework.pdf` | Assignment instructions | Requires one PDF with 14 checks, a decision log, five record checks, and one checked Codex suggestion. The cleaned sample may contain up to 50 rows. |

## 4. Row definitions and keys

| Output table | One row represents | Expected key |
|---|---|---|
| Claude metrics | One metric for one period, geography, category/hierarchy node | `date_start`, `date_end`, `geo_level`, `geo_id`, `category_name`, `hierarchy_level`, `node_external_id`, `metric_id` |
| Exposure | One supplied occupation exposure record | Source row; valid exact-code join key is unique six-digit `occ_code` |
| OEWS | One release/area/industry/ownership/occupation-level estimate | `release`, `AREA`, `NAICS`, `I_GROUP`, `OWN_CODE`, `OCC_CODE`, `O_GROUP` |
| Projection Table 1.2 | One national occupation or occupation summary | National Employment Matrix code |
| Projection Table 1.12 | One occupation-industry utilization explanation | Occupation code + industry code |
| California screening table | One detailed occupation estimate in one California MSA or nonmetropolitan area | `AREA`, `OCC_CODE` within the cross-industry/ownership scope |

## 5. Column rules

### 5.1 Claude Economic Index

| Column(s) | Rule and reason | Validation |
|---|---|---|
| `date_start`, `date_end` | Strict ISO dates; require `date_end > date_start`; keep as dates internally and ISO text in CSV | Failed parses; observed periods; interval order |
| `geo_id` | Preserve text exactly, including punctuation and country/subregion codes | Blank count; unique count by `geo_level` |
| `geo_level` | Allow supplied `country`, `global`, `subregion`; do not infer a different geography | Unexpected categories |
| `category_name` | Preserve `onet`, `overall`, `request`, `soc_occupation` | Unexpected categories |
| `hierarchy_level` | Nullable integer only after validating values 0-3; preserve raw text | Conversion failures and range |
| `metric_id` | Preserve all 53 metric names; derive `metric_unit` using explicit suffix/name rules | Unknown metrics and unit mapping coverage |
| `value` | Numeric. Do not apply one global range: `_pct` and `pct` are percentage points, times/years and indices have different scales. Keep valid zero | Failed/finite checks; metric-specific min/max; flag negative values and percentage metrics outside 0-100 |
| `node_name` | Preserve narrative text; no case folding or punctuation rewrite | Blank and outer-whitespace counts |
| `node_external_id` | Preserve text. Literal `-` is a published overall/not-applicable identifier, not missing | Count literal `-`; blank count |

No Claude rows will be removed. A gzip CSV is used to reduce output size without
changing values.

### 5.2 Occupation exposure

| Column | Rule and reason | Validation |
|---|---|---|
| `occ_code` | Preserve raw text in `occ_code_raw`; exact six-digit SOC pattern `NN-NNNN` becomes join-eligible. Date-like strings such as `Nov-11` are flagged and not guessed | Valid/invalid counts; duplicates among valid codes |
| `title` | Trim accidental outer whitespace only; preserve wording/case | Before/after examples; blank count |
| `observed_exposure` | Convert to numeric fraction; require 0-1; do not multiply by 100 | Failed conversions, min/max, zero count |
| Derived `code_join_eligible` | True only for valid, unique exact SOC codes | 724 expected valid rows; invalid rows retained |

No exposure rows will be dropped from the cleaned base. Invalid-code rows are
excluded only from exact-code joins and recorded in the exclusion ledger.

### 5.3 OEWS metropolitan and nonmetropolitan files

| Column group | Rule and reason | Validation |
|---|---|---|
| `AREA`, `NAICS`, `OWN_CODE`, `OCC_CODE` | Preserve as text and leading zeros | Pattern/blank checks |
| `AREA_TITLE`, `NAICS_TITLE`, `OCC_TITLE` | Trim outer whitespace only | Changed-cell count and examples |
| `AREA_TYPE`, `I_GROUP`, `O_GROUP` | Preserve source categories; add `area_class` from source file (`metropolitan`/`nonmetropolitan`) | Category sets and counts |
| `TOT_EMP`, `EMP_PRSE`, `JOBS_1000`, `LOC_QUOTIENT` | Convert numeric text. `**` means unavailable, not zero; keep companion status columns | Failed conversions; marker counts; nonnegative checks |
| Wage/statistic fields | Convert numeric text. `*` means unavailable and `#` means censored exact value; both become numeric missing with distinct status values and raw markers retained | Marker counts by column; finite/nonnegative checks |
| `PCT_TOTAL`, `PCT_RPT` | Entirely blank in these files; keep as nullable fields and do not fill | Confirm all missing |
| `ANNUAL`, `HOURLY` | Preserve source marker; derive booleans without treating blank as an error | Unique values and counts |
| Wage percentiles | Preserve hourly and annual units separately; do not use a 2,080-hour conversion | Nondecreasing percentile-order check where all values exist |

The two observation sheets will be appended, not merged, with source and row
lineage. Supporting documentation sheets are not observation rows. All 198,712
observation rows must reconcile before and after cleaning.

### 5.4 BLS projection workbook

| Column group | Rule and reason | Validation |
|---|---|---|
| Sheet title and footer rows | Store as metadata/non-data exclusions; do not treat as observations | Raw-row reconciliation by sheet |
| Codes | Preserve text; apply SOC format only to occupation-code tables, not Table 1.9 industry codes | Key uniqueness by sheet |
| Titles | Preserve original indented title and add trimmed display title | Changed-cell examples |
| Employment and change | Numeric values are thousands of jobs; preserve negative change as valid | `2035 - 2025` reconciliation with rounding tolerance |
| Percent/rate columns | Numeric percentage points, not fractions; negative projected growth may be valid | Failed conversions and documented ranges |
| Wage | Annual dollars; unavailable marks become missing with status | Marker and missing counts |
| Education/experience/training | Preserve valid category `None`; unavailable glyphs remain missing with status | Category lists and summary-row patterns |
| Duplicate OOH headers | Keep both: label and raw link/HTML field; do not overwrite one | Column-count check |
| Tables 1.3-1.6 | Keep as selected lists; do not append to Table 1.2 | Separate outputs |
| Tables 1.8-1.12 | Keep each table's own grain and namespace | Sheet-specific key checks |

## 6. Join and domain decisions

1. Append MSA and BOS OEWS rows after adding `area_class` and `release`.
2. Build the screening table only from `PRIM_STATE = CA`, cross-industry,
   ownership code `1235`, detailed-occupation rows. Inspection found 25
   metropolitan and 3 nonmetropolitan California regions. `PRIM_STATE` is the
   only supplied state-scope field; cross-state coverage not represented by it
   remains a limitation. This is an analytical scope filter, not deletion from
   the cleaned OEWS base. Exclusions are reconciled by rule and count.
3. Join exposure many-to-one using exact six-digit `OCC_CODE = occ_code`. Invalid
   exposure codes remain in the exposure base but cannot join.
4. Join Projection Table 1.2 many-to-one using the exact occupation code.
5. Keep OEWS employment and wages regional, exposure as national occupational
   context, projections as national context, and Claude metrics in a separate
   cleaned table. Do not claim that contextual measures were observed locally.
6. Do not join the 1.6 million Claude metric rows directly to OEWS: its category
   hierarchy and geography do not form a validated one-to-one SOC crosswalk.

### Transparent screening score

The score is calculated only when all four components are present. Within each
California region, each component is converted to a percentile:

- 40% higher observed AI exposure;
- 30% larger regional employment;
- 15% lower annual mean wage, used only as a transparent proxy for transition-
  support need;
- 15% weaker national 2025-2035 employment outlook, also used only as a
  transition-support proxy.

The score is `100 x weighted percentile sum`. Missing components are not
silently reweighted; such records remain visible with no score and an
`insufficient component data` status. Each region receives a rank and a top-25
review flag. All component values and percentiles remain visible so reviewers
can disagree with or replace the weights. The score is a screening aid, not a
funding recommendation or an automation recommendation.

## 7. Outputs to generate after this plan

- `clean_data.py`: one reproducible pandas/openpyxl pipeline.
- `cleaning_assignment.ipynb`: readable notebook that runs the same pipeline and
  presents key evidence.
- `README.md`: simple project structure, run instructions, outputs, and field
  definitions.
- `final_cleaned_sample.csv`: one top-ranked cleaned occupation from each of the
  28 California regions.
- `requirements.txt`: minimal dependencies.
- `outputs/cleaned_*.csv.gz`: cleaned full-source tables.
- `outputs/projections/*.csv`: one cleaned output per data sheet.
- `outputs/analysis_california_occupation_region.csv.gz`: California screening
  table with source metrics, component percentiles, score, rank, and eligibility.
- `outputs/shortlist_top25_by_region.csv` and `region_summary.csv`: dashboard-
  ready review views that remain traceable to the full screening table.
- `outputs/cleaned_sample_max_50.csv`: purposefully selected difficult cases,
  capped at 50 rows and explicitly not a statistical sample.
- `outputs/validation.json`, `stage_changes.csv`, `missing_counts.csv`,
  `duplicates.csv`, `exclusion_ledger.csv`, and `record_checks.csv`.
- `assignment_report.md`: supporting text used inside the notebook for the
  14-item checklist, decision log, five record checks, checked Codex suggestion,
  and limitations.

## 8. Acceptance tests

1. SHA-256 hashes of all five source datasets are unchanged after the run.
2. Claude output has 1,636,573 rows and its declared key remains unique.
3. Exposure output has 756 rows; 32 invalid codes are retained and flagged.
4. OEWS output has 198,712 rows and declared keys remain unique.
5. Source marker counts reconcile to status values; no marker becomes zero.
6. Exact duplicates and repeated IDs are reported separately.
7. All numeric conversion failures are zero or explicitly listed.
8. The California analytical join cannot increase its scoped OEWS row count;
   unmatched keys and match rates are reported.
9. Starting/final rows and important employment totals reconcile by stage.
10. Five predeclared difficult records show original, expected, actual, and pass.
11. A fresh run from the original files recreates the same semantic results.
12. The <=50-row sample includes invalid codes, unavailable employment, censored
    wages, a valid zero, high Claude metric values, metropolitan and
    nonmetropolitan records, and negative projected growth.

## 9. Decisions documented for the final submission

- The score uses the stated 40/30/15/15 weights. Lower wage and weaker outlook
  are transparent transition-support proxies, not automatic funding rules.
- The 32 malformed exposure codes are preserved and flagged. They are not
  guessed because the source does not provide an authoritative mapping.
- The final shortlist supports human review and does not recommend automatic
  job automation.
