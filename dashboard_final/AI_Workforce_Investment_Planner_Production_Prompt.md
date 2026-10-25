# AI Workforce Investment Planner — Production Dashboard Build Specification

## 1. Objective and deliverables

Build a complete, locally running **production-data dashboard** titled **AI Workforce Investment Planner** using the supplied cleaned workbook `final_cleaned_core.xlsx`. All charts, scores, region summaries, and occupation–area rankings must derive from this workbook and the explicitly documented score calculation below. **Do not use synthetic rows, fabricated scores, or placeholder chart data.** Use Streamlit + Plotly and processed Parquet tables. Provide reproducible data processing, scoring implementation, dashboard, tests, documentation, and instructions for running locally. The purpose is to identify occupation–area combinations worth further workforce-transition assessment, not to automatically approve investment or predict AI-caused displacement.

Keep the UI focused on precisely these sections, in this order:
1. Title: **AI Workforce Investment Planner**.
2. **Scope, Releases and Limitations**.
3. **What Does the Priority Score Mean?**
4. **Priority Score Distribution**.
5. **California Area Map (Map & Regional Ranking View)**.
6. **Ranked Occupation × Area Records**.

Do not add unrelated analytics sections, global filters, augmentation/automation measures, occupation tasks, national openings, or KPIs requiring unavailable data.

## 2. Canonical input and validated facts

Input workbook: `final_cleaned_core.xlsx`, worksheet `cleaned_data`. There are 11 fields, in order:

| Field | Meaning / type |
|---|---|
| `release` | BLS data release label; string |
| `area_class` | metropolitan / nonmetropolitan; string |
| `AREA` | BLS area identifier; string (retain leading zeroes) |
| `AREA_TITLE` | display area title; string |
| `OCC_CODE` | SOC occupation identifier; string |
| `OCC_TITLE` | occupation title; string |
| `job_exposure` | Claude Global Job Exposure; numeric |
| `claude_usage_pct` | Claude CA PCT; original numeric **percentage-point** values, not a unit interval by assumption |
| `TOT_EMP` | BLS published employment; numeric |
| `A_MEAN` | BLS mean annual wage, USD; numeric |
| `employment_change_pct` | BLS projected employment change, percentage points; numeric |

Observed workbook audit (verify independently before building): 11,847 rows; 28 distinct `AREA` values; 783 distinct `OCC_CODE` values; one release `May 2025`; no duplicate `(release, AREA, OCC_CODE)` records. Missing numeric fields: `job_exposure` 1,037 (8.75%); `claude_usage_pct` 5,387 (45.47%); `TOT_EMP` 215 (1.81%); `A_MEAN` 169 (1.43%); `employment_change_pct` 0. Exactly 6,123 rows have all five numeric metrics available (51.7%). Verify actual coverage after loading; fail loudly if unexpectedly different rather than silently changing definitions.

Important: `claude_usage_pct` contains values up to approximately **9.04**, and **must not be blindly multiplied by 100**. Source indicates `pct` is expressed in percentage points. Display and document units unambiguously, e.g. an original value of `0.16` corresponds to `0.16%`, not `16%`. Keep raw values intact. Likewise `employment_change_pct = -6.0` means `-6.0%`. Preserve `job_exposure` in its original scale and apply appropriate numeric formatting.

Use the workbook as the only authoritative data for numerical results. Never fabricate source values or fill geographical coverage gaps. Preserve raw source columns in processed outputs. Validate all numerics, unique keys, supported area classes, and the source-to-output row count. Do not assume the release for projected employment is identical to the wage/employment observation release; identify and disclose projection horizon from confirmed metadata if available; otherwise label it only as `employment_change_pct` and document that its source horizon needs confirmation.

## 3. Missing data: strict and transparent policy

- Distinguish genuinely missing or suppressed values from numeric zero. Valid zeros (such as `job_exposure = 0`) **must remain zero**.
- Do **not** impute `claude_usage_pct` or `job_exposure` with zero, global mean, group mean, arbitrary constants, or model predictions. The high, potentially systematic missingness of `claude_usage_pct` makes imputed rankings misleading.
- Do **not** impute `TOT_EMP` or `A_MEAN` to compute the official score; do not impute `employment_change_pct` if absent.
- Calculate the official score only for rows with all five numeric fields present, finite, and valid (`TOT_EMP > 0`, `A_MEAN > 0`, exposure and usage nonnegative). Set all score components, final score and global rank to `null` for incomplete/ineligible rows. Set `score_status = 'Insufficient Data'`, or a precise validation status for invalid values. For eligible rows use `score_status = 'Scored'`.
- Keep **all original rows** in the processed occupation–area table; do not delete records merely because score is unavailable. Show em dash / `Not scored` for missing values, display status and an explanation in the table and the limitations section.
- Report scored and unscored counts, field-wise missingness, and coverage by area. Do not claim complete regional coverage.
- Use only eligible rows to establish percentile reference distributions. Persist the reference definition and coverage with the score version so results are reproducible.
- Do not change scoring weights or redistribute weights dynamically for rows missing components. Never compare scores computed with different component sets under the same version.

