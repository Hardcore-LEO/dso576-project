# Cleaned source data dictionary

Read [cleaning_answers.md](cleaning_answers.md) for the assignment answers, methodological decisions, and measured coverage. All outputs are in `data/cleaned/`. Full sources use Parquet to retain types and avoid excessively large CSVs; smaller analytical tables have both Parquet and CSV copies.

## Common conventions

- Identifier columns are strings, including area codes with leading zeros and full O*NET extensions. Import CSV identifier fields as text.
- Missing values are Parquet nulls / empty CSV cells. Real zero stays zero. No imputation is applied.
- Percent metrics use 0–100 units. Changes in percentage metrics use percentage points.
- Date columns identify the original observation interval. Release dates are not observation dates.
- Matching the first seven characters of an O*NET code is a documented prefix linkage, not an independently verified official crosswalk.
- Source field descriptions are preserved as `BOS_M2025_dl_field_descriptions.json` and `MSA_M2025_dl_field_descriptions.json`.

## Full cleaned source tables

| File | Grain / key | Scope |
| --- | --- | --- |
| aei_claude_ai_clean.parquet | `date_start, date_end, geo_id, geo_level, category_name, hierarchy_level, metric_id, node_external_id` | All 1,636,573 source metric rows, all countries, categories, and both months |
| bos_m2025_dl_clean.parquet | `area, area_type, naics, i_group, own_code, occ_code, o_group` | All 48,689 nonmetropolitan records, including occupation totals |
| msa_m2025_dl_clean.parquet | Same BLS key | All 150,023 metropolitan records, including occupation totals |
| occupations.csv / .parquet | `onet_soc_code` | All 1,016 occupation dictionary entries, plus derived `soc_code` |

AEI original columns are retained: dates, geography, category, hierarchy level, metric ID, numeric value, node title, and node ID. `source_file` and `source_release` are added. `hierarchy_level = 0` is the leaf level; its meaning depends on category, so an occupation leaf and a task leaf are different objects.

For AEI metric definitions and denominators, consult [the release documentation](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data_documentation.md). `pct` is a usage-composition measure, not occupation exposure. `use_case_work_pct` is work-use classification, not task change. Autonomy uses a 1–5 scale. Time fields differ in units: `human_only_time_mean` is hours; `human_with_ai_time_mean` is minutes. Unpublished cells are not zeros. Other metrics remain at their original units, names, and grain; they have not been merged across categories.

### BLS field groups

| Fields | Meaning / units |
| --- | --- |
| area, area_title, area_type, prim_state | Geographic identifiers, title, type, and primary state; type 4 = metro and 6 = nonmetro |
| naics, naics_title, i_group | Industry scope; these sources are cross-industry |
| own_code | Ownership scope; 1235 covers the combined government/private scope in these sources |
| occ_code, occ_title, o_group | Published occupation code, title, and level; “detailed” can include combined categories |
| tot_emp | Published employment, rounded to nearest 10 in the source; not a worker-level observation |
| emp_prse | Employment percent relative standard error |
| jobs_1000 | Occupation jobs per 1,000 area jobs |
| loc_quotient | Location quotient, a relative concentration index |
| pct_total, pct_rpt | Source industry/reporting shares; blank in these files |
| h_mean, a_mean | Mean hourly / annual wage in dollars |
| mean_prse | Mean-wage percent relative standard error |
| h_pct10, h_pct25, h_median, h_pct75, h_pct90 | Hourly wage distribution, dollars/hour |
| a_pct10, a_pct25, a_median, a_pct75, a_pct90 | Annual wage distribution, dollars/year |
| annual, hourly | Nullable original annual-only / hourly-only flags; blank is not asserted False |
| source_file, oews_release | Added source filename and May 2025 release label |

Each numeric BLS column has a corresponding `_status`: `reported`, `blank_not_available`, `wage_not_available` (`*`), `employment_not_available` (`**`), `top_coded_lower_bound` (`#`), or supported but unused `below_reporting_threshold` (`~`). Numeric nonreported values remain null. The status names on error/concentration fields retain the source marker's meaning; they do not imply that the field itself counts employees.

