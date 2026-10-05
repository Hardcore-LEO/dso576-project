# Source-data cleaning and assignment answers

## 1. Scope, inputs, and reproducibility

This work cleans the **four source files supplied by the user**, not values extracted from the dashboard. The questions come from [project-start.md](project-start.md), [data-fit.md](data-fit.md), [technical.md](technical.md), [auxiliary.md](auxiliary.md), and [alternatives.md](alternatives.md). Their suggested searches, synthetic fallbacks, and earlier access claims are project context, not additional user instructions or verified measurements. The original files and dashboard are unchanged.

| Supplied file | Source rows | Cleaned rows | Exact duplicates removed |
| --- | --- | --- | --- |
| BOS_M2025_dl.xlsx | 48,689 | 48,689 | 0 |
| MSA_M2025_dl.xlsx | 150,023 | 150,023 | 0 |
| Occupation Data.xlsx | 1,016 | 1,016 | 0 |
| aei_claude_ai_2026-06-26.csv | 1,636,573 | 1,636,573 | 0 |

Every source row is retained except any identical duplicates explicitly counted above. All geographies, months, and categories in the Anthropic file are preserved in the full cleaned Parquet output. Both BLS workbooks retain their non-California records and aggregate occupation rows in full cleaned outputs. Only the analytical California table filters to detailed occupation rows. Worksheet headers, descriptions, and internal metadata are not observations.

Run from the `project` directory in PowerShell:

```powershell
uv venv .venv --python 3.14
uv pip install --python .venv/Scripts/python.exe -r requirements-cleaning.txt
.\.venv\Scripts\python.exe clean_source_data.py --input-dir 'C:\Users\Cortl\Downloads\drive-download-20261004T203842Z-1-001'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe validate_cleaned_data.py --input-dir 'C:\Users\Cortl\Downloads\drive-download-20261004T203842Z-1-001'
```

The input directory is configurable. The default output directory is `data/cleaned/`. File hashes, source row counts, token counts, and reconciliation results are recorded in [source_manifest.json](data/cleaned/source_manifest.json) and [cleaning_audit.json](data/cleaned/cleaning_audit.json). Dependencies are pinned in [requirements-cleaning.txt](requirements-cleaning.txt).

## 2. What one row represents and what was cleaned

**Anthropic:** one published metric for a period × geography × category × hierarchy level × node. The unique key also includes `metric_id`. April and May 2026 are separate observations; no cross-month backfill or averaging was used. Dates are parsed, numeric values checked, hierarchy levels retained, and node IDs kept as strings. The full file contains 1,636,573 published rows with no blank metric values; absence in a derived wide table usually means a particular cell was never published. All percentages are validated in 0–100, and autonomy in 1–5. Distinct categories are never merged by coincidentally matching node IDs.

**BLS:** one area × industry × ownership × occupation × occupation-level estimate. Identifier formatting and all original numeric precision are retained. Exact duplicates are removable; conflicting keys cause an error. `O_GROUP = detailed` selects the most detailed published rows for analysis, but the workbook explicitly says some such rows are combined occupational categories. They must not be assumed to be identical to every O*NET parent code. Major-group and all-occupation totals stay out of the analytical table to prevent double counting.

**Occupation Data:** one full O*NET occupation code with its title and description. There are 1,016 full codes and 867 seven-character parent codes. Full extensions remain intact. A separate parent-code lookup connects descriptions to BLS codes without copying employment for every extension. This workbook does not contain task statements, task-occupation mappings, importance ratings, skills, or task penetration.

### Missing, censored, and valid zero values

From the BLS workbooks' own Field Descriptions sheets: `*` means a wage estimate is unavailable; `**` means an employment estimate is unavailable; `#` means at least $115/hour or $239,200/year. `~` indicates a reporting share below 0.5%; the parser supports it even though it does not occur in these numeric columns. The pipeline preserves separate status fields. Top-coded wages have a null exact value and a separate lower bound. Blanks are not automatically labeled confidential suppression. Real zeros remain zero. Annual-only/hourly-only source flags are retained; no annual wage is fabricated by multiplying an hourly rate by 2,080.

| Field / status | California occupation–area cells |
| --- | --- |
| tot_emp: reported | 11632 |
| tot_emp: employment_not_available | 215 |
| a_median: reported | 11678 |
| a_median: wage_not_available | 154 |
| a_median: top_coded_lower_bound | 15 |

No values were filled with means, zeros, another month, or another geography. High but valid estimates were retained. Employment standard errors and wage distributions remain available for assessing reliability; no arbitrary outlier cutoff was imposed.

## 3. Can more importance or task-change values be retained?

