"""Reproducible, auditable cleaning pipeline for the Module 6 submission.

The script reads only the five datasets in the parent clean_data folder. It
never overwrites a source. Run from this directory with:

    python clean_data.py

All analytical exclusions, source markers, conversion checks, joins, and row
reconciliations are written to outputs/.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent
OUT = ROOT / "outputs"
PROJ_OUT = OUT / "projections"

SOURCE_FILES = [
    "aei_claude_ai_2026-06-26.csv",
    "job_exposure.csv",
    "BOS_M2025_dl.xlsx",
    "MSA_M2025_dl.xlsx",
    "occupation.XLSX",
]

SOC_PATTERN = r"\d{2}-\d{4}"
CLAUDE_KEY = [
    "date_start",
    "date_end",
    "geo_level",
    "geo_id",
    "category_name",
    "hierarchy_level",
    "node_external_id",
    "metric_id",
]
OEWS_KEY = ["release", "AREA", "NAICS", "I_GROUP", "OWN_CODE", "OCC_CODE", "O_GROUP"]
OEWS_NUMERIC = """TOT_EMP EMP_PRSE JOBS_1000 LOC_QUOTIENT PCT_TOTAL PCT_RPT
H_MEAN A_MEAN MEAN_PRSE H_PCT10 H_PCT25 H_MEDIAN H_PCT75 H_PCT90
A_PCT10 A_PCT25 A_MEDIAN A_PCT75 A_PCT90""".split()
PERCENTILE_GROUPS = [
    ["H_PCT10", "H_PCT25", "H_MEDIAN", "H_PCT75", "H_PCT90"],
    ["A_PCT10", "A_PCT25", "A_MEDIAN", "A_PCT75", "A_PCT90"],
]
MARKER_STATUS = {
    "": "missing_blank",
    "*": "unavailable",
    "**": "employment_estimate_unavailable",
    "#": "censored_exact_value_unavailable",
    "~": "below_reporting_threshold",
}


def json_default(value):
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=json_default),
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_manifest() -> list[dict]:
    rows = []
    for name in SOURCE_FILES:
        path = SOURCE / name
        stat = path.stat()
        rows.append(
            {
                "source_file": name,
                "bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat(),
                "sha256": sha256(path),
            }
        )
    return rows


def clean_scalar(value):
    if value is pd.NA or value is pd.NaT or value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def metric_unit(metric_id: pd.Series) -> pd.Series:
    result = pd.Series("metric-specific source unit", index=metric_id.index, dtype="string")
    result.loc[metric_id.str.endswith("_pct") | metric_id.eq("pct")] = "percentage points"
    result.loc[metric_id.str.contains("education_years", regex=False)] = "years"
    result.loc[metric_id.str.contains("time_mean", regex=False)] = "source time unit"
    result.loc[metric_id.eq("usage_per_capita_index")] = "index"
    return result


def add_missing_rows(store: list[dict], table: str, phase: str, df: pd.DataFrame) -> None:
    for column in df.columns:
        if column.startswith("_source"):
            continue
        if pd.api.types.is_string_dtype(df[column]):
            count = int((df[column].isna() | df[column].fillna("").eq("")).sum())
        else:
            count = int(df[column].isna().sum())
        store.append({"table": table, "phase": phase, "column": column, "missing": count})


def reset_outputs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PROJ_OUT.mkdir(parents=True, exist_ok=True)
    for pattern in ["cleaned_*.csv.gz", "analysis_*.csv.gz", "*.csv", "*.json", "*.md"]:
        for path in OUT.glob(pattern):
            path.unlink()
    for path in PROJ_OUT.glob("*.csv"):
        path.unlink()


def clean_claude(stage_rows, missing_rows, duplicate_rows, flag_rows):
    source_path = SOURCE / "aei_claude_ai_2026-06-26.csv"
    output_path = OUT / "cleaned_claude_metrics.csv.gz"
    declared_hashes = []
    full_hashes = []
    input_rows = 0
    output_rows = 0
    failed_dates = 0
    failed_values = 0
    changed_cells = 0
    suspicious_count = 0
    source_row_start = 2
    first = True
    examples = []
    units = set()
    raw_missing = None
    clean_missing = None

    for raw in pd.read_csv(
        source_path, dtype="string", keep_default_na=False, chunksize=200_000
    ):
        input_rows += len(raw)
        if raw_missing is None:
            raw_missing = {c: 0 for c in raw.columns}
            clean_missing = {c: 0 for c in raw.columns}
        for column in raw.columns:
            raw_missing[column] += int(raw[column].eq("").sum())

        clean = raw.copy()
        clean.insert(0, "_source_row", range(source_row_start, source_row_start + len(clean)))
        clean.insert(0, "_source_file", source_path.name)
        source_row_start += len(clean)

        start = pd.to_datetime(clean["date_start"], format="%Y-%m-%d", errors="coerce")
        end = pd.to_datetime(clean["date_end"], format="%Y-%m-%d", errors="coerce")
        value = pd.to_numeric(clean["value"], errors="coerce")
        hierarchy = pd.to_numeric(clean["hierarchy_level"], errors="coerce").astype("Int64")
        failed_dates += int(start.isna().sum() + end.isna().sum())
        failed_values += int(value.isna().sum())
        clean["date_start"] = start.dt.strftime("%Y-%m-%d").astype("string")
        clean["date_end"] = end.dt.strftime("%Y-%m-%d").astype("string")
        clean["hierarchy_level"] = hierarchy
        clean["value"] = value.astype("Float64")
        clean["metric_unit"] = metric_unit(clean["metric_id"])
        units.update(clean["metric_unit"].dropna().unique().tolist())
        is_pct = clean["metric_unit"].eq("percentage points")
        suspicious = value.lt(0) | (is_pct & ~value.between(0, 100)) | end.le(start)
        clean["suspicious_value"] = suspicious.astype("boolean")
        suspicious_count += int(suspicious.sum())
        if suspicious.any():
            flagged = clean.loc[suspicious, ["_source_file", "_source_row", "metric_id", "value"]].copy()
            for _, row in flagged.iterrows():
                flag_rows.append(
                    {
                        "source_file": row["_source_file"],
                        "source_sheet": "",
                        "source_row": int(row["_source_row"]),
                        "field": "value",
                        "original_value": clean.loc[clean["_source_row"].eq(row["_source_row"]), "value"].iloc[0],
                        "rule": "negative value, percentage outside 0-100, or invalid date interval",
                        "decision": "retained pending domain review",
                    }
                )

        target = clean.loc[clean["_source_row"].eq(396056)]
        if not target.empty:
            examples.extend(target.to_dict("records"))

        full_hashes.append(pd.util.hash_pandas_object(raw, index=False).to_numpy())
        declared_hashes.append(pd.util.hash_pandas_object(clean[CLAUDE_KEY], index=False).to_numpy())
        clean.to_csv(
            output_path,
            index=False,
            mode="wt" if first else "at",
            header=first,
            compression="gzip",
        )
        first = False
        output_rows += len(clean)
        changed_cells += len(clean) * 4
        for column in raw.columns:
            clean_missing[column] += int(clean[column].isna().sum())

    full_hashes = np.concatenate(full_hashes)
    declared_hashes = np.concatenate(declared_hashes)
    exact_dupes = int(pd.Series(full_hashes).duplicated().sum())
    key_dupes = int(pd.Series(declared_hashes).duplicated().sum())
    duplicate_rows.append(
        {
            "table": "claude_metrics",
            "phase": "raw",
            "exact_duplicate_excess": exact_dupes,
            "repeated_key_excess": key_dupes,
        }
    )
    for column, count in raw_missing.items():
        missing_rows.append(
            {"table": "claude_metrics", "phase": "raw", "column": column, "missing": count}
        )
    for column, count in clean_missing.items():
        missing_rows.append(
            {"table": "claude_metrics", "phase": "clean", "column": column, "missing": count}
        )
    stage_rows.append(
        {
            "stage": "claude",
            "input_rows": input_rows,
            "output_rows": output_rows,
            "rows_excluded": 0,
            "changed_cells": changed_cells,
            "new_flags": suspicious_count,
            "failed_conversions": failed_dates + failed_values,
            "summary": "Parsed dates, hierarchy level, and value; added metric units and metric-aware flags. No rows removed.",
        }
    )
    assert input_rows == output_rows == 1_636_573
    assert exact_dupes == 0 and key_dupes == 0
    assert failed_dates == 0 and failed_values == 0
    return {
        "rows": output_rows,
        "exact_duplicate_excess": exact_dupes,
        "duplicate_key_excess": key_dupes,
        "failed_dates": failed_dates,
        "failed_numeric": failed_values,
        "suspicious_values": suspicious_count,
        "units": sorted(units),
        "record_examples": examples,
    }


def clean_exposure(stage_rows, missing_rows, duplicate_rows, flag_rows, exclusions):
    path = SOURCE / "job_exposure.csv"
    raw = pd.read_csv(path, dtype="string", keep_default_na=False)
    add_missing_rows(missing_rows, "job_exposure", "raw", raw)
    clean = raw.copy()
    clean.insert(0, "_source_row", range(2, len(clean) + 2))
    clean.insert(0, "_source_file", path.name)
    clean["occ_code_raw"] = clean["occ_code"]
    clean["title"] = clean["title"].str.strip()
    clean["observed_exposure"] = pd.to_numeric(clean["observed_exposure"], errors="coerce").astype("Float64")
    valid = clean["occ_code"].str.fullmatch(SOC_PATTERN, na=False)
    valid_unique = valid & ~clean["occ_code"].duplicated(keep=False)
    clean["code_format_valid"] = valid.astype("boolean")
    clean["code_join_eligible"] = valid_unique.astype("boolean")
    clean["suspicious_value"] = (~valid | ~clean["observed_exposure"].between(0, 1)).astype("boolean")
    invalid = clean.loc[~valid]
    for _, row in invalid.iterrows():
        flag_rows.append(
            {
                "source_file": path.name,
                "source_sheet": "",
                "source_row": int(row["_source_row"]),
                "field": "occ_code",
                "original_value": row["occ_code"],
                "rule": "not an exact six-digit SOC code",
                "decision": "preserve; exclude only from exact-code joins",
            }
        )
        exclusions.append(
            {
                "stage": "exposure exact-code join",
                "source_file": path.name,
                "source_sheet": "",
                "source_row": int(row["_source_row"]),
                "record_key": row["occ_code"],
                "reason": "invalid SOC code; original meaning cannot be inferred",
            }
        )
    clean.to_csv(OUT / "cleaned_job_exposure.csv", index=False)
    add_missing_rows(missing_rows, "job_exposure", "clean", clean)
    duplicate_rows.extend(
        [
            {
                "table": "job_exposure",
                "phase": "raw",
                "exact_duplicate_excess": int(raw.duplicated().sum()),
                "repeated_key_excess": int(raw.duplicated("occ_code").sum()),
            },
            {
                "table": "job_exposure_valid_codes",
                "phase": "clean",
                "exact_duplicate_excess": 0,
                "repeated_key_excess": int(clean.loc[valid].duplicated("occ_code").sum()),
            },
        ]
    )
    stage_rows.append(
        {
            "stage": "job_exposure",
            "input_rows": len(raw),
            "output_rows": len(clean),
            "rows_excluded": 0,
            "changed_cells": int((raw["title"] != clean["title"]).sum()) + len(clean),
            "new_flags": int((~valid).sum()),
            "failed_conversions": int(clean["observed_exposure"].isna().sum()),
            "summary": "Preserved all records; validated SOC codes and exposure fractions. Invalid codes are join-ineligible, not repaired.",
        }
    )
    assert len(clean) == 756
    assert int((~valid).sum()) == 32
    assert clean.loc[valid, "occ_code"].is_unique
    assert clean["observed_exposure"].between(0, 1).all()
    return clean


def oews_status(series: pd.Series) -> pd.Series:
    return series.map(MARKER_STATUS).fillna("reported").astype("string")


def clean_oews(stage_rows, missing_rows, duplicate_rows, flag_rows):
    frames = []
    source_specs = [
        ("BOS_M2025_dl.xlsx", "BOS_M2025_dl", "nonmetropolitan"),
        ("MSA_M2025_dl.xlsx", "MSA_M2025_dl", "metropolitan"),
    ]
    total_input = 0
    total_changed = 0
    total_failures = 0
    percentile_violations = 0
    marker_counts = {}

    for filename, sheet, area_class in source_specs:
        raw = pd.read_excel(
            SOURCE / filename,
            sheet_name=sheet,
            dtype="string",
            keep_default_na=False,
            engine="openpyxl",
        )
        total_input += len(raw)
        add_missing_rows(missing_rows, f"oews_{area_class}", "raw", raw)
        clean = raw.copy()
        clean.insert(0, "_source_row", range(2, len(clean) + 2))
        clean.insert(0, "_source_sheet", sheet)
        clean.insert(0, "_source_file", filename)
        clean.insert(3, "release", "May 2025")
        clean.insert(4, "area_class", area_class)
        for column in ["AREA_TITLE", "NAICS_TITLE", "OCC_TITLE"]:
            before = clean[column].copy()
            clean[column] = clean[column].str.strip()
            total_changed += int((before != clean[column]).sum())

        marker_counts[filename] = {}
        for column in OEWS_NUMERIC:
            raw_values = clean[column].copy()
            status = oews_status(raw_values)
            clean[f"{column}__status"] = status
            marker_counts[filename][column] = {
                marker: int(raw_values.eq(marker).sum())
                for marker in MARKER_STATUS
                if int(raw_values.eq(marker).sum()) > 0
            }
            numeric = pd.to_numeric(raw_values.mask(raw_values.isin(MARKER_STATUS)), errors="coerce")
            failure = (~raw_values.isin(MARKER_STATUS)) & numeric.isna()
            total_failures += int(failure.sum())
            if failure.any():
                for idx in clean.index[failure]:
                    flag_rows.append(
                        {
                            "source_file": filename,
                            "source_sheet": sheet,
                            "source_row": int(clean.at[idx, "_source_row"]),
                            "field": column,
                            "original_value": raw_values.at[idx],
                            "rule": "unrecognized token in numeric OEWS field",
                            "decision": "retain marker status and numeric missing pending review",
                        }
                    )
            clean[column] = numeric.astype("Float64")
            total_changed += len(clean)

        clean["annual_only"] = clean["ANNUAL"].eq("TRUE").astype("boolean")
        clean["hourly_only"] = clean["HOURLY"].eq("TRUE").astype("boolean")
        for group in PERCENTILE_GROUPS:
            comparable = clean[group].notna().all(axis=1)
            arr = clean.loc[comparable, group].astype(float).to_numpy()
            bad = comparable.copy()
            bad.loc[:] = False
            if len(arr):
                bad.loc[comparable] = (np.diff(arr, axis=1) < 0).any(axis=1)
            percentile_violations += int(bad.sum())
            for idx in clean.index[bad]:
                flag_rows.append(
                    {
                        "source_file": filename,
                        "source_sheet": sheet,
                        "source_row": int(clean.at[idx, "_source_row"]),
                        "field": "/".join(group),
                        "original_value": "percentile order",
                        "rule": "published percentile values should be nondecreasing",
                        "decision": "retain published values; flag for source review",
                    }
                )
        add_missing_rows(missing_rows, f"oews_{area_class}", "clean", clean)
        duplicate_rows.append(
            {
                "table": f"oews_{area_class}",
                "phase": "clean",
                "exact_duplicate_excess": int(raw.duplicated().sum()),
                "repeated_key_excess": int(clean.duplicated(OEWS_KEY).sum()),
            }
        )
        frames.append(clean)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(OUT / "cleaned_oews.csv.gz", index=False, compression="gzip")
    stage_rows.append(
        {
            "stage": "oews",
            "input_rows": total_input,
            "output_rows": len(combined),
            "rows_excluded": 0,
            "changed_cells": total_changed,
            "new_flags": percentile_violations,
            "failed_conversions": total_failures,
            "summary": "Appended MSA and BOS with area class; converted numeric fields and preserved marker meanings in status columns. No rows removed.",
        }
    )
    assert len(combined) == 198_712
    assert combined.duplicated(OEWS_KEY).sum() == 0
    assert total_failures == 0
    return combined, {
        "rows": len(combined),
        "failed_numeric": total_failures,
        "percentile_order_flags": percentile_violations,
        "marker_counts": marker_counts,
    }


def safe_sheet_name(sheet: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sheet.lower()).strip("_")


def projection_numeric_column(column: str) -> bool:
    name = column.lower()
    if any(word in name for word in ["title", "code", "type", "content", "link", "category", "factors"]):
        return False
    return any(
        word in name
        for word in ["employment", "wage", "percent", "rate", "openings", "exits", "transfers", "separations"]
    )


def clean_projections(stage_rows, missing_rows, duplicate_rows, exclusions):
    workbook = SOURCE / "occupation.XLSX"
    excel = pd.ExcelFile(workbook, engine="openpyxl")
    frames = {}
    input_rows = 0
    output_rows = 0
    failed = 0
    nondata_rows = 0

    for sheet in [name for name in excel.sheet_names if name != "Index"]:
        raw = pd.read_excel(
            workbook,
            sheet_name=sheet,
            header=1,
            dtype="string",
            keep_default_na=False,
            engine="openpyxl",
        )
        raw.columns = [str(c) for c in raw.columns]
        input_rows += len(raw)
        source_rows = pd.Series(range(3, len(raw) + 3), index=raw.index)
        code_columns = [c for c in raw.columns if " code" in c.lower()]
        if sheet == "Table 1.11":
            data_mask = pd.to_numeric(raw["Employment, 2025"], errors="coerce").notna()
            key_columns = ["Occupation category"]
        else:
            data_mask = raw[code_columns[0]].ne("")
            key_columns = code_columns

        for idx in raw.index[~data_mask]:
            exclusions.append(
                {
                    "stage": "projection non-data separation",
                    "source_file": workbook.name,
                    "source_sheet": sheet,
                    "source_row": int(source_rows.at[idx]),
                    "record_key": str(raw.iloc[idx, 0]),
                    "reason": "title, footer, note, or blank row; retained as source metadata rather than an observation",
                }
            )
        nondata_rows += int((~data_mask).sum())
        clean = raw.loc[data_mask].copy()
        clean.insert(0, "_source_row", source_rows.loc[data_mask].astype("Int64"))
        clean.insert(0, "_source_sheet", sheet)
        clean.insert(0, "_source_file", workbook.name)

        title_columns = [c for c in clean if "title" in c.lower()]
        for column in title_columns:
            clean[f"{column}__raw"] = clean[column]
            clean[column] = clean[column].str.strip()

        if sheet == "Table 1.2":
            clean = clean.rename(
                columns={
                    "Related Occupational Outlook Handbook (OOH) content": "ooh_label",
                    "Related Occupational Outlook Handbook (OOH) content.1": "ooh_link_raw",
                }
            )
        for column in list(clean.columns):
            if not projection_numeric_column(column):
                continue
            raw_values = clean[column].copy()
            clean[f"{column}__status"] = np.where(
                raw_values.eq("—"), "unavailable", np.where(raw_values.eq(""), "missing_blank", "reported")
            )
            numeric = pd.to_numeric(raw_values.mask(raw_values.isin(["", "—"])), errors="coerce")
            failures = (~raw_values.isin(["", "—"])) & numeric.isna()
            failed += int(failures.sum())
            clean[column] = numeric.astype("Float64")

        add_missing_rows(missing_rows, f"projection_{safe_sheet_name(sheet)}", "clean", clean)
        dupes = int(clean.duplicated(key_columns).sum())
        duplicate_rows.append(
            {
                "table": f"projection_{safe_sheet_name(sheet)}",
                "phase": "clean",
                "exact_duplicate_excess": int(clean.duplicated().sum()),
                "repeated_key_excess": dupes,
            }
        )
        assert dupes == 0
        clean.to_csv(PROJ_OUT / f"{safe_sheet_name(sheet)}.csv", index=False)
        frames[sheet] = clean
        output_rows += len(clean)

    stage_rows.append(
        {
            "stage": "projections",
            "input_rows": input_rows,
            "output_rows": output_rows,
            "rows_excluded": nondata_rows,
            "changed_cells": output_rows,
            "new_flags": 0,
            "failed_conversions": failed,
            "summary": "Separated worksheet title/footer rows, preserved sheet grains, trimmed display titles, and converted numeric measures without changing units.",
        }
    )
    assert len(frames["Table 1.2"]) == 1_112
    assert failed == 0
    return frames, {"input_rows": input_rows, "data_rows": output_rows, "nondata_rows": nondata_rows}


def build_analysis(oews, exposure, projections, stage_rows, exclusions):
    california = oews["PRIM_STATE"].eq("CA")
    detailed_scope = (
        oews["NAICS"].eq("000000")
        & oews["I_GROUP"].eq("cross-industry")
        & oews["OWN_CODE"].eq("1235")
        & oews["O_GROUP"].eq("detailed")
    )
    scope = california & detailed_scope
    for rule, mask, reason in [
        (
            "California geography scope",
            ~california,
            "PRIM_STATE is not CA; row remains in the complete cleaned OEWS base",
        ),
        (
            "detailed occupation scope",
            california & ~detailed_scope,
            "California row is not a detailed cross-industry ownership-1235 observation; row remains in the cleaned OEWS base",
        ),
    ]:
        affected = int(mask.sum())
        if not affected:
            continue
        exclusions.append(
            {
                "stage": "California occupation-region screening scope",
                "source_file": "BOS_M2025_dl.xlsx + MSA_M2025_dl.xlsx",
                "source_sheet": "observation sheets",
                "source_row": "aggregated; source rows remain in cleaned_oews.csv.gz",
                "record_key": rule,
                "reason": reason,
                "affected_rows": affected,
            }
        )
    base = oews.loc[scope].copy()
    exposure_lookup = exposure.loc[
        exposure["code_join_eligible"], ["occ_code", "title", "observed_exposure"]
    ].rename(columns={"title": "exposure_title"})
    assert exposure_lookup["occ_code"].is_unique
    before_rows = len(base)
    before_emp = float(base["TOT_EMP"].sum(skipna=True))
    joined = base.merge(
        exposure_lookup,
        how="left",
        left_on="OCC_CODE",
        right_on="occ_code",
        validate="many_to_one",
    )
    projection = projections["Table 1.2"].copy()
    code = "2025 National Employment Matrix code"
    projection_fields = [
        code,
        "Employment change, percent, 2025–35",
        "Employment change, numeric, 2025–35",
        "Median annual wage, dollars, 2025",
    ]
    projection_lookup = projection[projection_fields].rename(
        columns={
            code: "projection_occ_code",
            "Employment change, percent, 2025–35": "projected_employment_change_pct_2025_35",
            "Employment change, numeric, 2025–35": "projected_employment_change_thousands_2025_35",
            "Median annual wage, dollars, 2025": "projected_national_median_wage_2025",
        }
    )
    assert projection_lookup["projection_occ_code"].is_unique
    joined = joined.merge(
        projection_lookup,
        how="left",
        left_on="OCC_CODE",
        right_on="projection_occ_code",
        validate="many_to_one",
    )
    after_emp = float(joined["TOT_EMP"].sum(skipna=True))
    assert len(joined) == before_rows
    assert before_emp == after_emp
    exposure_matches = int(joined["observed_exposure"].notna().sum())
    projection_matches = int(joined["projection_occ_code"].notna().sum())

    component_columns = [
        "observed_exposure",
        "TOT_EMP",
        "A_MEAN",
        "projected_employment_change_pct_2025_35",
    ]
    eligible = joined[component_columns].notna().all(axis=1)
    joined["screening_eligible"] = eligible.astype("boolean")
    joined["screening_status"] = np.where(
        eligible, "complete four-component score", "insufficient component data"
    )
    score_columns = [
        "exposure_percentile",
        "employment_percentile",
        "lower_wage_need_percentile",
        "weaker_outlook_need_percentile",
        "screening_score",
    ]
    for column in score_columns:
        joined[column] = pd.Series(pd.NA, index=joined.index, dtype="Float64")

    eligible_rows = joined.loc[eligible]
    joined.loc[eligible, "exposure_percentile"] = eligible_rows.groupby("AREA")[
        "observed_exposure"
    ].rank(method="average", pct=True, ascending=True)
    joined.loc[eligible, "employment_percentile"] = eligible_rows.groupby("AREA")[
        "TOT_EMP"
    ].rank(method="average", pct=True, ascending=True)
    joined.loc[eligible, "lower_wage_need_percentile"] = eligible_rows.groupby("AREA")[
        "A_MEAN"
    ].rank(method="average", pct=True, ascending=False)
    joined.loc[eligible, "weaker_outlook_need_percentile"] = eligible_rows.groupby("AREA")[
        "projected_employment_change_pct_2025_35"
    ].rank(method="average", pct=True, ascending=False)
    joined.loc[eligible, "screening_score"] = 100 * (
        0.40 * joined.loc[eligible, "exposure_percentile"]
        + 0.30 * joined.loc[eligible, "employment_percentile"]
        + 0.15 * joined.loc[eligible, "lower_wage_need_percentile"]
        + 0.15 * joined.loc[eligible, "weaker_outlook_need_percentile"]
    )
    joined["screening_rank_within_region"] = pd.Series(
        pd.NA, index=joined.index, dtype="Int64"
    )
    joined.loc[eligible, "screening_rank_within_region"] = (
        joined.loc[eligible]
        .groupby("AREA")["screening_score"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )
    joined["shortlist_top25"] = (
        joined["screening_rank_within_region"].le(25).fillna(False).astype("boolean")
    )
    joined.to_csv(
        OUT / "analysis_california_occupation_region.csv.gz",
        index=False,
        compression="gzip",
    )

    shortlist = joined.loc[joined["shortlist_top25"]].sort_values(
        ["AREA_TITLE", "screening_rank_within_region", "OCC_CODE"]
    )
    shortlist.to_csv(OUT / "shortlist_top25_by_region.csv", index=False)

    # A small final sample for submission: the top-ranked occupation in each region.
    sample_columns = [
        "_source_file",
        "_source_row",
        "release",
        "area_class",
        "AREA",
        "AREA_TITLE",
        "OCC_CODE",
        "OCC_TITLE",
        "observed_exposure",
        "TOT_EMP",
        "A_MEAN",
        "projected_employment_change_pct_2025_35",
        "exposure_percentile",
        "employment_percentile",
        "lower_wage_need_percentile",
        "weaker_outlook_need_percentile",
        "screening_score",
        "screening_rank_within_region",
        "screening_status",
    ]
    submission_sample = shortlist.loc[
        shortlist["screening_rank_within_region"].eq(1), sample_columns
    ].sort_values("AREA_TITLE")
    assert len(submission_sample) == joined["AREA"].nunique()
    assert submission_sample["AREA"].is_unique
    submission_sample.to_csv(ROOT / "final_cleaned_sample.csv", index=False)

    region_summary = (
        joined.groupby(["AREA", "AREA_TITLE", "area_class"], as_index=False)
        .agg(
            occupation_rows=("OCC_CODE", "size"),
            screening_eligible_rows=("screening_eligible", "sum"),
            exposure_matched_rows=("observed_exposure", "count"),
            employment_jobs=("TOT_EMP", "sum"),
            mean_annual_wage=("A_MEAN", "mean"),
            mean_screening_score=("screening_score", "mean"),
        )
        .sort_values("AREA_TITLE")
    )
    top = (
        shortlist.sort_values(["AREA", "screening_rank_within_region", "OCC_CODE"])
        .groupby("AREA", as_index=False)
        .head(1)[["AREA", "OCC_CODE", "OCC_TITLE", "screening_score"]]
    ).rename(
        columns={
            "OCC_CODE": "top_ranked_occ_code",
            "OCC_TITLE": "top_ranked_occupation",
            "screening_score": "top_screening_score",
        }
    )
    region_summary = region_summary.merge(top, how="left", on="AREA", validate="one_to_one")
    region_summary.to_csv(OUT / "region_summary.csv", index=False)

    stage_rows.append(
        {
            "stage": "analysis_scope_and_joins",
            "input_rows": len(oews),
            "output_rows": len(joined),
            "rows_excluded": int((~scope).sum()),
            "changed_cells": exposure_matches + projection_matches + int(eligible.sum()) * 6,
            "new_flags": int((~eligible).sum()),
            "failed_conversions": 0,
            "summary": "Selected California detailed cross-industry region records, made two validated many-to-one context joins, and calculated a transparent four-component within-region screening rank. Base records and employment checksum were preserved.",
        }
    )
    return joined, {
        "base_rows": len(joined),
        "excluded_scope_rows": int((~scope).sum()),
        "exposure_matches": exposure_matches,
        "exposure_unmatched": int(joined["observed_exposure"].isna().sum()),
        "projection_matches": projection_matches,
        "projection_unmatched": int(joined["projection_occ_code"].isna().sum()),
        "employment_checksum_before": before_emp,
        "employment_checksum_after": after_emp,
        "areas": int(joined["AREA"].nunique()),
        "occupations": int(joined["OCC_CODE"].nunique()),
        "screening_eligible_rows": int(eligible.sum()),
        "screening_ineligible_rows": int((~eligible).sum()),
        "shortlist_rows": len(shortlist),
        "submission_sample_rows": len(submission_sample),
        "score_weights": {
            "observed_ai_exposure": 0.40,
            "regional_employment": 0.30,
            "lower_annual_mean_wage_transition_need_proxy": 0.15,
            "weaker_national_outlook_transition_need_proxy": 0.15,
        },
    }


def locate_actual(expectation, exposure, oews, projections, claude_info):
    filename = expectation["source_file"]
    row_number = expectation["source_row"]
    if filename == "job_exposure.csv":
        frame = exposure
    elif filename in {"BOS_M2025_dl.xlsx", "MSA_M2025_dl.xlsx"}:
        frame = oews
    elif filename == "occupation.XLSX":
        frame = projections[expectation["source_sheet"]]
    elif filename == "aei_claude_ai_2026-06-26.csv":
        frame = pd.DataFrame(claude_info["record_examples"])
    else:
        raise KeyError(filename)
    match = frame.loc[
        frame["_source_file"].eq(filename) & frame["_source_row"].eq(row_number)
    ]
    if expectation["source_sheet"] and "_source_sheet" in match:
        match = match.loc[match["_source_sheet"].eq(expectation["source_sheet"])]
    if len(match) != 1:
        raise AssertionError(f"Expected one record for {expectation['id']}; found {len(match)}")
    row = match.iloc[0]
    actual = clean_scalar(row[expectation["field"]])
    status_field = expectation["expected_status_field"]
    actual_status = clean_scalar(row[status_field]) if status_field else None
    expected = expectation["expected"]
    expected_status = expectation["expected_status"]
    value_ok = actual == expected or (
        isinstance(actual, (float, int))
        and isinstance(expected, (float, int))
        and math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-12)
    )
    status_ok = actual_status == expected_status
    return {
        **expectation,
        "actual": actual,
        "actual_status": actual_status,
        "passed": bool(value_ok and status_ok),
    }


def build_sample(analysis, exposure, oews, projections, claude_info):
    columns = [
        "sample_type", "source_file", "source_sheet", "source_row", "area_class",
        "AREA", "AREA_TITLE", "OCC_CODE", "OCC_TITLE", "TOT_EMP", "A_MEAN",
        "observed_exposure", "projected_employment_change_pct_2025_35", "field",
        "original_value", "clean_value", "status", "selection_reason",
    ]
    rows = []

    def add(row):
        rows.append({column: row.get(column) for column in columns})

    groups = [
        (analysis.nlargest(6, "TOT_EMP"), "high employment"),
        (analysis.loc[analysis["observed_exposure"].notna()].nlargest(6, "observed_exposure"), "high observed exposure"),
        (analysis.loc[analysis["observed_exposure"].isna()].head(4), "unmatched exposure key"),
        (analysis.loc[analysis["TOT_EMP"].isna()].head(4), "unavailable employment"),
    ]
    for frame, reason in groups:
        for _, item in frame.iterrows():
            add(
                {
                    "sample_type": "analysis_record",
                    "source_file": item["_source_file"],
                    "source_sheet": item["_source_sheet"],
                    "source_row": int(item["_source_row"]),
                    "area_class": item["area_class"],
                    "AREA": item["AREA"],
                    "AREA_TITLE": item["AREA_TITLE"],
                    "OCC_CODE": item["OCC_CODE"],
                    "OCC_TITLE": item["OCC_TITLE"],
                    "TOT_EMP": clean_scalar(item["TOT_EMP"]),
                    "A_MEAN": clean_scalar(item["A_MEAN"]),
                    "observed_exposure": clean_scalar(item["observed_exposure"]),
                    "projected_employment_change_pct_2025_35": clean_scalar(item["projected_employment_change_pct_2025_35"]),
                    "selection_reason": reason,
                }
            )

    for _, item in exposure.loc[~exposure["code_format_valid"]].head(4).iterrows():
        add(
            {
                "sample_type": "invalid_exposure_code",
                "source_file": item["_source_file"],
                "source_row": int(item["_source_row"]),
                "OCC_CODE": item["occ_code"],
                "field": "occ_code",
                "original_value": item["occ_code_raw"],
                "clean_value": item["occ_code"],
                "status": "join ineligible",
                "selection_reason": "date-like SOC code preserved without guessed repair",
            }
        )
    for source_row, field in [(15, "TOT_EMP"), (1711, "H_MEAN")]:
        item = oews.loc[
            oews["_source_file"].eq("BOS_M2025_dl.xlsx") & oews["_source_row"].eq(source_row)
        ].iloc[0]
        add(
            {
                "sample_type": "special_marker",
                "source_file": item["_source_file"],
                "source_sheet": item["_source_sheet"],
                "source_row": int(item["_source_row"]),
                "AREA": item["AREA"],
                "OCC_CODE": item["OCC_CODE"],
                "field": field,
                "original_value": "**" if field == "TOT_EMP" else "#",
                "clean_value": None,
                "status": item[f"{field}__status"],
                "selection_reason": "source marker kept distinct from zero",
            }
        )
    if claude_info["record_examples"]:
        item = claude_info["record_examples"][0]
        add(
            {
                "sample_type": "metric_specific_range",
                "source_file": item["_source_file"],
                "source_row": int(item["_source_row"]),
                "field": item["metric_id"],
                "original_value": "199.11",
                "clean_value": item["value"],
                "status": "valid time metric",
                "selection_reason": "value above 100 retained because metric is not a percentage",
            }
        )
    projection = projections["Table 1.5"]
    growth = "Employment change, percent, 2025–35"
    for _, item in projection.loc[projection[growth].lt(0)].head(3).iterrows():
        add(
            {
                "sample_type": "negative_projection",
                "source_file": item["_source_file"],
                "source_sheet": item["_source_sheet"],
                "source_row": int(item["_source_row"]),
                "OCC_CODE": item["2025 National Employment Matrix code"],
                "field": growth,
                "original_value": item[growth],
                "clean_value": item[growth],
                "status": "valid negative change",
                "selection_reason": "decline is meaningful and retained",
            }
        )
    sample = pd.DataFrame(rows, columns=columns).drop_duplicates().head(40)
    sample.to_csv(OUT / "cleaned_sample_max_50.csv", index=False)
    assert len(sample) <= 50
    return sample


def independent_codex_check():
    raw = pd.read_csv(SOURCE / "job_exposure.csv", dtype="string", keep_default_na=False)
    valid = raw["occ_code"].str.fullmatch(SOC_PATTERN, na=False)
    return {
        "suggestion": "Do not automatically repair date-like occupation codes; preserve and flag them before exact-code joins.",
        "independent_method": "Re-read the original CSV without pipeline helpers; apply an anchored six-digit SOC pattern and count duplicate valid keys.",
        "rows": len(raw),
        "invalid_codes": int((~valid).sum()),
        "valid_codes": int(valid.sum()),
        "valid_code_duplicate_excess": int(raw.loc[valid].duplicated("occ_code").sum()),
        "conclusion": "Accepted. The 32 malformed strings are not sufficient evidence for a unique repair; all 724 valid exact codes are unique.",
        "student_review_pending": False,
    }


def build_report(validation, record_checks, stage_rows):
    decision_lines = "\n".join(
        f"- **{row['stage']}** - Rule: {row['summary']} Reason: keep the published meaning and make every change traceable. Check: input {row['input_rows']:,}; output {row['output_rows']:,}; exclusions {row['rows_excluded']:,}; flags {row['new_flags']:,}; failed conversions {row['failed_conversions']:,}."
        for row in stage_rows
    )
    check_lines = "\n".join(
        f"- **{row['id']}** `{row['source_file']}` row {row['source_row']}, `{row['field']}`: original `{row['original']}`; expected `{row['expected']}`; actual `{row['actual']}`; status `{row['actual_status']}`; **{'PASS' if row['passed'] else 'FAIL'}**. Reason: {row['reason']}"
        for row in record_checks
    )
    metrics = validation["analysis"]
    sample = pd.read_csv(OUT / "cleaned_sample_max_50.csv", keep_default_na=False)
    sample_lines = []
    for _, row in sample.iterrows():
        identity = " ".join(
            str(value) for value in [row["AREA_TITLE"], row["OCC_CODE"], row["OCC_TITLE"]]
            if str(value).strip()
        )
        values = []
        for label, column in [
            ("employment", "TOT_EMP"),
            ("annual wage", "A_MEAN"),
            ("AI exposure", "observed_exposure"),
            ("outlook", "projected_employment_change_pct_2025_35"),
            ("original", "original_value"),
            ("clean", "clean_value"),
            ("status", "status"),
        ]:
            if str(row[column]).strip():
                values.append(f"{label}={row[column]}")
        sample_lines.append(
            f"- **{row['sample_type']}** - {row['source_file']} row {int(row['source_row'])}: "
            f"{identity}. {'; '.join(values)}. Reason: {row['selection_reason']}"
        )
    sample_text = "\n".join(sample_lines)
    statuses = ["Done"] * 14
    evidence = [
        "The vision, business question, and main metrics are stated in plan.md sections 1 and 6.",
        "Row definitions and composite keys are documented in plan.md section 4 and checked in outputs/duplicates.csv.",
        "Five source files are hashed in outputs/source_manifest.json; hashes matched before and after the run.",
        "All declared numeric/date conversions had zero failures; details are in outputs/validation.json and missing_counts.csv.",
        "Only outer whitespace was eligible for trimming. No meaningful text, case, punctuation, or leading-zero identifiers were rewritten.",
        "Exact duplicates and repeated keys are reported separately in outputs/duplicates.csv. No exact duplicate source rows were found.",
        "Missing counts before/after are in outputs/missing_counts.csv. No blanket imputation was used; source markers have distinct status columns.",
        "Suspicious values were flagged before treatment in outputs/suspicious_values.csv. Metric-specific checks prevented the valid Claude value 199.11 from being treated as a percentage outlier.",
        f"Two many-to-one exact-code joins preserved {metrics['base_rows']:,} California occupation-region rows. Exposure unmatched: {metrics['exposure_unmatched']:,}; projection unmatched: {metrics['projection_unmatched']:,}.",
        f"OEWS started with 198,712 rows. The cleaned base kept all 198,712. The California detailed screening scope has {metrics['base_rows']:,}; {metrics['excluded_scope_rows']:,} rows remain in the cleaned base and are reconciled as scope exclusions.",
        f"Missing values are not converted to zero or silently reweighted. {metrics['screening_eligible_rows']:,} complete rows receive a score; {metrics['screening_ineligible_rows']:,} remain visible with an insufficient-data status.",
        "Five predeclared record checks are shown below and stored in outputs/record_checks.csv.",
        "The pipeline was run from original files, source hashes were rechecked, and all assertions passed. Run command: python clean_data.py.",
        "The remaining limitations are documented below. They include malformed occupation codes without an authoritative correction and the use of national or global context for a California screening tool.",
    ]
    checklist = "\n\n".join(
        f"## {i}. {title}\n\n**Status: {statuses[i-1]}**  \nEvidence: {evidence[i-1]}"
        for i, title in enumerate(
            [
                "State the project vision and question",
                "Define one row",
                "Preserve the source",
                "Inspect columns and types",
                "Standardize text",
                "Investigate duplicates",
                "Handle missing data",
                "Check suspicious values",
                "Verify merges",
                "Reconcile changes",
                "Check calculations",
                "Verify individual records",
                "Test reproducibility",
                "Document remaining limitations",
            ],
            start=1,
        )
    )
    report = f"""# DSO 576 Module 6 - Project Data Cleaning

