# AI Workforce Investment Planner — Final Production Dashboard Specification

## 1. Goal and required output

Build a complete, professional, responsive **AI Workforce Investment Planner** dashboard using the real cleaned dataset `final_cleaned_core.xlsx`. Implement its full reproducible processing and scoring backend, verified California geography, interactive map, regional ranking, and occupation–area table. Deliver a locally runnable application plus a standalone HTML export if feasible without changing data or calculations. Do **not** use synthetic records, synthetic scores, or fabricated geographic shapes.

Keep the dashboard focused on exactly these top-level sections, in this order:
1. **AI Workforce Investment Planner** (title and concise subtitle)
2. **Scope, Releases and Limitations**
3. **What Does the Priority Score Mean?**
4. **Priority Score Distribution**
5. **California Area Map (Map & Regional Ranking View)**
6. **Ranked Occupation × Area Records**

No global filter bar or unrelated analytics modules. Present this as a decision-support screening tool, **not** a causal estimate of AI job loss, an automatic funding recommendation, or a validated measure of return on investment.

## 2. Source data and canonical schema

Authoritative numerical input: `final_cleaned_core.xlsx`, worksheet `cleaned_data`. Preserve all 11 source columns:

| Field | Definition |
|---|---|
| `release` | BLS release label |
| `area_class` | Metropolitan / nonmetropolitan |
| `AREA` | OEWS area code; read as a string and retain leading zeros |
| `AREA_TITLE` | Area name |
| `OCC_CODE` | SOC occupation code; string |
| `OCC_TITLE` | Occupation name |
| `job_exposure` | Claude Global Job Exposure |
| `claude_usage_pct` | Claude CA PCT, original percentage-point values |
| `TOT_EMP` | BLS published employment |
| `A_MEAN` | BLS mean annual wage in USD |
| `employment_change_pct` | BLS projected employment change in percentage points |

Previously observed audit results (independently recheck): 11,847 records, 28 OEWS areas, 783 occupations, May 2025 release, no duplicate `(release, AREA, OCC_CODE)` keys. Missing counts: `job_exposure` 1,037; `claude_usage_pct` 5,387; `TOT_EMP` 215; `A_MEAN` 169; `employment_change_pct` 0. Approximately 6,123 records have complete five-indicator data. These are validation expectations, not values to hard-code into the UI.

Respect source units: Claude `claude_usage_pct` is already in percentage points (a value `0.16` is `0.16%`, **not** `16%`); `employment_change_pct = -6` represents `-6%`. Do not multiply or rescale either without explicit verification. Do not claim a data vintage for Claude metrics or an employment-projection horizon unless verified from metadata. Preserve raw inputs and show human-readable labels and units.

## 3. Transparent missing-data policy

- Do not replace missing/suppressed indicators with zero, a mean, or a guessed number. Actual numeric zero is valid where appropriate.
- Official scoring eligibility requires all five numeric metrics to be finite, `TOT_EMP > 0`, `A_MEAN > 0`, and nonnegative exposure and usage. Invalid/missing required fields yield no score or global rank, with `score_status = 'Insufficient Data'` or a more precise validation status.
- Retain **all source rows** in the final records table. Show `Not scored` or a dash rather than fake zeros for unscored records. Report completeness overall and by area; explain how incomplete coverage may bias comparisons.
- Keep the percentile reference population fixed, using all complete eligible California occupation–area rows of the release, not the filtered records table.

## 4. Priority Score algorithm — v1.0

Compute an interpretable 0–100 **relative Workforce Transition Priority Score**. Higher values mean higher screening priority for further workforce transition investigation under the stated assumptions, **not** proven AI-caused displacement. The component directions and weights below are policy/modeling assumptions, not empirically optimized causal coefficients.

For the eligible reference population, calculate each component on a 0–100 percentile scale using one documented tie rule, such as `pandas.Series.rank(method='average', pct=True) * 100`:

| Component | Calculation | Weight |
|---|---|---:|
| Exposure | Percentile of `job_exposure` | 30% |
| Claude usage | Percentile of `claude_usage_pct` | 15% |
| Workforce scale | Percentile of `log1p(TOT_EMP)` | 30% |
| Wage | Percentile of `A_MEAN` | 10% |
| Weaker employment outlook | Percentile of `-employment_change_pct` | 15% |

`priority_score = 0.30*exposure_component + 0.15*usage_component + 0.30*employment_component + 0.10*wage_component + 0.15*outlook_component`

Do not round intermediate computations. Retain raw components, weighted contributions, unrounded score, `score_version = 'v1.0'`, and status. Assign global ranks to scored occupation–area rows by descending score, with deterministic tie resolution (`AREA`, then `OCC_CODE`); unscored rows have null ranks. Display rounding only.