Wage columns also have `_lower_bound`, populated only for `#`: 115 for hourly wages and 239200 for annual wages, per the workbook notes. A lower bound is not an exact estimate. It is not included as an exact number in averages or rankings.

## Analytical tables

### occupation_ai_by_scope.csv / .parquet

Key: `(date_start, date_end, geo_id, geo_level, onet_soc_code)`. This wide occupation table contains GLOBAL, USA, and US-CA separately, for both months. Every published metric becomes a column. Blank columns for a geographic scope remain blank even if a global value exists. `aei_occupation_title` is the source AI title; `onet_title` is the dictionary title; `onet_title_match` records `both` or `left_only`. `soc_code` is the derived seven-character prefix. Titles are preserved independently rather than overwritten.

### global_occupation_context.csv / .parquet

Key: `soc_code`. Latest-month global context only, with explicit `ai_context_geo`, `ai_period_start`, and `ai_period_end`. Four metric families are summarized: work-use, augmentation, automation, and autonomy. Each has `_min`, `_max`, and `_n_extensions`. Min/max summarize observed full-code extensions and are not uncertainty intervals or parent-code population estimates. `published_ai_extensions` counts published nodes; `published_onet_codes` lists their full codes; `dictionary_extensions` counts corresponding dictionary entries, which can include unobserved extensions.

### occupation_area.csv / .parquet

Key: `(area_code, soc_code)`. Contains 11,847 California detailed occupation–area cells. It preserves all BLS fields and status/lower-bound columns, with these renames: `area` → `area_code`, `area_title` → `area_name`, `occ_code` → `soc_code`, and `occ_title` → `occupation_title`. It adds the global context fields above through a many-to-one merge.

`ai_parent_match` identifies a matching global parent-context row; `has_global_work_use_context` indicates at least one observed work-use extension. A match is not proof of taxonomy equivalence or local AI behavior. Missing context is retained. There is no fabricated priority score, exposure, national outlook, task penetration, or importance value.

### Other analytical and audit outputs

| File | Meaning |
| --- | --- |
| occupation_code_bridge.csv / .parquet | Outer lookup of unique California SOCs and dictionary extensions; `both`, `left_only`, `right_only` identify prefix matches and each unmatched side. Never sum employment after expanding this bridge. |
| soc_match_audit.csv | Union of parent codes with boolean membership in California OEWS, O*NET dictionary, and latest global AI tables |
| aei_codes_not_in_dictionary.csv | Full AI codes/titles with no dictionary match; header-only when there are no unmatched codes |
| occupation_usage_month_comparison.csv / .parquet | Original geography and full O*NET code; April/May `pct` values and their difference in percentage points. Missing months stay missing. |
| area_summary.csv / .parquet | Counts of occupation cells, published employment cells, exact median-wage cells, and global context cells; context coverage uses all supplied detailed cells as denominator. Published-employment sum is a cell checksum, not an official statewide total. |
| largest_workforces_with_ai_context.csv / .parquet | Largest 20 published employment cells with some global work-use context. Ordered by employment only; `ordering_basis` states that this is not an AI priority ranking. |
| aei_metric_coverage.csv | Published-row counts by period, geographic level, category, hierarchy, and metric; not expected publication denominators |
| missingness.csv | Null counts and percentages by analytical table and field; derived lower-bound columns are intentionally blank except where censored |
| source_manifest.json | Original filenames, byte sizes, and SHA-256 fingerprints |
| cleaning_audit.json | Full source counts, duplicate removals, BLS status frequencies, and analytical reconciliation results |
| validation_results.json | Independent validation checks and raw-file hash verification from the completed validation run |

No raw source was changed, no synthetic record was created, and no dashboard data were imported. The full Anthropic file retains task-level metrics, but the supplied occupation dictionary does not supply the task-to-occupation bridge or O*NET task importance ratings.