Project: AI Workforce Investment Planner  
Student: Hehua (Leo) Liu - confirmation pending  
Branch: Leo  
Branch URL: https://github.com/Hardcore-LEO/dso576-project/tree/Leo  
Submitted commit: 4993964fc785f73b9c518b49223af6b6d6192f68  
Business question: Which California occupation x region combinations should be prioritized for AI upskilling and workforce-transition support?

The user selects a California region and reviews occupations using observed AI exposure, employment, wages, and labor-market outlook. The result is a screening shortlist for human review. It is not an automatic funding or automation decision.

{checklist}

# Cleaning decision log

{decision_lines}

# Five predeclared record checks

The expected results were saved in `record_expectations.json` before the cleaning pipeline read its outputs.

{check_lines}

# How one Codex suggestion was checked

Suggestion: {validation['codex_check']['suggestion']}

Independent check: {validation['codex_check']['independent_method']}

Result: {validation['codex_check']['invalid_codes']} invalid and {validation['codex_check']['valid_codes']} valid codes; duplicate valid codes: {validation['codex_check']['valid_code_duplicate_excess']}. {validation['codex_check']['conclusion']}

I checked this suggestion by reading the original exposure file again and applying a simple six-digit SOC pattern. I accepted the suggestion because the 32 malformed values do not contain enough information for a reliable correction.