Perform sensitivity analysis using at least two alternative configurations while retaining the official v1.0 score:
- AI emphasis: 40% exposure, 25% usage, 20% employment, 5% wage, 10% outlook.
- Workforce emphasis: 20% exposure, 10% usage, 40% employment, 15% wage, 15% outlook.

Document rank correlation and materially changing rankings. Do not present a model assumption as an empirical causal finding.

## 5. Regional statistics and ranking

Work at the official OEWS `AREA` level, retaining metropolitan and nonmetropolitan areas as separate units. Validate SOC occupation granularity before totaling employment: major/group and detailed SOC rows must not be simultaneously added as if they were distinct jobs. Use a clearly documented, non-overlapping occupation subset when computing employment-weighted regional statistics.

Compute the following real-data metrics for **every area** (and clearly label the eligible/scored subset used):

1. **Median Priority Score** — median valid occupation–area `priority_score` in that area; this is the **default map coloring metric**.
2. **Top Priority Score** — maximum valid occupation–area `priority_score` in that area.
3. **Score Coverage (%)** — number of records with a valid priority score / total eligible-scope occupation–area records in that area × 100. State the denominator clearly; missing scores count in the denominator.
4. **Visible Occupation-Area Records** — total number of distinct occupation–area records represented for that area in the map's underlying regional dataset (including unscored rows). This number refers to the map's complete input scope, **not** the separately filtered records table.

Also produce **Employment-Weighted Regional Priority Score** = `Σ(priority_score × TOT_EMP) / Σ(TOT_EMP)` for scored rows in the documented non-overlapping occupation subset. Regional ranking uses this **separate, fixed metric**, descending, with deterministic ties. Report scored/total records, scored employment, known employment, and coverage. **Do not equate the median map metric with the employment-weighted regional ranking metric.** Explain both methods in the UI/tooltips.

All regional statistics and ranks use the complete canonical data and **never** change when users filter the records table.

## 6. California Area Map — REQUIRED, with selectable color metrics

Implement an actual interactive **California OEWS area geographic map**, not merely a bar chart labeled as a map. Retain a separate Regional Ranking View beside/below it. Geography is a core deliverable: actively locate and verify authoritative US Census and/or BLS-compatible boundaries, document source URLs, vintage and crosswalk decisions, and ship the geometry or reproducible retrieval process with the application.

- Match `AREA` codes using verified official geography identifiers/crosswalks, rather than loose string matching. Include metropolitan and nonmetropolitan areas wherever valid polygon boundaries can be established; never replace OEWS areas with county boundaries merely because they are available.
- If a subset cannot be mapped reliably, show its region in the ranking and an explicit **Unmapped OEWS areas** notice. Never invent polygons, hide missing coverage, or pass off location dots as area boundaries. Do not silently remove the map or replace it with ranking alone; implement all verifiable areas, and report any outstanding mapping gap.
- Include a metric dropdown **within the map section**, with exactly four options in this order:
  1. `Median priority score` **(default on load)**
  2. `Top priority score`
  3. `Score coverage (%)`
  4. `Visible occupation-area records`
- The map is a choropleth: **darker color = higher value of the selected metric**. Recompute the color scale/legend from the selected metric, with correct score points, percentages, or record counts; maintain a meaningful, readable legend and use a neutral color for unavailable regions.
- On each map-metric selection, update **only the map colors, map legend and map tooltip emphasis**. Do not update the fixed regional ranking metric/order, score histogram, or occupation–area table. All values derive from actual data.
- Tooltip shows `AREA_TITLE`, `AREA`, selected metric with units, median score, top score, coverage %, number of records, employment-weighted regional score, and regional rank when available; distinguish unavailable fields.
- Provide zoom/pan and useful hover interaction; ensure map is legible at desktop sizes and usable on smaller screens.
- Include a **Regional Ranking View** adjacent to or below the map, ranking regions by the fixed employment-weighted regional score and showing coverage. It must remain visible and stable when switching the map dropdown.
- Verify that every rendered polygon corresponds to the intended OEWS area and report the mapped/unmapped count. If the mapping cannot be completed for all areas after a good-faith search, keep accurate mapped areas plus ranking for all; document limitations rather than drawing incorrect geography.

## 7. Other dashboard sections

### A. Header
Use exactly **AI Workforce Investment Planner** and a concise California occupation × OEWS area subtitle.

### B. Scope, Releases and Limitations
Clearly explain the real data sources (Claude Global Job Exposure and CA PCT; BLS), release scope, data size, number of areas and occupations, validity/coverage and missing-data policy, score version, limitations of AI inference, and geography limitations where relevant. No artificial KPIs.

