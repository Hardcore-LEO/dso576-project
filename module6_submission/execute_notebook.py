"""Build and execute the submission notebook.

The detailed transformations remain in clean_data.py.  This file creates a
short, template-style notebook that displays raw evidence, cleaning rules,
cleaned examples, audit tables, integration checks, and final results.
"""

import ast
import contextlib
import io
import textwrap
import traceback
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "cleaning_assignment.ipynb"


def markdown(text):
    return nbformat.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text):
    return nbformat.v4.new_code_cell(textwrap.dedent(text).strip())


def build_notebook():
    cells = [
        markdown(
            """
            # AI Workforce Investment Planner

            **Project:** AI Workforce Investment Planner  
            **Student:** Hehua (Leo) Liu - confirmation pending  
            **Branch:** `Leo`  
            **Branch URL:** [https://github.com/Hardcore-LEO/dso576-project/tree/Leo](https://github.com/Hardcore-LEO/dso576-project/tree/Leo)  
            **Submitted commit:** Not yet submitted

            **Business question:** The Executive Director of the California Workforce Development Board must decide which California occupation × region combinations should be prioritized for AI upskilling and workforce-transition support.

            The output is a transparent screening shortlist for workforce-planning review. It is not an automatic funding decision, and higher AI exposure does not automatically mean that a job should be automated.

            ## Workflow

            1. Inspect each original source.
            2. Apply documented, source-specific cleaning rules.
            3. Show cleaned records and reconcile row counts.
            4. Integrate California occupation × region records.
            5. Validate the final analysis and five predeclared records.
            """
        ),
        markdown(
            """
            # Inspect and clean the data: 14-item checklist

            ## 1 State the project vision and question

            **Status: Done**  
            **Evidence or explanation:** The project produces a transparent California workforce-planning shortlist. The main comparison is the within-region screening score built from observed AI exposure, employment size, annual wage, and national employment outlook. See **Business question** and **Screening score**.

            ## 2 Define one row

            **Status: Done**  
            **Evidence or explanation:** In the final analysis, one row represents one detailed occupation in one California metropolitan or nonmetropolitan region. `AREA` and `OCC_CODE`, together with the retained OEWS grain fields, identify the record. See **Data integration and merge verification** and **Duplicate checks**.

            ## 3 Preserve the source

            **Status: Done**  
            **Evidence or explanation:** The five original files remain unchanged. File names, sizes, and SHA-256 hashes are shown in **Source inventory**, and the pipeline confirms that hashes are unchanged after cleaning.

            ## 4 Inspect columns and types

            **Status: Done**  
            **Evidence or explanation:** Dates and numeric fields are converted with explicit rules. Failed conversion counts are reported after each source and are zero for the declared conversions. See each source's **Original data checks**, **Cleaning rules**, and **Row-count reconciliation**.

            ## 5 Standardize text

            **Status: Done**  
            **Evidence or explanation:** Only outside whitespace is removed from display text. Meaningful spelling, punctuation, capitalization, and leading zeros in identifiers are preserved. Raw occupation titles are retained in projection output columns ending in `__raw`.

            ## 6 Investigate duplicates

            **Status: Done**  
            **Evidence or explanation:** Exact duplicate rows and repeated keys are checked separately. The results are displayed in **Final validation - Duplicate checks**. Valid exposure SOC codes are unique.

            ## 7 Handle missing data

            **Status: Done**  
            **Evidence or explanation:** Missing counts before and after cleaning are displayed in **Missing values before and after cleaning**. OEWS markers such as `**`, `*`, and `#` become missing numeric values with separate status columns; they are never changed to zero.

            ## 8 Check suspicious values

            **Status: Done**  
            **Evidence or explanation:** Suspicious values are flagged before treatment. Thirty-two malformed SOC strings are preserved and made join-ineligible. The Claude value 199.11 is retained because it belongs to a time metric, and negative projection growth remains negative.

            ## 9 Verify merges

            **Status: Done**  
            **Evidence or explanation:** Both joins use exact SOC codes and are validated as many-to-one. **Join and checksum verification** reports 10,145 exposure matches, 1,702 exposure nonmatches, 11,847 projection matches, and zero projection nonmatches.

            ## 10 Reconcile changes

            **Status: Done**  
            **Evidence or explanation:** **Changes after each major transformation** reports starting rows, final rows, exclusions, changed cells, flags, failed conversions, and explanations. The employment checksum remains 17,277,510 before and after joins.

            ## 11 Check calculations

            **Status: Done**  
            **Evidence or explanation:** Scores are calculated only when all four inputs are present; missing components are not treated as zero or reweighted. There are 9,829 eligible rows and 2,018 retained incomplete rows. See **Screening score**.

            ## 12 Verify individual records

            **Status: Done**  
            **Evidence or explanation:** **Five predeclared record checks** compares original, expected, and actual values for five difficult records. All five checks pass.

            ## 13 Test reproducibility

            **Status: Done**  
            **Evidence or explanation:** `python execute_notebook.py` rebuilds and runs the notebook from the original data. `python -m unittest -v test_clean_data.py` runs six automated tests. The executed notebook confirms that every pipeline assertion passed.

            ## 14 Document remaining limitations

            **Status: Done**  
            **Evidence or explanation:** The **Remaining limitations** section explains unresolved malformed codes, geographic differences between sources, missing estimates, and the judgment involved in screening weights.
            """
        ),
        markdown(
            """
            ## Setup and reproducible pipeline

            The notebook uses basic pandas commands for inspection. The longer cleaning functions are stored in `clean_data.py` so that the notebook stays readable and the same rules can be rerun.
            """
        ),
        code(
            """
            from pathlib import Path
            import json
            import pandas as pd
            import clean_data

            ROOT = Path.cwd()
            SOURCE = ROOT.parent
            OUTPUT = ROOT / "outputs"

            pd.set_option("display.max_columns", None)
            pd.set_option("display.max_colwidth", None)
            pd.set_option("display.width", 200)

            validation = clean_data.main(show_summary=False)
            stage_changes = pd.read_csv(OUTPUT / "stage_changes.csv")
            missing_counts = pd.read_csv(OUTPUT / "missing_counts.csv")
            duplicate_checks = pd.read_csv(OUTPUT / "duplicates.csv")

            print("Pipeline completed successfully.")
            print("All validation assertions passed:", validation["all_assertions_passed"])
            print("Original source hashes unchanged:", validation["source_hashes_unchanged"])
            """
        ),
        markdown(
            """
            ## Source inventory

            These are the five input files used by the cleaning pipeline. No file outside the supplied `clean_data` folder is used as a data source.

            - Anthropic Economic Index snapshot: `aei_claude_ai_2026-06-26.csv` (2026-06-26 snapshot).
            - Course-provided occupation exposure file: `job_exposure.csv` (no separate version date stated in the supplied file).
            - BLS OEWS metropolitan and nonmetropolitan estimates: May 2025 releases.
            - BLS Employment Projections workbook: 2025-2035 projection period.
            """
        ),
        code(
            """
            source_inventory = pd.read_json(OUTPUT / "source_manifest.json")
            source_inventory[["source_file", "bytes", "sha256"]]
            """
        ),
        markdown(
            """
            # 1. Anthropic Economic Index

            This source contains Claude usage metrics by date, geography, category, hierarchy level, and task or occupation node. Metric meaning depends on `metric_id`, so the values cannot all be treated as percentages.
            """
        ),
        markdown(
            """
            ## Original data checks

            The first five source rows are displayed before cleaning. The audit checks row count, duplicates, date conversion, numeric conversion, and metric units.
            """
        ),
        code(
            """
            claude_raw = pd.read_csv(SOURCE / "aei_claude_ai_2026-06-26.csv", nrows=5)
            print("Full source rows:", f'{validation["claude"]["rows"]:,}')
            claude_raw
            """
        ),
        code(
            """
            pd.DataFrame({
                "check": [
                    "Exact duplicate excess",
                    "Declared-key duplicate excess",
                    "Failed date conversions",
                    "Failed numeric conversions",
                    "Suspicious values after metric-aware checks",
                ],
                "result": [
                    validation["claude"]["exact_duplicate_excess"],
                    validation["claude"]["duplicate_key_excess"],
                    validation["claude"]["failed_dates"],
                    validation["claude"]["failed_numeric"],
                    validation["claude"]["suspicious_values"],
                ],
            })
            """
        ),
        markdown(
            """
            ## Cleaning rules

            - Preserve every source row and add `_source_file` and `_source_row`.
            - Parse the two date columns as dates.
            - Convert hierarchy level and value with `pd.to_numeric()`.
            - Assign units from `metric_id` instead of applying one universal range.
            - Flag a value only when it violates the rule for its own metric.
            """
        ),
        markdown("## Cleaned data preview"),
        code(
            """
            claude_clean = pd.read_csv(OUTPUT / "cleaned_claude_metrics.csv.gz", nrows=8)
            claude_clean[[
                "_source_row", "date_start", "geo_level", "category_name",
                "metric_id", "value", "metric_unit", "suspicious_value"
            ]]
            """
        ),
        markdown("## Row-count reconciliation"),
        code(
            """
            stage_changes.loc[stage_changes["stage"] == "claude", [
                "stage", "input_rows", "output_rows", "rows_excluded",
                "changed_cells", "new_flags", "summary"
            ]]
            """
        ),
        markdown(
            """
            **Summary:** All Claude rows are retained. Dates and numeric values convert successfully, the declared key is unique, and metric-specific units prevent a valid time value such as 199.11 from being incorrectly flagged as a percentage.
            """
        ),
        markdown(
            """
            # 2. Occupation AI-exposure data

            This source supplies observed AI exposure by occupation. A valid join key must follow the six-digit SOC pattern `NN-NNNN`.
            """
        ),
        markdown("## Original data checks"),
        code(
            """
            exposure_raw = pd.read_csv(SOURCE / "job_exposure.csv")
            valid_soc = exposure_raw["occ_code"].astype(str).str.fullmatch(r"\d{2}-\d{4}")
            print("Shape:", exposure_raw.shape)
            print("Valid SOC codes:", int(valid_soc.sum()))
            print("Malformed codes:", int((~valid_soc).sum()))
            print("Exact duplicate rows:", int(exposure_raw.duplicated().sum()))
            exposure_raw.head()
            """
        ),
        markdown(
            """
            ## Cleaning rules

            - Preserve every row and the original occupation-code text.
            - Trim outside spaces from text fields.
            - Convert exposure to numeric without changing its unit.
            - Mark malformed SOC codes as not eligible for exact-code joins.
            - Do not guess repairs for date-like values such as `Nov-11`.
            """
        ),
        markdown("## Cleaned data preview"),
        code(
            """
            exposure_clean = pd.read_csv(OUTPUT / "cleaned_job_exposure.csv")
            exposure_clean.head(8)
            """
        ),
        markdown("## Flagged malformed-code examples"),
        code(
            """
            exposure_clean.loc[~exposure_clean["code_join_eligible"], [
                "_source_row", "occ_code_raw", "title", "observed_exposure",
                "code_format_valid", "code_join_eligible"
            ]].head(10)
            """
        ),
        markdown("## Row-count reconciliation"),
        code(
            """
            stage_changes.loc[stage_changes["stage"] == "job_exposure", [
                "stage", "input_rows", "output_rows", "rows_excluded",
                "new_flags", "failed_conversions", "summary"
            ]]
            """
        ),
        markdown(
            """
            **Summary:** All 756 records remain in the cleaned file. The 32 malformed occupation codes are visible and flagged rather than silently deleted or guessed. The 724 valid SOC codes are unique and can be joined safely.
            """
        ),
        markdown(
            """
            # 3. BLS OEWS employment and wage data

            The metropolitan and nonmetropolitan workbooks contain May 2025 employment and wage estimates. Symbols such as `**`, `*`, and `#` have different meanings and must not be converted to zero.
            """
        ),
        markdown("## Original data checks"),
        code(
            """
            oews_raw_msa = pd.read_excel(
                SOURCE / "MSA_M2025_dl.xlsx", sheet_name="MSA_M2025_dl", nrows=5
            )
            oews_raw_msa
            """
        ),
        code(
            """
            oews_raw_nonmetro = pd.read_excel(
                SOURCE / "BOS_M2025_dl.xlsx", sheet_name="BOS_M2025_dl", nrows=5
            )
            oews_raw_nonmetro
            """
        ),
        code(
            """
            marker_rows = []
            for filename, columns in validation["oews"]["marker_counts"].items():
                for column, counts in columns.items():
                    for marker, count in counts.items():
                        marker_rows.append({
                            "source_file": filename,
                            "column": column,
                            "source_marker": "blank" if marker == "" else marker,
                            "count": count,
                        })
            marker_table = pd.DataFrame(marker_rows)
            marker_table.head(12)
            """
        ),
        markdown(
            """
            ## Cleaning rules

            - Add source file, sheet, source row, release, and area class.
            - Append metropolitan and nonmetropolitan records with `pd.concat()`.
            - Convert published numeric fields with `pd.to_numeric()`.
            - Store each source marker's meaning in a matching `__status` column.
            - Keep missing, unavailable, thresholded, and censored estimates as missing numeric values, not zero.
            - Check wage percentile order after conversion.
            """
        ),
        markdown("## Cleaned data preview"),
        code(
            """
            oews_clean = pd.read_csv(OUTPUT / "cleaned_oews.csv.gz", nrows=8)
            oews_clean[[
                "_source_file", "_source_row", "area_class", "AREA", "AREA_TITLE",
                "OCC_CODE", "OCC_TITLE", "TOT_EMP", "TOT_EMP__status",
                "A_MEAN", "A_MEAN__status"
            ]]
            """
        ),
        markdown("## Cleaned examples of special source markers"),
        code(
            """
            oews_special = pd.read_csv(
                OUTPUT / "cleaned_oews.csv.gz",
                usecols=["_source_file", "_source_row", "OCC_CODE", "OCC_TITLE",
                         "TOT_EMP", "TOT_EMP__status", "H_MEAN", "H_MEAN__status"]
            )
            oews_special.loc[
                oews_special["TOT_EMP__status"].notna() |
                oews_special["H_MEAN__status"].notna()
            ].head(10)
            """
        ),
        markdown("## Row-count reconciliation"),
        code(
            """
            stage_changes.loc[stage_changes["stage"] == "oews", [
                "stage", "input_rows", "output_rows", "rows_excluded",
                "failed_conversions", "summary"
            ]]
            """
        ),
        markdown(
            """
            **Summary:** The two OEWS tables produce 198,712 cleaned records with no row loss and no failed numeric conversions. Marker meanings remain available in status columns, so an unavailable estimate is distinguishable from a real zero.
            """
        ),
        markdown(
            """
            # 4. BLS employment projections

            The workbook contains multiple tables with different grains. Each table is cleaned separately so that titles, footer rows, and numeric fields are handled without mixing table meanings.
            """
        ),
        markdown("## Original data checks"),
        code(
            """
            projection_book = pd.ExcelFile(SOURCE / "occupation.XLSX")
            print("Workbook sheets:", projection_book.sheet_names)
            projection_raw = pd.read_excel(
                SOURCE / "occupation.XLSX", sheet_name="Table 1.2", header=1, nrows=5
            )
            projection_raw
            """
        ),
        markdown(
            """
            ## Cleaning rules

            - Preserve workbook, sheet, and source-row lineage.
            - Remove only worksheet title and footer rows that are not observations.
            - Trim display titles while preserving a raw-title column.
            - Convert numeric measures without changing thousands, dollars, percentages, or rates.
            - Keep negative projected employment change because decline is meaningful.
            - Save every cleaned table separately.
            """
        ),
        markdown("## Cleaned data preview"),
        code(
            """
            projection_clean = pd.read_csv(OUTPUT / "projections" / "table_1_2.csv")
            projection_clean.head(8)
            """
        ),
        markdown("## Row-count reconciliation"),
        code(
            """
            pd.DataFrame({
                "measure": ["Input worksheet rows", "Clean data rows", "Non-data title/footer rows"],
                "count": [
                    validation["projections"]["input_rows"],
                    validation["projections"]["data_rows"],
                    validation["projections"]["nondata_rows"],
                ],
            })
            """
        ),
        markdown(
            """
            **Summary:** The workbook contains 4,876 inspected rows. Thirty-two title or footer rows are documented as non-data, leaving 4,844 cleaned observations across the projection tables.
            """
        ),
        markdown(
            """
            # 5. Data integration and merge verification

            The analysis begins with California detailed-occupation, cross-industry OEWS records. National AI exposure and national employment outlook are added by exact SOC occupation code. The joins provide context; they do not create local causal estimates.
            """
        ),
        code(
            """
            merge_plan = pd.DataFrame([
                {"left table": "California OEWS", "right table": "AI exposure", "join key": "OCC_CODE = occ_code", "validation": "many-to-one"},
                {"left table": "California OEWS + exposure", "right table": "Projection Table 1.2", "join key": "OCC_CODE = projection code", "validation": "many-to-one"},
            ])
            merge_plan
            """
        ),
        markdown("## Integrated data preview"),
        code(
            """
            analysis = pd.read_csv(OUTPUT / "analysis_california_occupation_region.csv.gz")
            print("Shape:", analysis.shape)
            analysis[[
                "AREA", "AREA_TITLE", "area_class", "OCC_CODE", "OCC_TITLE",
                "observed_exposure", "TOT_EMP", "A_MEAN",
                "projected_employment_change_pct_2025_35", "screening_status",
                "screening_score", "screening_rank_within_region"
            ]].head(8)
            """
        ),
        markdown("## Join and checksum verification"),
        code(
            """
            metrics = validation["analysis"]
            pd.DataFrame({
                "check": [
                    "California base rows", "Exposure matches", "Exposure unmatched",
                    "Projection matches", "Projection unmatched", "California regions",
                    "Employment before joins", "Employment after joins"
                ],
                "result": [
                    metrics["base_rows"], metrics["exposure_matches"], metrics["exposure_unmatched"],
                    metrics["projection_matches"], metrics["projection_unmatched"], metrics["areas"],
                    metrics["employment_checksum_before"], metrics["employment_checksum_after"]
                ]
            })
            """
        ),
        markdown(
            """
            ## Screening score

            The score is calculated only when all four inputs are present. Within each region, it combines 40% observed AI exposure, 30% employment size, 15% lower annual wage as a transition-support proxy, and 15% weaker national outlook as a transition-support proxy. All components remain visible for review.
            """
        ),
        code(
            """
            print("Eligible for scoring:", f'{metrics["screening_eligible_rows"]:,}')
            print("Retained without a score:", f'{metrics["screening_ineligible_rows"]:,}')
            print("Top-25 shortlist rows:", f'{metrics["shortlist_rows"]:,}')
            analysis["screening_score"].describe().to_frame("screening_score")
            """
        ),
        markdown(
            """
            **Summary:** The many-to-one joins preserve all 11,847 California base rows and preserve the employment checksum of 17,277,510 jobs. Missing exposure does not remove a record; it gives the record an incomplete screening status.
            """
        ),
        markdown(
            """
            # 6. Final validation

            These tables summarize row changes, duplicate checks, and missing-value changes. They make each major transformation auditable instead of relying only on the statement that the code ran.
            """
        ),
        markdown(
            """
            ## Cleaning decision log

            Each row documents the applied rule, its reason, and the numerical check used to verify the result.
            """
        ),
        code(
            """
            decision_log = stage_changes[[
                "stage", "summary", "input_rows", "output_rows", "rows_excluded",
                "new_flags", "failed_conversions"
            ]].copy()
            decision_log = decision_log.rename(columns={"summary": "rule"})
            decision_log["reason"] = "Preserve source meaning and make every change traceable."
            decision_log["check"] = (
                "input=" + decision_log["input_rows"].astype(str)
                + "; output=" + decision_log["output_rows"].astype(str)
                + "; excluded=" + decision_log["rows_excluded"].astype(str)
                + "; flags=" + decision_log["new_flags"].astype(str)
                + "; failed conversions=" + decision_log["failed_conversions"].astype(str)
            )
            decision_log[["stage", "rule", "reason", "check"]]
            """
        ),
        markdown("## Changes after each major transformation"),
        code("stage_changes"),
        markdown("## Duplicate checks"),
        code("duplicate_checks"),
        markdown("## Missing values before and after cleaning"),
        code(
            """
            missing_summary = missing_counts.pivot_table(
                index=["table", "column"], columns="phase", values="missing",
                aggfunc="first"
            ).reset_index()
            missing_summary.head(20)
            """
        ),
        markdown("## Important categorical and numeric checks"),
        code(
            """
            pd.DataFrame({
                "measure": [
                    "Unique California regions", "Unique occupations", "Eligible rows",
                    "Ineligible rows", "Minimum score", "Maximum score"
                ],
                "result": [
                    analysis["AREA"].nunique(), analysis["OCC_CODE"].nunique(),
                    int(analysis["screening_eligible"].sum()),
                    int((~analysis["screening_eligible"]).sum()),
                    analysis["screening_score"].min(), analysis["screening_score"].max()
                ]
            })
            """
        ),
        markdown(
            """
            ## Five predeclared record checks

            These five records were declared before the final run. They test the most important difficult cases: a malformed occupation code, a high but valid time metric, unavailable employment, a censored wage, and negative projected growth.
            """
        ),
        code(
            """
            record_checks = pd.read_csv(OUTPUT / "record_checks.csv")
            record_checks[[
                "id", "source_file", "source_sheet", "source_row", "field",
                "original", "actual", "actual_status", "passed", "reason"
            ]]
            """
        ),
        code(
            """
            assert record_checks["passed"].all()
            print(
                f'{validation["record_checks_passed"]} of '
                f'{validation["record_checks_total"]} predeclared checks passed.'
            )
            """
        ),
        markdown(
            """
            ## How one Codex suggestion was checked

            Codex suggested preserving date-like occupation codes instead of guessing corrections. The original exposure CSV was read again without the cleaning helpers, an anchored six-digit SOC pattern was applied, and valid-code duplicates were counted independently. The result below supports accepting the suggestion.
            """
        ),
        code(
            """
            pd.DataFrame([validation["codex_check"]])
            """
        ),
        markdown(
            """
            # 7. Saved cleaned outputs

            The full cleaned tables, audit files, and compact submission sample are saved without overwriting any original source file.
            """
        ),
        code(
            """
            saved_outputs = ["final_cleaned_sample.csv"] + sorted(
                str(path.relative_to(ROOT))
                for path in OUTPUT.rglob("*")
                if path.is_file()
            )
            pd.DataFrame({"saved_file": saved_outputs})
            """
        ),
        markdown(
            """
            # 8. Difficult-case cleaned sample

            This purposeful sample displays real rows selected to demonstrate high employment, high exposure, unmatched codes, special missing-value markers, negative outlook, and the high-but-valid Claude time value.
            """
        ),
        code(
            """
            difficult_sample = pd.read_csv(OUTPUT / "cleaned_sample_max_50.csv")
            difficult_sample[[
                "sample_type", "source_file", "source_row", "AREA_TITLE", "OCC_CODE",
                "OCC_TITLE", "TOT_EMP", "A_MEAN", "observed_exposure",
                "projected_employment_change_pct_2025_35", "original_value",
                "clean_value", "status", "selection_reason"
            ]]
            """
        ),
        markdown(
            """
            # 9. Final cleaned data sample

            The submission CSV contains the top-ranked complete-data occupation from each of the 28 California regions. The first ten rows below show the final column structure and values. All selected columns are displayed; Jupyter does not replace the middle columns with dots.
            """
        ),
        code(
            """
            final_sample = pd.read_csv(ROOT / "final_cleaned_sample.csv")
            print("Rows:", len(final_sample))
            print("Regions:", final_sample["AREA"].nunique())
            final_sample[[
                "AREA", "AREA_TITLE", "area_class", "OCC_CODE", "OCC_TITLE",
                "observed_exposure", "TOT_EMP", "A_MEAN",
                "projected_employment_change_pct_2025_35", "exposure_percentile",
                "employment_percentile", "lower_wage_need_percentile",
                "weaker_outlook_need_percentile", "screening_score",
                "screening_rank_within_region", "screening_status"
            ]].head(10)
            """
        ),
        markdown(
            """
            # Remaining limitations

            - The 32 malformed exposure occupation codes cannot be corrected without an authoritative source mapping, so they remain visible but join-ineligible.
            - AI exposure and employment projections are national occupation context, while OEWS employment and wages are California regional estimates.
            - Claude-use measures may describe global, country, or subregion activity and should not be interpreted as California causal effects.
            - Missing or censored OEWS estimates remain unknown; rows missing any score component do not receive a screening score.
            - Screening weights and the lower-wage and weaker-outlook proxies are planning judgments that require human review.

            # Conclusion

            The cleaned analysis preserves the published phenomena: source identifiers and units remain intact, special missing-value markers are not changed to zero, malformed codes are flagged rather than guessed, and the joins do not multiply rows or employment. The final score is a transparent screening aid for human workforce-planning review, not an automatic funding or automation decision.
            """
        ),
    ]

    notebook = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
    )
    return notebook