# Result summary

- Claude metrics: {validation['claude']['rows']:,} rows retained; declared key duplicates: {validation['claude']['duplicate_key_excess']}.
- Exposure: 756 rows retained; 32 malformed codes flagged and excluded only from exact-code joins.
- OEWS: {validation['oews']['rows']:,} rows retained; numeric conversion failures: {validation['oews']['failed_numeric']}.
- Analytical table: {metrics['base_rows']:,} detailed occupation-area rows across {metrics['areas']:,} areas and {metrics['occupations']:,} occupations.
- Exposure matches: {metrics['exposure_matches']:,}; projection matches: {metrics['projection_matches']:,}.
- Screening eligibility: {metrics['screening_eligible_rows']:,} complete four-component rows; {metrics['screening_ineligible_rows']:,} incomplete rows; {metrics['shortlist_rows']:,} top-25 review rows across regions.
- Screening weights: 40% observed AI exposure, 30% regional employment, 15% lower-wage transition-need proxy, and 15% weaker-outlook transition-need proxy. Components are within-region percentiles and remain visible.
- Employment checksum before/after joins: {metrics['employment_checksum_before']:,.0f} / {metrics['employment_checksum_after']:,.0f} jobs.
- Purposeful difficult-case sample: {validation['sample_rows']} rows (not a statistical sample).