**Importance cannot be recovered from these four files:** the O*NET workbook is an occupation dictionary, not the Task Ratings table. The Anthropic `onet` category supplies task/activity usage statistics, not O*NET importance ratings. Its task rows are preserved in the full clean file, but joining tasks to occupations needs a separate occupation–task mapping. Therefore no importance column was invented or imported from the old dashboard.

**Work-use values are retained wherever published.** In May, the supplied occupation-level data contain:

| Geography | Published occupation nodes | Work-use values | Augmentation values |
| --- | --- | --- | --- |
| GLOBAL | 718 | 718 | 716 |
| US-CA | 460 | 0 | 0 |
| USA | 627 | 0 | 0 |

Across the California BLS table, **9,296 of 11,847 cells** have at least one matching global work-use value; **2,551 cells**, spanning **215 SOC codes**, do not. These are context matches across seven-character codes, not direct California measurements or validated taxonomy crosswalks.

The old dashboard's label “task change” should not be reused for `use_case_work_pct`: it measures work-related use, not change in tasks. The metric remains named `use_case_work_pct` here. Country and state occupational usage shares are kept separately. Global behavior is not silently used to fill U.S. or California cells.

The release documentation defines publication limits by geography and hierarchy; an unpublished cell is not a measured zero. It defines `pct` as the category-node share of a geography's usage, work-use as the percentage classified as work, and autonomy on a 1–5 scale. Estimated human-only time is in **hours**, while AI-assisted time is in **minutes**, so raw subtraction would be invalid. Period starts are inclusive and ends exclusive. These definitions were checked against [Anthropic's June release documentation](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data_documentation.md).

## 4. Which geography should Vision A use?

Use the **28 California OEWS areas in these workbooks: 25 metropolitan and 3 nonmetropolitan areas**. Selection uses `PRIM_STATE = CA`, and all selected metro labels end in `, CA`; no selected metro is labeled multi-state. This is not a county-level validation of coverage. Preserve `area_code` and `area_type`; do not call these Regional Planning Units.

CWDB Regional Planning Units require a validated county-to-RPU definition and compatible occupational employment detail. A county boundary lookup alone cannot divide a metro's occupational employment between RPUs. No such source is among the four supplied files. Do not aggregate overlapping geographic levels or present a sum of available area cells as the official statewide total.

## 5. Which code level, vintage, official crosswalk, and aggregation rule?

Use BLS published occupation codes as strings for the occupation–area analytical grain. Keep O*NET's full `XX-XXXX.XX` identifiers in the separate dictionary and AI table. Deriving `XX-XXXX` creates an auditable **prefix linkage**, not an official crosswalk. There are **783 California BLS codes**, of which **12 lack a dictionary parent match**. Across the selected AI scopes and months, **0 distinct full AI codes** have no exact dictionary match. Inspect [soc_match_audit.csv](data/cleaned/soc_match_audit.csv), [occupation_code_bridge.csv](data/cleaned/occupation_code_bridge.csv), and [aei_codes_not_in_dictionary.csv](data/cleaned/aei_codes_not_in_dictionary.csv).

The earlier project documents mention O*NET 31.0 / O*NET-SOC 2019 and BLS SOC 2018. The supplied occupation workbook has no explicit database-version column, so its exact release is **unverified**. We do not certify that all mappings are equivalent. In particular, combined BLS occupations may differ from full O*NET categories. No fuzzy title matches, guessed remapping, or unweighted means of occupation percentages were used.

When a BLS parent has several published AI extensions, the analytical table stores their minimum, maximum, count, and full-code list. These are **ranges across published extensions**, not parent-occupation estimates, confidence intervals, or coverage of all workers. For a single observed extension the endpoints coincide, but omitted extensions may still exist. Behavior and employment are joined many-to-one from this summary, preserving exactly 11,847 occupation–area rows. Raw extension values remain available for more detailed review.

## 6. Which releases are frozen, and is the timing compatible?

The BLS filenames and Field Descriptions identify **May 2025**. Their internal UpdateTime sheets contain an older timestamp and are not treated as the estimate vintage. The Anthropic filename identifies the **2026-06-26 release**, containing April `[2026-04-01, 2026-05-01)` and May `[2026-05-01, 2026-06-01)` observations. The May context table uses May only; the April data are preserved separately. Joining 2026 AI behavior to 2025 employment is an explicitly lagged descriptive comparison.

The observation windows, geography, and category remain in the clean data. A two-month comparison is supplied, with changes computed only when both cells were published. Differences are percentage points, not percent growth. Two periods cannot establish a long-run trend, and changes in observed usage are not employment effects.

## 7. Which occupations and regions should be prioritized?

These files support **descriptive review candidates**, not a defensible final funding ranking. They do not include `job_exposure.csv`, the separate task-penetration data, BLS employment projections, training costs, or worker skill gaps. Therefore the old dashboard's five-component priority score cannot be reproduced from these four files alone. No synthetic score or “missing equals zero” ranking was produced.

