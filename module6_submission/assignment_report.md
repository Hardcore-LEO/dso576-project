# DSO 576 Module 6 - Project Data Cleaning

Project: AI Workforce Investment Planner  
Student: Hehua (Leo) Liu
Branch: Leo  
Branch URL: https://github.com/Hardcore-LEO/dso576-project/tree/Leo  
Submitted commit: 4993964fc785f73b9c518b49223af6b6d6192f68  
Business question: Which California occupation x region combinations should be prioritized for AI upskilling and workforce-transition support?

The user selects a California region and reviews occupations using observed AI exposure, employment, wages, and labor-market outlook. The result is a screening shortlist for human review. It is not an automatic funding or automation decision.

## 1. State the project vision and question

**Status: Done**  
Evidence: The vision, business question, and main metrics are stated in plan.md sections 1 and 6.

## 2. Define one row

**Status: Done**  
Evidence: Row definitions and composite keys are documented in plan.md section 4 and checked in outputs/duplicates.csv.

## 3. Preserve the source

**Status: Done**  
Evidence: Five source files are hashed in outputs/source_manifest.json; hashes matched before and after the run.

## 4. Inspect columns and types

**Status: Done**  
Evidence: All declared numeric/date conversions had zero failures; details are in outputs/validation.json and missing_counts.csv.

## 5. Standardize text

**Status: Done**  
Evidence: Only outer whitespace was eligible for trimming. No meaningful text, case, punctuation, or leading-zero identifiers were rewritten.

## 6. Investigate duplicates

**Status: Done**  
Evidence: Exact duplicates and repeated keys are reported separately in outputs/duplicates.csv. No exact duplicate source rows were found.

## 7. Handle missing data

**Status: Done**  
Evidence: Missing counts before/after are in outputs/missing_counts.csv. No blanket imputation was used; source markers have distinct status columns.

## 8. Check suspicious values

**Status: Done**  
Evidence: Suspicious values were flagged before treatment in outputs/suspicious_values.csv. Metric-specific checks prevented the valid Claude value 199.11 from being treated as a percentage outlier.

## 9. Verify merges

**Status: Done**  
Evidence: Two many-to-one exact-code joins preserved 11,847 California occupation-region rows. Exposure unmatched: 1,702; projection unmatched: 0.

## 10. Reconcile changes

**Status: Done**  
Evidence: OEWS started with 198,712 rows. The cleaned base kept all 198,712. The California detailed screening scope has 11,847; 186,865 rows remain in the cleaned base and are reconciled as scope exclusions.

## 11. Check calculations

**Status: Done**  
Evidence: Missing values are not converted to zero or silently reweighted. 9,829 complete rows receive a score; 2,018 remain visible with an insufficient-data status.

## 12. Verify individual records

**Status: Done**  
Evidence: Five predeclared record checks are shown below and stored in outputs/record_checks.csv.

## 13. Test reproducibility

**Status: Done**  
Evidence: The pipeline was run from original files, source hashes were rechecked, and all assertions passed. Run command: python clean_data.py.

## 14. Document remaining limitations

**Status: Done**  
Evidence: The remaining limitations are documented below. They include malformed occupation codes without an authoritative correction and the use of national or global context for a California screening tool.

# Cleaning decision log

- **claude** - Rule: Parsed dates, hierarchy level, and value; added metric units and metric-aware flags. No rows removed. Reason: keep the published meaning and make every change traceable. Check: input 1,636,573; output 1,636,573; exclusions 0; flags 0; failed conversions 0.
- **job_exposure** - Rule: Preserved all records; validated SOC codes and exposure fractions. Invalid codes are join-ineligible, not repaired. Reason: keep the published meaning and make every change traceable. Check: input 756; output 756; exclusions 0; flags 32; failed conversions 0.
- **oews** - Rule: Appended MSA and BOS with area class; converted numeric fields and preserved marker meanings in status columns. No rows removed. Reason: keep the published meaning and make every change traceable. Check: input 198,712; output 198,712; exclusions 0; flags 0; failed conversions 0.
- **projections** - Rule: Separated worksheet title/footer rows, preserved sheet grains, trimmed display titles, and converted numeric measures without changing units. Reason: keep the published meaning and make every change traceable. Check: input 4,876; output 4,844; exclusions 32; flags 0; failed conversions 0.
- **analysis_scope_and_joins** - Rule: Selected California detailed cross-industry region records, made two validated many-to-one context joins, and calculated a transparent four-component within-region screening rank. Base records and employment checksum were preserved. Reason: keep the published meaning and make every change traceable. Check: input 198,712; output 11,847; exclusions 186,865; flags 2,018; failed conversions 0.

# Five predeclared record checks

The expected results were saved in `record_expectations.json` before the cleaning pipeline read its outputs.