## 4. Official, implementable Priority Score v1.0

**Definition:** `Workforce Transition Priority Score v1.0` is a transparent **relative prioritization index**, scaled approximately 0–100, indicating where a combination of AI exposure / observed Claude usage, workforce scale, wage level, and weaker projected employment outlook suggests further workforce-transition investigation. It is **not** a causal measure of AI displacement, a probability, or an automatic funding recommendation. Higher scores indicate higher screening priority under this explicit policy framework. Weights are proposed **policy assumptions**, not statistically optimized or independently validated effects; present them as such and test sensitivity.

For the scored reference population (all complete eligible California occupation × area rows for the input release), calculate percentile ranks using a single consistent, documented tie convention such as pandas `rank(method='average', pct=True) * 100`. Do not recompute percentiles or scores when users filter the records table. Components:

1. `exposure_component = percentile(job_exposure)`; higher = higher priority; weight **0.30**.
2. `usage_component = percentile(claude_usage_pct)`; higher = higher priority; weight **0.15**.
3. `employment_component = percentile(log1p(TOT_EMP))`; higher employment = larger workforce reach; weight **0.30**.
4. `wage_component = percentile(A_MEAN)`; higher wages = greater earnings magnitude potentially affected; weight **0.10**.
5. `outlook_component = percentile(-employment_change_pct)`; lower projected growth = higher vulnerability subscore; weight **0.15**.

Calculate without intermediate rounding:

`priority_score = 0.30*exposure_component + 0.15*usage_component + 0.30*employment_component + 0.10*wage_component + 0.15*outlook_component`

Do not claim that employment decline is caused by AI. The use of higher wage and higher observed usage as priority-increasing indicators is an explicit modeling choice, not a proven relationship. Include a concise explanation of each direction and limitation in `docs/scoring_methodology.md` and in the UI. A high score does not imply that a region should receive more funding without further local context.

Store component percentile scores, five weighted component contributions, unrounded final score, `score_version = 'v1.0'`, `score_status`, and missingness flags in the ranking mart. Round **for display only** (e.g. 1 decimal). Create a deterministic global rank among scored records only, sorting final score descending, then `AREA`, then `OCC_CODE` ascending for tie resolution. Unscored records have null rank. Include metadata with exact weight settings and reference-population definition.

Create at least two documented sensitivity scenarios without changing the official v1.0 output, e.g. `AI emphasis`: exposure .40, usage .25, employment .20, wage .05, outlook .10; `workforce emphasis`: exposure .20, usage .10, employment .40, wage .15, outlook .15. Reuse the same component percentile reference values, compare score/rank changes among the same eligible records, report rank correlation and significant movers; define the threshold for 'significant' before reporting. State that these are sensitivity scenarios, not alternative official scores.

## 5. Area summaries and geography

Generate `mart_area_summary.parquet` from scored occupation–area rows, grouped by `AREA`, `AREA_TITLE`, `area_class` and release. Primary regional statistic: **employment-weighted mean priority score**, using `TOT_EMP` for scored records: `sum(priority_score * TOT_EMP) / sum(TOT_EMP)`. Include scored-record count, total-record count, scored employment, total *known* published employment, and clear coverage ratios (record coverage, and employment coverage where denominator known). The regional rank is descending on the regional statistic and is global across all available scored areas; no table filter may change it.

Employment-weighted regional scores are derived indicators, not directly comparable to individual occupation-row scores without explaining the aggregation. Coverage differences can bias regional rankings; display coverage prominently. Do not sum occupational employment across major and detailed SOC levels without validating occupation granularity / avoiding double-counting. If detailed and aggregate SOC levels are mixed, restrict the area employment-weighted summary to an explicitly documented non-overlapping comparable occupation subset. Do not treat overlapping aggregates as independent jobs. Add unit tests on aggregation rules.

Use **verified and appropriately licensed** California OEWS metropolitan/nonmetropolitan area boundary geometries with a defensible join to `AREA`. Never fabricate polygons or use unrelated county boundaries as OEWS regions. If trustworthy compatible geometries are unavailable, implement the interactive regional ranking view with real data and clearly explain that the accurate regional choropleth is unavailable. A point map, if used, must be explicitly labeled as illustrative location markers, never as area boundaries. Preserve consistent metric choices and regional ranking across visualizations.

## 6. UI and interactions

Build a clean, professional, responsive Streamlit + Plotly dashboard with human-readable labels, helpful legends, hover details, and accurate units. Display **real, computed** v1.0 priority scores; never use dummy records or demo ranks. UI sections:

### A. Title
`AI Workforce Investment Planner`, with concise subtitle explaining occupation × California OEWS area scope.