The following are the largest published occupation–area employment cells with some global work-use context, ordered **only by employment**. This answers where potentially relevant workforces are large; it does not establish high exposure, training need, or suitability for automation.

| Area | SOC | Occupation | Employment | Global work-use range (%) |
| --- | --- | --- | --- | --- |
| Los Angeles-Long Beach-Anaheim, CA | 35-3023 | Fast Food and Counter Workers | 160,270 | 58.44–88.30 |
| Los Angeles-Long Beach-Anaheim, CA | 41-2031 | Retail Salespersons | 130,650 | 8.26–8.26 |
| Los Angeles-Long Beach-Anaheim, CA | 53-7062 | Laborers and Freight, Stock, and Material Movers, Hand | 120,720 | 64.71–64.71 |
| Los Angeles-Long Beach-Anaheim, CA | 43-9061 | Office Clerks, General | 112,270 | 60.29–60.29 |
| Los Angeles-Long Beach-Anaheim, CA | 41-2011 | Cashiers | 109,940 | 20.70–20.70 |
| Los Angeles-Long Beach-Anaheim, CA | 29-1141 | Registered Nurses | 109,360 | 8.49–56.13 |
| Los Angeles-Long Beach-Anaheim, CA | 11-1021 | General and Operations Managers | 104,610 | 80.91–80.91 |
| San Jose-Sunnyvale-Santa Clara, CA | 15-1252 | Software Developers | 87,350 | 77.24–77.24 |
| Los Angeles-Long Beach-Anaheim, CA | 53-7065 | Stockers and Order Fillers | 85,630 | 11.65–11.65 |
| Los Angeles-Long Beach-Anaheim, CA | 35-3031 | Waiters and Waitresses | 85,210 | 2.82–2.82 |

The May California occupation usage leaders are shown below at their original O*NET-code grain. These percentages reflect the observed usage mix, not the percentage of workers adopting AI:

| O*NET code | Occupation | California usage share (%) |
| --- | --- | --- |
| 15-1299.03 | Document Management Specialists | 6.87 |
| 25-4022.00 | Librarians and Media Collections Specialists | 5.36 |
| 41-2021.00 | Counter and Rental Clerks | 3.60 |
| 27-3041.00 | Editors | 2.49 |
| 27-3043.00 | Writers and Authors | 2.35 |
| 13-2071.00 | Credit Counselors | 1.97 |
| 41-4012.00 | Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products | 1.83 |
| 15-1232.00 | Computer User Support Specialists | 1.75 |
| 25-4031.00 | Library Technicians | 1.68 |
| 27-3042.00 | Technical Writers | 1.64 |

For regional comparisons, coverage varies and incomplete cells remain visible:

| Area | Occupation cells | Cells with global work-use context | Coverage |
| --- | --- | --- | --- |
| North Coast Region of California nonmetropolitan area | 344 | 274 | 79.7% |
| Eastern Sierra-Mother Lode Region of California nonmetropolitan area | 277 | 223 | 80.5% |
| North Valley-Northern Mountains Region of California nonmetropolitan area | 352 | 278 | 79.0% |
| Bakersfield-Delano, CA | 479 | 370 | 77.2% |
| Chico, CA | 290 | 233 | 80.3% |
| El Centro, CA | 228 | 187 | 82.0% |
| Fresno, CA | 531 | 412 | 77.6% |
| Hanford-Corcoran, CA | 196 | 161 | 82.1% |
| Los Angeles-Long Beach-Anaheim, CA | 754 | 555 | 73.6% |
| Merced, CA | 273 | 220 | 80.6% |
| Modesto, CA | 400 | 316 | 79.0% |
| Napa, CA | 268 | 219 | 81.7% |
| Oxnard-Thousand Oaks-Ventura, CA | 496 | 386 | 77.8% |
| Redding, CA | 294 | 242 | 82.3% |
| Riverside-San Bernardino-Ontario, CA | 682 | 513 | 75.2% |
| Sacramento-Roseville-Folsom, CA | 658 | 506 | 76.9% |
| Salinas, CA | 374 | 294 | 78.6% |
| San Diego-Chula Vista-Carlsbad, CA | 682 | 514 | 75.4% |
| San Francisco-Oakland-Fremont, CA | 701 | 529 | 75.5% |
| San Jose-Sunnyvale-Santa Clara, CA | 592 | 463 | 78.2% |
| San Luis Obispo-Paso Robles, CA | 372 | 306 | 82.3% |
| Santa Cruz-Watsonville, CA | 334 | 280 | 83.8% |
| Santa Maria-Santa Barbara, CA | 438 | 357 | 81.5% |
| Santa Rosa-Petaluma, CA | 424 | 341 | 80.4% |
| Stockton-Lodi, CA | 449 | 346 | 77.1% |
| Vallejo, CA | 367 | 295 | 80.4% |
| Visalia, CA | 365 | 290 | 79.5% |
| Yuba City, CA | 227 | 186 | 81.9% |