### C. What Does the Priority Score Mean?
Explain the formula and all five component weights/directions, the fixed percentile reference set, why higher means greater *screening* priority, treatment of missing scores, and key interpretive limitations. An inline weight display is acceptable, but do not add extra top-level sections.

### D. Priority Score Distribution
Histogram of the **actual** scored occupation–area records, with appropriate bins, axis labels, count of scored observations, and missing-data notice. No unscored rows plotted as zero. Chart is independent of all records-table filters and map metric selection.

### E. California Area Map (Map & Regional Ranking View)
Implement section 6 exactly, including a real map, all four selector options, the default median, and the separate fixed ranking.

### F. Ranked Occupation × Area Records
Show every source column plus `priority_score`, `global_rank`, `score_status` and optionally component scores. Display valid scored rows sorted by their fixed global rank; put unscored rows afterward. This is the **only section** with occupation, area and employment filters:
- Searchable multi-select **Occupation** (`OCC_TITLE`, with code to disambiguate).
- Searchable multi-select **Area** (`AREA_TITLE`, with `AREA` code).
- Inclusive numeric-range **Published Employment** (`TOT_EMP`) with clear handling of missing values (include missing when no range is selected; exclude them for an explicit numeric bound).
- **Reset Table Filters** button.

Filters combine conjunctively and affect **only the records table, its visible record count and its CSV export**. They must not affect the priority score formula or any scores/ranks, Scope, explanation, distribution, map (including its dropdown), or regional ranking. Preserve each displayed record's **original global rank**, even after filtering. Support sensible sorting, scrolling/pagination, precise numeric/percentage formatting and export of the visible filtered records. Display an informative empty-state message.

## 8. Technical architecture and deliverables

Implement a clean modular pipeline and browser-viewable dashboard. Prefer the existing project tooling where appropriate (Python + pandas for preprocessing, Parquet outputs, Plotly for interactive charts; Streamlit is acceptable for the live application). If also delivering an offline self-contained HTML, verify that the map and every other interaction function from the exported file; **an HTML export must not be missing the geographic map**.

Provide, at minimum:
- Processed canonical data Parquet and metadata/configuration.
- Occupation–area score/ranking mart (all rows preserved).
- Regional summary mart including all four map metrics, fixed regional ranking score/rank, and coverage information.
- Verified geography/crosswalk assets and a mapping source note.
- Modular data-loading, eligibility, scoring, ranking, aggregation and filtering code.
- Dashboard source and final runnable build (plus offline HTML if applicable).
- `docs/scoring_methodology.md` documenting weights, percentile reference, missingness, scale, and sensitivity checks.
- Tests for scores, missingness, area geometry joins, map metric switching, ranking stability, and local table-filter independence.
- `README.md` with build/rebuild, local preview, asset and dependency instructions.

At dashboard runtime use processed data, not repeated Excel parsing. Preserve provenance/version details, deterministic results, and separation between scoring logic, map state and table-filter state.

## 9. Acceptance tests — REQUIRED

1. Load and validate all 11 columns, types, leading-zero code preservation, unique occupation–area/release keys, raw values, record totals, and field-specific missingness.
2. Verify eligibility policy, score calculation against independently computed sample cases, tie behavior, fixed rank stability, component contributions summing to the displayed score, and no fabricated/imputed values.
3. Verify detailed/non-overlapping occupation handling for weighted regional scores, and independently recalculate sample regional medians, maxima, coverage percentages and visible-record counts.
4. Confirm the map is a **real geographic visualization**, that `AREA` polygons correctly match official OEWS areas, that verified metropolitan and nonmetropolitan areas are included where possible, and that unmapped regions are disclosed.
5. Confirm the map dropdown has **exactly four options**, defaults to **Median priority score**, and changes regional color shading, legend and tooltips correctly for all four options. Higher values must always appear darker. Score coverage must be shown in percent; record count as an integer.
6. Confirm changing the map dropdown does **not** change regional ranking or any other dashboard section.
7. Confirm Occupation, Area and Published Employment filters affect **only** the Ranked Occupation × Area Records table, its count and CSV; map, map metric selector, ranking and histogram remain unchanged. Confirm reset, multi-filter intersections and no-result states.
8. Run the actual end-to-end pipeline and dashboard with real data, test both the local app and any supplied offline HTML, provide representative screenshots including the geographic map and all dropdown modes, and report any unavailable geography, missingness or source metadata honestly.

## 10. Execution guidance

Inspect/validate the workbook → produce and verify official v1.0 scores → compute all four map metrics and fixed regional rankings → obtain and verify authoritative OEWS geometry → implement and test map and dropdown → implement remaining sections and table-only filters → run full test suite and preview → deliver complete runnable artifacts, concise documentation and screenshots. Do not stop after generating a specification; complete the functioning product. Do not deploy publicly without explicit authorization.