### B. Scope, Releases and Limitations
Document sources (Claude Global Job Exposure, Claude CA PCT, BLS), record counts, date/release, area classes, occupation coverage, model version and precise indicator meanings. Show coverage/missing-data warning and the difference between AI indicators and BLS labor-market indicators. Explain that the score ranks **available complete records** and is not causally validated or a policy prescription. Do not assert an unverified provenance/date for Claude indicators.

### C. What Does the Priority Score Mean?
Show the finalized formula, five weights, component definitions, percentile reference population, higher-vs-lower interpretation, score eligibility policy, and concise model caveats. Provide an optional weight breakdown visualization within this explanation section if helpful, but do not add extra top-level sections.

### D. Priority Score Distribution
Real histogram of scored `priority_score` across **all eligible records**. Clearly label N, coverage, x-axis (index points), and y-axis (occupation × area records). Never include unscored rows as zeros. Distribution should not change in response to records-table filters.

### E. California Area Map (Map & Regional Ranking View)
Real regional summary metric, score coverage and rank. If verified boundaries exist, create a color-scaled choropleth, hovering area, regional score, coverage, and number of scored occupations. Always provide a synchronized regional ranking table/bar chart (all available areas), including missing/low-coverage messaging. Do not update the map or regional ranks when table filters change.

### F. Ranked Occupation × Area Records
Display all source fields plus `priority_score`, `global_rank`, `score_status` (and optionally expandable component scores). Default sort: scored rows by global rank ascending; unscored records separately at the end. This is the **only** section containing user filters:
- Occupation: searchable multi-select using `OCC_TITLE` with code disambiguation.
- Area: searchable multi-select using `AREA_TITLE` / `AREA`.
- Published Employment: numeric inclusive min/max using `TOT_EMP`; choose clear treatment for null employment (default excluded when an explicit employment range is selected, included otherwise).
- A `Reset Table Filters` action.

All three filters apply **only** to this table. They must never affect Scope, Score Explanation, Score Distribution, area map, or regional ranking. A filtered record retains its original official `priority_score` and `global_rank`; never re-rank or recompute scores within the filtered subset. Show filtered-row count, status, paginated/scrollable table, and CSV export of exactly the visible filtered rows; leave the 11 original columns intact and add derived fields alongside them.

## 7. Engineering outputs

Use a reproducible modular project structure, with paths configurable and documented. Produce at minimum:
- `data/processed/cleaned_core.parquet` (faithful standardized copy of the supplied workbook, original rows preserved)
- `data/processed/score_config.parquet` (version / weight / reference metadata; if configuration is better stored as YAML/JSON, also preserve a reproducible Parquet representation)
- `data/processed/mart_priority_ranking.parquet`
- `data/processed/mart_area_summary.parquet`
- `src/` data validation, scoring, and aggregation functions with explicit inputs/outputs
- `dashboard/app.py` (modular components as useful)
- `docs/scoring_methodology.md` including formula, units, assumptions, missingness policy and sensitivity tests
- `tests/test_scoring.py`, `tests/test_data_quality.py`, `tests/test_aggregation.py`, `tests/test_dashboard_filters.py`
- `requirements.txt` or existing dependency configuration, and `README.md` with local run and reproduction steps.

Use processed Parquet tables at dashboard runtime, never repeatedly parse the Excel input on every page refresh. Separate data preparation, scoring, regional summary, and UI from each other. Cache reads safely; ensure clean rebuild reproducibility.

## 8. Acceptance tests and verification

1. Validate expected 11 headers, types, key uniqueness, and row counts; verify original numeric values and retained leading zeroes.
2. Report per-column missingness and compare complete-case count with the audit. Verify missing `claude_usage_pct` is never silently set to zero or given a derived final score.
3. Test percentile scoring, tie treatment, boundary cases, weighted contribution sums, score range, version metadata, and independently hand-computed sample rows. Confirm no component/score is calculated for incomplete records.
4. Test deterministic ranks, sensitivity scenarios, area summary denominators and employment double-count safeguards.
5. Verify the records-table Occupation, Area, Published Employment filters AND reset action; verify every other chart/area rank remains unchanged as filters change.
6. Confirm that map shapes (if provided) correctly correspond to OEWS `AREA` codes; explain unmatched areas and coverage.
7. Run the entire real-data pipeline and Streamlit dashboard locally; test empty-filter results and missing numeric values. Capture representative screenshots; report real top-ranked records and regional results with clear coverage caveats.
8. Do not deploy externally. Do not claim actual policy effectiveness, AI-driven job loss, or funding ROI.

**Execution order:** inspect and validate workbook → reproduce audit → implement score v1.0 and test it → create Parquet marts → implement regional aggregates/geography → build and test dashboard → document sources, assumptions and scoring limitations → launch locally and provide run instructions and screenshots.

If a noncritical design choice is unspecified, make a reasonable choice and document it. Do not substitute fabricated records or provisional simulated scores for official results. Flag any material data/provenance discrepancy transparently, and continue with supported functionality wherever possible.