Higher exposure would need its own measure; work-use percentage is not a substitute. Employment × exposure, even if exposure were provided, would be an index rather than a count of displaced workers. Likewise, employment × median wage is not total payroll. The supplied wage distributions and mean wages can support separate economic-context analysis, with their missingness and censoring disclosed.

## 8. What weighting method should be used?

Final weights require a policy objective: worker reach, earnings, equity, demand, or transition risk. The proposed 30/25/15/15/15 dashboard weights cannot be applied without exposure and national outlook data, and were not approved by a stakeholder in the supplied materials. Do not redistribute those missing weights silently; that would change the score's meaning. Keep the indicators separate for this assignment. After acquiring the missing inputs and validating mappings, document normalization, missing-data eligibility, weights, and sensitivity to alternative weights before presenting a priority ranking.

## 9. Can Vision B be Accenture-specific?

**No.** None of the four files supplies Accenture role mappings, headcounts, role-level adoption, skill proficiency, workflow timing, implementation costs, or business outcomes. The dictionary and native occupation AI tables can support an external role comparison, but California employment is not Accenture headcount and global AI behavior is not internal adoption. These BLS workbooks are area tables, not an official national occupational employment table.

Before selecting real company pilots, obtain the role-to-occupation mapping, headcount and task mix, current tool use and skills, quality/error measures, training costs, workflow constraints, and employee input. Preserve privacy and only use appropriately aggregated internal data. The external comparison should be described as a hypothesis-generating screen, not an Accenture investment recommendation.

## 10. What additional decision-important input is needed for each vision?

**Vision A — employment and wage context:** the supplied BLS files provide this addition at area × occupation grain. Its link is a validated occupation code; failures include combined categories, unmatched codes, missing estimates, lagged releases, and the mismatch with RPU geography. The most decision-critical remaining inputs are local skill gaps, employer demand, program feasibility/cost, and RPU-compatible data if the decision is made in RPUs.

**Vision B — employer behavior/internal readiness:** auxiliary.md proposes Census BTOS as a public employer-behavior source. That workbook is not supplied, so its reported percentages were not recomputed or inserted into the outputs. BTOS's proposed grain is scope × breakdown × question × answer, not SOC; industry percentages cannot be used as measured occupation or company adoption. Internal workforce records are still needed for the company decision. Choosing BTOS context versus employment projections as an additional project source is a team scope decision; neither can be manufactured by cleaning these four inputs.

## 11. Do employers augment or replace tasks, train or hire, and change headcount?

These files describe AI interaction patterns and occupational employment levels, not firm responses to AI. Collaboration percentages cannot show which employers replaced workers or retrained staff. The BTOS figures quoted in auxiliary.md, including its “no employment change” and training-versus-hiring comparisons, remain document-reported claims outside this analysis. If verified for the proper survey scope, they may motivate evaluating incumbent-worker training; they do not validate an exposure-based funding rule or establish causation.

## 12. Data fit, association versus causation, and human review

Vision A has the stronger fit to these inputs because employment and wages are directly observed for California occupation–area cells. Vision B remains an external prototype. Associations between occupation AI usage and employment scale do not show that AI caused displacement, wage changes, productivity gains, or a training need. No causal claim or ROI estimate is supported.

Before a pilot, review worker skill gaps, employer demand, training availability and cost, equity/access, worker preferences, and local feasibility. Before workflow redesign, assess confidentiality, consequences of errors, required human oversight, and quality/productivity outcomes. High automation-related usage alone never establishes safe automation. A suitable pilot evaluation and comparison group would be needed to evaluate effects.

Relative to the alternatives described in alternatives.md, the deliverable standardizes external evidence, preserves missingness and provenance, and exposes linkage gaps. It does not replace local labor-market expertise, worker input, or an organization's formal investment decisions.

## 13. Validation and code review

The pipeline checks source-key uniqueness, code syntax, numeric tokens and ranges, date ordering, publication scope separation, and merge cardinality. It verifies that joining AI context preserves every California occupation–area cell and that source hashes remain unchanged. Tests cover censored wages, unknown tokens, duplicate conflicts, and identifier preservation. A separate validator independently reconciles the exported tables, recomputes the AI ranges, checks geography-specific absence, and verifies file hashes. See [validation_results.json](data/cleaned/validation_results.json) for the actual post-run results and [code_review.md](code_review.md) for the completed once-over.

Original source observations are kept in Parquet; smaller analysis tables are also CSV. See [data_dictionary.md](data_dictionary.md) for keys, units, status fields, and file descriptions. CSV consumers must import identifiers as text to preserve leading zeros.