- **R1** `job_exposure.csv` row 5, `occ_code`: original `Nov-11`; expected `Nov-11`; actual `Nov-11`; status `False`; **PASS**. Reason: The date-like value is not a valid six-digit SOC code. Preserve it and do not guess a repair.
- **R2** `aei_claude_ai_2026-06-26.csv` row 396056, `value`: original `199.11`; expected `199.11`; actual `199.11`; status `False`; **PASS**. Reason: A value above 100 is valid for a time metric; a global percentage rule would be wrong.
- **R3** `BOS_M2025_dl.xlsx` row 15, `TOT_EMP`: original `**`; expected `None`; actual `None`; status `employment_estimate_unavailable`; **PASS**. Reason: Unavailable employment is unknown, not zero.
- **R4** `BOS_M2025_dl.xlsx` row 1711, `H_MEAN`: original `#`; expected `None`; actual `None`; status `censored_exact_value_unavailable`; **PASS**. Reason: A censored wage is not an exact value and must not be imputed.
- **R5** `occupation.XLSX` row 4, `Employment change, percent, 2025–35`: original `-34.4`; expected `-34.4`; actual `-34.4`; status `None`; **PASS**. Reason: Negative projected growth is meaningful and must remain negative.

# How one Codex suggestion was checked

Suggestion: Do not automatically repair date-like occupation codes; preserve and flag them before exact-code joins.

Independent check: Re-read the original CSV without pipeline helpers; apply an anchored six-digit SOC pattern and count duplicate valid keys.

Result: 32 invalid and 724 valid codes; duplicate valid codes: 0. Accepted. The 32 malformed strings are not sufficient evidence for a unique repair; all 724 valid exact codes are unique.

I checked this suggestion by reading the original exposure file again and applying a simple six-digit SOC pattern. I accepted the suggestion because the 32 malformed values do not contain enough information for a reliable correction.

# Result summary

- Claude metrics: 1,636,573 rows retained; declared key duplicates: 0.
- Exposure: 756 rows retained; 32 malformed codes flagged and excluded only from exact-code joins.
- OEWS: 198,712 rows retained; numeric conversion failures: 0.
- Analytical table: 11,847 detailed occupation-area rows across 28 areas and 783 occupations.
- Exposure matches: 10,145; projection matches: 11,847.
- Screening eligibility: 9,829 complete four-component rows; 2,018 incomplete rows; 701 top-25 review rows across regions.
- Screening weights: 40% observed AI exposure, 30% regional employment, 15% lower-wage transition-need proxy, and 15% weaker-outlook transition-need proxy. Components are within-region percentiles and remain visible.
- Employment checksum before/after joins: 17,277,510 / 17,277,510 jobs.
- Purposeful difficult-case sample: 30 rows (not a statistical sample).

# Cleaned sample

The following 30 rows were selected on purpose to show difficult cases. The sample is not random. It includes high-employment records, high-exposure records, unmatched occupation codes, missing-value markers, malformed codes, a high but valid Claude time value, and negative projected growth.