def display_data(value):
    """Return the plain-text and HTML forms stored by a Jupyter output."""
    data = {"text/plain": repr(value)}
    html_method = getattr(value, "_repr_html_", None)
    if callable(html_method):
        html = html_method()
        if html:
            data["text/html"] = html
    return data


def execute_cell(source, namespace, execution_count):
    """Execute one notebook cell and capture its printed and final values."""
    tree = ast.parse(source, mode="exec")
    final_expression = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        final_expression = ast.Expression(tree.body.pop().value)

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = None
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        if tree.body:
            exec(compile(tree, "<notebook-cell>", "exec"), namespace)
        if final_expression is not None:
            result = eval(compile(final_expression, "<notebook-cell>", "eval"), namespace)

    outputs = []
    if stdout.getvalue():
        outputs.append(
            nbformat.v4.new_output(
                output_type="stream", name="stdout", text=stdout.getvalue()
            )
        )
    if stderr.getvalue():
        outputs.append(
            nbformat.v4.new_output(
                output_type="stream", name="stderr", text=stderr.getvalue()
            )
        )
    if result is not None:
        outputs.append(
            nbformat.v4.new_output(
                output_type="execute_result",
                data=display_data(result),
                metadata={},
                execution_count=execution_count,
            )
        )
    return outputs


def main():
    notebook = build_notebook()
    print(f"Built notebook with {len(notebook.cells)} cells.", flush=True)
    print("Executing notebook cells...", flush=True)

    namespace = {"__name__": "__notebook__"}
    execution_count = 0
    for cell_number, cell in enumerate(notebook.cells, start=1):
        if cell.cell_type != "code":
            continue
        execution_count += 1
        cell.execution_count = execution_count
        try:
            cell.outputs = execute_cell(cell.source, namespace, execution_count)
        except Exception as error:
            cell.outputs = [
                nbformat.v4.new_output(
                    output_type="error",
                    ename=type(error).__name__,
                    evalue=str(error),
                    traceback=traceback.format_exc().splitlines(),
                )
            ]
            nbformat.write(notebook, NOTEBOOK_PATH)
            raise RuntimeError(
                f"Notebook execution failed in cell {cell_number}."
            ) from error

    nbformat.write(notebook, NOTEBOOK_PATH)
    print(f"Saved executed notebook: {NOTEBOOK_PATH}", flush=True)


if __name__ == "__main__":
    main()
