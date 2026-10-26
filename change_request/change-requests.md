# Team change requests

Copy this template into the top folder of your team's app repository if `change-requests.md` is missing. If it already exists, add to it; do not replace your teammates' work. Keep your individual evidence and conclusions in `my-audit.md`.

## Claims

Add your name and what you will audit. Choose a different scope from your teammates, or explain the new evidence you will contribute.

| Author | Feature | Number | Distinct scope or new evidence |
| --- | --- | --- | --- |
| | | | |
| Hehua (Leo) Liu | Occupation and OEWS-area filters, including combined selection and reset behavior | Priority Score `92.9193205945` and Global Rank `1` for AREA `40900` / OCC_CODE `15-1232` | Browser reproduction of the occupation-area intersection plus an independent workbook recomputation of all 6,123 eligible scores and ranks |
| Unassigned | Scope and data-coverage summary, including scored versus not-scored records and missing-value disclosure | `6,123 / 11,847 = 51.7%` score coverage | Recompute the eligibility denominator and missing counts from the workbook; confirm unscored records remain visible and are not represented as zero |
| Unassigned | Priority Score distribution histogram and its independence from table filters and map selections | Histogram observation count of `6,123` scored occupation-area records | Sum the histogram bins independently and verify that filtering the records table or changing the map metric does not change the distribution |
| Unassigned | California OEWS area map, four-option metric selector, legend, tooltips, and mapped/unmapped disclosure | For one chosen AREA, independently calculate its Median Priority Score and Score Coverage (%) | Verify the geographic polygon and reproduce the selected area's map metrics from canonical data; confirm exactly four selector options and correct units/color direction |
| Qiyue (Zoe) Zhao | Regional Ranking View: descending employment-weighted ordering and separation from map metric and records-table controls | Los Angeles-Long Beach-Anaheim (AREA `31080`): independently recomputed Regional Priority Score `66.88742717379786` and Regional Rank `3` of `28` | Recalculated from 328 scored detailed occupation records (`TOT_EMP` sum `3,752,450`); inspected `src/aggregation.py::aggregate_areas()`, `src/pipeline.py`, and HTML rendering logic. Static arithmetic and stored ordering verified; browser interaction independence remains unverified. Evidence and limitations documented in individual `my-audit.md`. |

## Requests

Copy this block for each actionable finding and choose a unique ID. Reference that ID in your individual audit. A check that finds no defect belongs in your audit; do not invent a bug to fill a request.

### AUDIT-XX Short description

- Author:
- Status: open
- App version or commit checked:
- Feature or number and its intended behavior or definition:
- Inputs and steps to reproduce:
- Expected result:
- Actual result:
- Evidence (including file, function, and relevant lines if code was checked):
- Likely cause, if established, and remaining uncertainty:
- Requested change:
- Verification check and expected result:
- Implementation commit and verification result, if resolved:

### AUDIT-LEO-01 Clarify that search text must be followed by checkbox selection

- Author: Hehua (Leo) Liu
- Status: open
- App version or commit checked: `project/dashboard_final/AI_Workforce_Investment_Planner.html`, checked October 25, 2026; embedded source-workbook SHA-256 `fff5d5f578cb1f864f669de6cca7d37d5f4cab4f5fd515ac155649c3b344ba3f`.
- Feature or number and its intended behavior or definition: The occupation and OEWS-area controls should let the user find and select values, filter the record table to their intersection, and reset the table without recalculating the fixed Priority Score or Global Rank.
- Inputs and steps to reproduce: Open the app in Chrome; expand **Occupation**; type `Computer User Support Specialists`; observe the narrowed options; select `Computer User Support Specialists - 15-1232`; expand **Area**; type `Sacramento`; select `Sacramento-Roseville-Folsom, CA - 40900`; then select **Reset Table Filters**.
- Expected result: The interface should make clear that typing only finds an option and that selecting its checkbox applies the filter. Selecting occupation `15-1232` should return 28 records; adding area `40900` should return one record with score `92.9` and rank `1`; reset should restore 11,847 records.
- Actual result: The record counts, score, rank, and reset behavior were correct. However, the search boxes only narrow the checkbox options; typing alone does not filter the table, and the interface does not clearly state that the matching checkbox must also be selected.
- Evidence (including file, function, and relevant lines if code was checked): The audited browser path returned 28, then 1, then 11,847 records. `project/audit_checks/leo_priority_score_check.py` independently rebuilt eligibility, percentile components, scores, and ranks from `final_cleaned_core.xlsx`. It matched all 6,123 embedded scored records with maximum absolute score difference `0.0` and zero rank mismatches; the selected row remained AREA `40900` / OCC_CODE `15-1232`, score `92.9193205945`, rank `1`.
- Likely cause, if established, and remaining uncertainty: The text inputs filter the lists of checkbox options rather than the record table, but their labels can be interpreted as direct table searches. This audit covered one Chrome interaction path, not every browser, responsive breakpoint, or CSV export. The dashboard intentionally retains source-missing values rather than imputing zero or a mean; `claude_usage_pct` adds an observed AI-adoption signal but lowers complete-case coverage, so only 6,123 of the 11,847 preserved OEWS rows receive a Priority Score.
- Requested change: Add helper text below both search boxes: `Type to find an option, then select its checkbox to apply the filter.` Alternatively, rename the inputs to `Find occupation options` and `Find area options`.
- Verification check and expected result: Before interaction, the interface should explain the two-step behavior. Typing should continue to narrow available options, selecting a checkbox should filter the table, the audited counts and fixed score/rank should remain unchanged, and reset should restore all 11,847 records.
- Implementation commit and verification result, if resolved: Not yet implemented; verification pending.

Record findings without undoing a teammate's work. Mark a request resolved only after verifying the change.