- **analysis_record** - MSA_M2025_dl.xlsx row 79222: Los Angeles-Long Beach-Anaheim, CA 31-1120 Home Health and Personal Care Aides. employment=385530.0; annual wage=35890.0; outlook=18.1. Reason: high employment
- **analysis_record** - MSA_M2025_dl.xlsx row 79272: Los Angeles-Long Beach-Anaheim, CA 35-3023 Fast Food and Counter Workers. employment=160270.0; annual wage=41080.0; AI exposure=0.0; outlook=5.8. Reason: high employment
- **analysis_record** - MSA_M2025_dl.xlsx row 79328: Los Angeles-Long Beach-Anaheim, CA 41-2031 Retail Salespersons. employment=130650.0; annual wage=43010.0; AI exposure=0.3222; outlook=-0.3. Reason: high employment
- **analysis_record** - MSA_M2025_dl.xlsx row 79630: Los Angeles-Long Beach-Anaheim, CA 53-7062 Laborers and Freight, Stock, and Material Movers, Hand. employment=120720.0; annual wage=44070.0; AI exposure=0.0; outlook=1.8. Reason: high employment
- **analysis_record** - MSA_M2025_dl.xlsx row 121408: San Francisco-Oakland-Fremont, CA 31-1120 Home Health and Personal Care Aides. employment=119120.0; annual wage=38810.0; outlook=18.1. Reason: high employment
- **analysis_record** - MSA_M2025_dl.xlsx row 79394: Los Angeles-Long Beach-Anaheim, CA 43-9061 Office Clerks, General. employment=112270.0; annual wage=50980.0; AI exposure=0.4504; outlook=-6.0. Reason: high employment
- **analysis_record** - BOS_M2025_dl.xlsx row 3283: North Coast Region of California nonmetropolitan area 15-1251 Computer Programmers. employment=40.0; annual wage=104610.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - MSA_M2025_dl.xlsx row 9721: Bakersfield-Delano, CA 15-1251 Computer Programmers. employment=100.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - MSA_M2025_dl.xlsx row 48486: Fresno, CA 15-1251 Computer Programmers. employment=110.0; annual wage=98190.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - MSA_M2025_dl.xlsx row 78941: Los Angeles-Long Beach-Anaheim, CA 15-1251 Computer Programmers. employment=3400.0; annual wage=108020.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - MSA_M2025_dl.xlsx row 84754: Merced, CA 15-1251 Computer Programmers. employment=30.0; annual wage=102030.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - MSA_M2025_dl.xlsx row 88736: Modesto, CA 15-1251 Computer Programmers. employment=50.0; annual wage=97650.0; AI exposure=0.7451; outlook=-7.3. Reason: high observed exposure
- **analysis_record** - BOS_M2025_dl.xlsx row 3231: North Coast Region of California nonmetropolitan area 11-2021 Marketing Managers. employment=90.0; annual wage=150420.0; outlook=6.9. Reason: unmatched exposure key
- **analysis_record** - BOS_M2025_dl.xlsx row 3232: North Coast Region of California nonmetropolitan area 11-2022 Sales Managers. employment=490.0; annual wage=112110.0; outlook=4.5. Reason: unmatched exposure key
- **analysis_record** - BOS_M2025_dl.xlsx row 3233: North Coast Region of California nonmetropolitan area 11-3012 Administrative Services Managers. employment=220.0; annual wage=106020.0; outlook=5.2. Reason: unmatched exposure key
- **analysis_record** - BOS_M2025_dl.xlsx row 3234: North Coast Region of California nonmetropolitan area 11-3013 Facilities Managers. employment=120.0; annual wage=102800.0; outlook=4.6. Reason: unmatched exposure key
- **analysis_record** - BOS_M2025_dl.xlsx row 3354: North Coast Region of California nonmetropolitan area 27-3041 Editors. annual wage=70020.0; AI exposure=0.246; outlook=-1.1. Reason: unavailable employment
- **analysis_record** - BOS_M2025_dl.xlsx row 3367: North Coast Region of California nonmetropolitan area 29-1151 Nurse Anesthetists. annual wage=297960.0; AI exposure=0.0; outlook=9.7. Reason: unavailable employment
- **analysis_record** - BOS_M2025_dl.xlsx row 3391: North Coast Region of California nonmetropolitan area 31-9011 Massage Therapists. annual wage=64660.0; AI exposure=0.0; outlook=15.3. Reason: unavailable employment
- **analysis_record** - BOS_M2025_dl.xlsx row 3529: North Coast Region of California nonmetropolitan area 47-4041 Hazardous Materials Removal Workers. annual wage=56530.0; AI exposure=0.0; outlook=1.5. Reason: unavailable employment
- **invalid_exposure_code** - job_exposure.csv row 5: Nov-11. original=Nov-11; clean=Nov-11; status=join ineligible. Reason: date-like SOC code preserved without guessed repair
- **invalid_exposure_code** - job_exposure.csv row 6: Nov-21. original=Nov-21; clean=Nov-21; status=join ineligible. Reason: date-like SOC code preserved without guessed repair
- **invalid_exposure_code** - job_exposure.csv row 7: Nov-22. original=Nov-22; clean=Nov-22; status=join ineligible. Reason: date-like SOC code preserved without guessed repair
- **invalid_exposure_code** - job_exposure.csv row 8: Nov-32. original=Nov-32; clean=Nov-32; status=join ineligible. Reason: date-like SOC code preserved without guessed repair
- **special_marker** - BOS_M2025_dl.xlsx row 15: 11-9039. original=**; status=employment_estimate_unavailable. Reason: source marker kept distinct from zero
- **special_marker** - BOS_M2025_dl.xlsx row 1711: 29-1214. original=#; status=censored_exact_value_unavailable. Reason: source marker kept distinct from zero
- **metric_specific_range** - aei_claude_ai_2026-06-26.csv row 396056: . original=199.11; clean=199.11; status=valid time metric. Reason: value above 100 retained because metric is not a percentage
- **negative_projection** - occupation.XLSX row 4: 43-9022. original=-34.4; clean=-34.4; status=valid negative change. Reason: decline is meaningful and retained
- **negative_projection** - occupation.XLSX row 5: 43-2021. original=-27.6; clean=-27.6; status=valid negative change. Reason: decline is meaningful and retained
- **negative_projection** - occupation.XLSX row 6: 43-2011. original=-26.0; clean=-26.0; status=valid negative change. Reason: decline is meaningful and retained

# Interpretation and limitations

The cleaned data still represent the published phenomena because original source rows remain in cleaned bases, identifiers and units are preserved, missing/censored estimates are not turned into zeros, and joins do not multiply rows or employment. The analytical table changes scope, not the underlying sources. Exposure and projections are national occupation context; Claude measures include global/country/subregion observations. None should be described as a local causal effect. The screening score is a transparent review aid, not an automatic funding or automation decision. Its weights and the lower-wage/weaker-outlook proxies require human review. The 32 malformed exposure codes remain unresolved until an authoritative source mapping is available.