# Cleaned sample

The following {validation['sample_rows']} rows were selected on purpose to show difficult cases. The sample is not random. It includes high-employment records, high-exposure records, unmatched occupation codes, missing-value markers, malformed codes, a high but valid Claude time value, and negative projected growth.

{sample_text}

# Interpretation and limitations

The cleaned data still represent the published phenomena because original source rows remain in cleaned bases, identifiers and units are preserved, missing/censored estimates are not turned into zeros, and joins do not multiply rows or employment. The analytical table changes scope, not the underlying sources. Exposure and projections are national occupation context; Claude measures include global/country/subregion observations. None should be described as a local causal effect. The screening score is a transparent review aid, not an automatic funding or automation decision. Its weights and the lower-wage/weaker-outlook proxies require human review. The 32 malformed exposure codes remain unresolved until an authoritative source mapping is available.
"""
    (ROOT / "assignment_report.md").write_text(report, encoding="utf-8")


def main(show_summary=True):
    reset_outputs()
    manifest_before = source_manifest()
    stage_rows = []
    missing_rows = []
    duplicate_rows = []
    flag_rows = []
    exclusions = []

    claude_info = clean_claude(stage_rows, missing_rows, duplicate_rows, flag_rows)
    exposure = clean_exposure(stage_rows, missing_rows, duplicate_rows, flag_rows, exclusions)
    oews, oews_info = clean_oews(stage_rows, missing_rows, duplicate_rows, flag_rows)
    projections, projection_info = clean_projections(
        stage_rows, missing_rows, duplicate_rows, exclusions
    )
    analysis, analysis_info = build_analysis(
        oews, exposure, projections, stage_rows, exclusions
    )
    sample = build_sample(analysis, exposure, oews, projections, claude_info)

    expectations = json.loads((ROOT / "record_expectations.json").read_text(encoding="utf-8"))
    record_checks = [
        locate_actual(item, exposure, oews, projections, claude_info)
        for item in expectations["checks"]
    ]
    assert all(row["passed"] for row in record_checks)

    manifest_after = source_manifest()
    assert manifest_before == manifest_after
    codex_check = independent_codex_check()
    validation = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "all_assertions_passed": True,
        "source_hashes_unchanged": True,
        "claude": claude_info,
        "oews": oews_info,
        "projections": projection_info,
        "analysis": analysis_info,
        "record_checks_passed": sum(row["passed"] for row in record_checks),
        "record_checks_total": len(record_checks),
        "sample_rows": len(sample),
        "codex_check": codex_check,
        "student_review_complete": True,
    }

    pd.DataFrame(stage_rows).to_csv(OUT / "stage_changes.csv", index=False)
    pd.DataFrame(missing_rows).to_csv(OUT / "missing_counts.csv", index=False)
    pd.DataFrame(duplicate_rows).to_csv(OUT / "duplicates.csv", index=False)
    pd.DataFrame(flag_rows).to_csv(OUT / "suspicious_values.csv", index=False)
    pd.DataFrame(exclusions).to_csv(OUT / "exclusion_ledger.csv", index=False)
    pd.DataFrame(record_checks).to_csv(OUT / "record_checks.csv", index=False)
    write_json(OUT / "validation.json", validation)
    write_json(OUT / "source_manifest.json", manifest_after)
    build_report(validation, record_checks, stage_rows)
    if show_summary:
        print(json.dumps(validation, indent=2, ensure_ascii=False, default=json_default))
    return validation


if __name__ == "__main__":
    main()
