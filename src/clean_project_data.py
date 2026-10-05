"""Clean and merge the AI Workforce Investment Planner source data.

The script keeps source files read-only and writes reproducible outputs under
the selected output root. Run ``python src/clean_project_data.py --help`` for
usage details.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


ANTHROPIC_FILE = "aei_claude_ai_2026-06-26.csv"
ONET_FILE = "Occupation Data (1).xlsx"
MSA_FILE = "MSA_M2025_dl.xlsx"
BOS_FILE = "BOS_M2025_dl.xlsx"

ANTHROPIC_START = "2026-05-01"
ANTHROPIC_END = "2026-06-01"
ANTHROPIC_COLUMNS = [
    "date_start",
    "date_end",
    "geo_id",
    "geo_level",
    "category_name",
    "hierarchy_level",
    "metric_id",
    "value",
    "node_name",
    "node_external_id",
]

BLS_ID_COLUMNS = [
    "AREA",
    "AREA_TITLE",
    "AREA_TYPE",
    "PRIM_STATE",
    "NAICS",
    "NAICS_TITLE",
    "I_GROUP",
    "OWN_CODE",
    "OCC_CODE",
    "OCC_TITLE",
    "O_GROUP",
]
BLS_MEASURE_COLUMNS = ["TOT_EMP", "A_MEDIAN", "JOBS_1000", "LOC_QUOTIENT"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory containing the four unchanged source files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd(),
        help="Project root that will receive data/processed, data/sample, and reports.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200_000,
        help="Rows per Anthropic CSV chunk.",
    )
    return parser.parse_args()


def require_sources(data_dir: Path) -> dict[str, Path]:
    paths = {
        "anthropic": data_dir / ANTHROPIC_FILE,
        "onet": data_dir / ONET_FILE,
        "msa": data_dir / MSA_FILE,
        "bos": data_dir / BOS_FILE,
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing source files:\n" + "\n".join(missing))
    return paths


def ensure_output_dirs(output_root: Path) -> dict[str, Path]:
    dirs = {
        "processed": output_root / "data" / "processed",
        "sample": output_root / "data" / "sample",
        "reports": output_root / "reports",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    return dirs


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def to_numeric(series: pd.Series) -> pd.Series:
    cleaned = clean_text(series).str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def read_anthropic(path: Path, chunk_size: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_rows = 0
    missing = Counter()
    seen_hashes: set[int] = set()
    exact_duplicates = 0
    pieces: list[pd.DataFrame] = []
    date_starts: set[str] = set()
    date_ends: set[str] = set()

    for chunk in pd.read_csv(
        path,
        dtype="string",
        usecols=ANTHROPIC_COLUMNS,
        chunksize=chunk_size,
        low_memory=False,
    ):
        source_rows += len(chunk)
        missing.update(chunk.isna().sum().to_dict())
        date_starts.update(chunk["date_start"].dropna().unique().tolist())
        date_ends.update(chunk["date_end"].dropna().unique().tolist())

        hashes = pd.util.hash_pandas_object(chunk.fillna("<NA>"), index=False)
        for value in hashes.to_numpy():
            integer = int(value)
            if integer in seen_hashes:
                exact_duplicates += 1
            else:
                seen_hashes.add(integer)

        mask = (
            chunk["date_start"].eq(ANTHROPIC_START)
            & chunk["date_end"].eq(ANTHROPIC_END)
            & chunk["geo_id"].str.fullmatch(r"US-[A-Z]{2}", na=False)
            & chunk["geo_level"].eq("subregion")
            & chunk["category_name"].eq("soc_occupation")
            & chunk["hierarchy_level"].eq("0")
            & chunk["metric_id"].eq("pct")
        )
        pieces.append(chunk.loc[mask].copy())

    filtered = pd.concat(pieces, ignore_index=True)
    filtered["geo_id"] = clean_text(filtered["geo_id"])
    filtered["node_external_id"] = clean_text(filtered["node_external_id"])
    filtered["node_name"] = clean_text(filtered["node_name"])
    filtered["state"] = filtered["geo_id"].str.removeprefix("US-")
    filtered["claude_usage_pct"] = to_numeric(filtered["value"])

    invalid_value_count = int(filtered["claude_usage_pct"].isna().sum())
    out_of_range_count = int(
        (
            (~filtered["claude_usage_pct"].between(0, 100, inclusive="both"))
            & filtered["claude_usage_pct"].notna()
        ).sum()
    )
    duplicate_keys = int(
        filtered.duplicated(
            ["date_start", "date_end", "geo_id", "node_external_id"], keep=False
        ).sum()
    )
    if invalid_value_count or out_of_range_count or duplicate_keys:
        raise ValueError(
            "Anthropic validation failed: "
            f"invalid_values={invalid_value_count}, out_of_range={out_of_range_count}, "
            f"duplicate_key_rows={duplicate_keys}"
        )

    audit = {
        "source_rows": source_rows,
        "source_exact_duplicate_rows": exact_duplicates,
        "source_missing_by_column": dict(missing),
        "source_date_start_values": sorted(date_starts),
        "source_date_end_values": sorted(date_ends),
        "filtered_rows": len(filtered),
        "filtered_states": int(filtered["state"].nunique()),
        "filtered_occupations": int(filtered["node_external_id"].nunique()),
        "filtered_duplicate_key_rows": duplicate_keys,
        "invalid_numeric_values": invalid_value_count,
        "out_of_range_values": out_of_range_count,
        "published_occupation_count_by_state": (
            filtered.groupby("state")["node_external_id"].nunique().sort_index().to_dict()
        ),
        "published_pct_sum_by_state": (
            filtered.groupby("state")["claude_usage_pct"].sum().round(6).sort_index().to_dict()
        ),
    }
    return filtered, audit


def read_onet(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    onet = pd.read_excel(
        path,
        sheet_name="Occupation Data",
        dtype="string",
        usecols=["O*NET-SOC Code", "Title", "Description"],
    )
    onet.columns = ["onet_soc_code", "onet_title", "onet_description"]
    for column in onet.columns:
        onet[column] = clean_text(onet[column])

    code_pattern = r"\d{2}-\d{4}\.\d{2}"
    invalid_codes = int((~onet["onet_soc_code"].str.fullmatch(code_pattern, na=False)).sum())
    duplicate_codes = int(onet.duplicated("onet_soc_code", keep=False).sum())
    if invalid_codes or duplicate_codes:
        raise ValueError(
            f"O*NET validation failed: invalid_codes={invalid_codes}, "
            f"duplicate_code_rows={duplicate_codes}"
        )

    audit = {
        "source_rows": len(onet),
        "missing_by_column": onet.isna().sum().to_dict(),
        "invalid_code_rows": invalid_codes,
        "duplicate_code_rows": duplicate_codes,
    }
    return onet, audit


def map_and_aggregate_ai(
    anthropic: pd.DataFrame, onet: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    mapped = anthropic.merge(
        onet,
        left_on="node_external_id",
        right_on="onet_soc_code",
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    unmatched = mapped.loc[mapped["_merge"].ne("both"), "node_external_id"].drop_duplicates()
    if not unmatched.empty:
        raise ValueError(f"Unmatched Anthropic O*NET codes: {unmatched.head(20).tolist()}")

    mapped["soc6"] = mapped["onet_soc_code"].str.slice(0, 7)
    invalid_soc6 = int((~mapped["soc6"].str.fullmatch(r"\d{2}-\d{4}", na=False)).sum())
    if invalid_soc6:
        raise ValueError(f"Invalid derived six-digit SOC rows: {invalid_soc6}")

    ai = (
        mapped.groupby(["state", "soc6"], as_index=False, sort=True)
        .agg(
            claude_usage_pct=("claude_usage_pct", "sum"),
            onet_occupation_count=("onet_soc_code", "nunique"),
            onet_titles=("onet_title", lambda s: " | ".join(sorted(set(s.dropna())))),
        )
    )
    ai["claude_usage_pct"] = ai["claude_usage_pct"].round(6)
    duplicate_keys = int(ai.duplicated(["state", "soc6"], keep=False).sum())
    if duplicate_keys:
        raise ValueError(f"Duplicate AI state + soc6 rows: {duplicate_keys}")

    audit = {
        "mapped_rows": len(mapped),
        "matched_rows": int(mapped["_merge"].eq("both").sum()),
        "unmatched_rows": int(mapped["_merge"].ne("both").sum()),
        "invalid_derived_soc6_rows": invalid_soc6,
        "aggregated_rows": len(ai),
        "aggregated_duplicate_key_rows": duplicate_keys,
        "claude_usage_pct_min": float(ai["claude_usage_pct"].min()),
        "claude_usage_pct_max": float(ai["claude_usage_pct"].max()),
    }
    return ai, audit


def read_bls_file(path: Path, sheet_name: str, area_category: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_excel(
        path,
        sheet_name=sheet_name,
        dtype="string",
        usecols=BLS_ID_COLUMNS + BLS_MEASURE_COLUMNS,
    )
    for column in BLS_ID_COLUMNS + BLS_MEASURE_COLUMNS:
        raw[column] = clean_text(raw[column])

    mask = (
        raw["NAICS"].eq("000000")
        & raw["I_GROUP"].eq("cross-industry")
        & raw["OWN_CODE"].eq("1235")
        & raw["O_GROUP"].eq("detailed")
    )
    clean = raw.loc[mask].copy()
    clean.insert(0, "area_category", area_category)
    clean["TOT_EMP_raw"] = clean["TOT_EMP"]
    clean["A_MEDIAN_raw"] = clean["A_MEDIAN"]
    clean["employment_suppressed"] = clean["TOT_EMP"].eq("**")
    clean["wage_unavailable"] = clean["A_MEDIAN"].eq("*")
    clean["wage_topcoded"] = clean["A_MEDIAN"].eq("#")

    for column in BLS_MEASURE_COLUMNS:
        clean[column] = to_numeric(clean[column])

    clean["is_multistate_msa"] = False
    if area_category == "metropolitan":
        suffix = clean["AREA_TITLE"].str.rsplit(",", n=1).str[-1].str.strip()
        clean["is_multistate_msa"] = suffix.str.contains("-", regex=False, na=False)

    duplicate_keys = int(clean.duplicated(["AREA", "OCC_CODE"], keep=False).sum())
    invalid_occ_codes = int((~clean["OCC_CODE"].str.fullmatch(r"\d{2}-\d{4}", na=False)).sum())
    if duplicate_keys or invalid_occ_codes:
        raise ValueError(
            f"BLS {area_category} validation failed: duplicate_key_rows={duplicate_keys}, "
            f"invalid_occ_code_rows={invalid_occ_codes}"
        )

    audit = {
        "source_rows": len(raw),
        "filtered_detailed_rows": len(clean),
        "removed_non_detailed_or_non_cross_industry_rows": len(raw) - len(clean),
        "duplicate_area_occupation_rows": duplicate_keys,
        "invalid_occ_code_rows": invalid_occ_codes,
        "employment_suppressed_rows": int(clean["employment_suppressed"].sum()),
        "wage_unavailable_rows": int(clean["wage_unavailable"].sum()),
        "wage_topcoded_rows": int(clean["wage_topcoded"].sum()),
        "multistate_msa_rows": int(clean["is_multistate_msa"].sum()),
        "numeric_missing_after_cleaning": clean[BLS_MEASURE_COLUMNS].isna().sum().to_dict(),
    }
    return clean, audit


def merge_bls_ai(bls: pd.DataFrame, ai: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = bls.merge(
        ai,
        left_on=["PRIM_STATE", "OCC_CODE"],
        right_on=["state", "soc6"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    merged["ai_merge_status"] = merged["_merge"].astype("string")
    merged = merged.drop(columns="_merge")

    final_key = ["area_category", "AREA", "OCC_CODE"]
    duplicate_final_keys = int(merged.duplicated(final_key, keep=False).sum())
    if len(merged) != len(bls) or duplicate_final_keys:
        raise ValueError(
            f"Final merge validation failed: before={len(bls)}, after={len(merged)}, "
            f"duplicate_key_rows={duplicate_final_keys}"
        )

    match_by_area = (
        merged.groupby("area_category")["ai_merge_status"]
        .value_counts()
        .unstack(fill_value=0)
        .to_dict(orient="index")
    )
    match_by_state = (
        merged.groupby("PRIM_STATE")["ai_merge_status"]
        .value_counts()
        .unstack(fill_value=0)
        .to_dict(orient="index")
    )
    audit = {
        "bls_rows_before_merge": len(bls),
        "final_rows": len(merged),
        "matched_rows": int(merged["ai_merge_status"].eq("both").sum()),
        "unmatched_bls_rows": int(merged["ai_merge_status"].eq("left_only").sum()),
        "final_duplicate_key_rows": duplicate_final_keys,
        "match_status_by_area_category": match_by_area,
        "match_status_by_state": match_by_state,
        "nonmissing_metric_counts": {
            column: int(merged[column].notna().sum())
            for column in [
                "claude_usage_pct",
                "TOT_EMP",
                "A_MEDIAN",
                "JOBS_1000",
                "LOC_QUOTIENT",
            ]
        },
    }
    return merged, audit


def select_one(df: pd.DataFrame, **conditions: Any) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for column, value in conditions.items():
        mask &= df[column].eq(value)
    matches = df.loc[mask]
    if len(matches) != 1:
        raise AssertionError(f"Expected one row for {conditions}, found {len(matches)}")
    return matches.iloc[0]


def make_record_checks(
    anthropic: pd.DataFrame,
    onet: pd.DataFrame,
    ai: pd.DataFrame,
    merged: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []

    source_1 = select_one(anthropic, geo_id="US-CA", node_external_id="27-1014.00")
    onet_1 = select_one(onet, onet_soc_code="27-1014.00")
    pass_1 = (
        onet_1["onet_title"] == source_1["node_name"]
        and source_1["state"] == "CA"
        and source_1["claude_usage_pct"] == 0.03
    )
    records.append(
        {
            "check_id": 1,
            "title": "Direct occupation mapping",
            "original": "US-CA; 27-1014.00; pct=0.03",
            "expected": "Exact O*NET match; state=CA; soc6=27-1014; value remains 0.03",
            "actual": f"title={onet_1['onet_title']}; state={source_1['state']}; value={source_1['claude_usage_pct']}",
            "passed": bool(pass_1),
        }
    )

    source_2 = anthropic.loc[
        anthropic["geo_id"].eq("US-CA")
        & anthropic["node_external_id"].isin(["11-3031.00", "11-3031.01", "11-3031.03"])
    ]
    ai_2 = select_one(ai, state="CA", soc6="11-3031")
    expected_sum = round(float(source_2["claude_usage_pct"].sum()), 6)
    pass_2 = expected_sum == 0.41 and ai_2["claude_usage_pct"] == 0.41 and ai_2["onet_occupation_count"] == 3
    records.append(
        {
            "check_id": 2,
            "title": "Aggregate multiple O*NET extensions",
            "original": "US-CA 11-3031.00=0.13; 11-3031.01=0.10; 11-3031.03=0.18",
            "expected": "claude_usage_pct=0.41; onet_occupation_count=3",
            "actual": f"claude_usage_pct={ai_2['claude_usage_pct']}; onet_occupation_count={ai_2['onet_occupation_count']}",
            "passed": bool(pass_2),
        }
    )

    row_3 = select_one(merged, area_category="metropolitan", AREA="10180", OCC_CODE="13-1031")
    pass_3 = pd.isna(row_3["TOT_EMP"]) and bool(row_3["employment_suppressed"])
    records.append(
        {
            "check_id": 3,
            "title": "Suppressed BLS employment",
            "original": "MSA AREA=10180; OCC_CODE=13-1031; TOT_EMP=**",
            "expected": "TOT_EMP missing; employment_suppressed=True; row retained",
            "actual": f"TOT_EMP={row_3['TOT_EMP']}; employment_suppressed={row_3['employment_suppressed']}",
            "passed": bool(pass_3),
        }
    )

    row_4 = select_one(merged, area_category="metropolitan", AREA="10540", OCC_CODE="29-1215")
    pass_4 = pd.isna(row_4["A_MEDIAN"]) and bool(row_4["wage_topcoded"])
    records.append(
        {
            "check_id": 4,
            "title": "Top-coded BLS annual wage",
            "original": "MSA AREA=10540; OCC_CODE=29-1215; A_MEDIAN=#",
            "expected": "A_MEDIAN missing; wage_topcoded=True; row retained",
            "actual": f"A_MEDIAN={row_4['A_MEDIAN']}; wage_topcoded={row_4['wage_topcoded']}",
            "passed": bool(pass_4),
        }
    )

    row_5 = select_one(merged, area_category="metropolitan", AREA="12540", OCC_CODE="13-2011")
    pass_5 = (
        row_5["PRIM_STATE"] == "CA"
        and row_5["claude_usage_pct"] == 0.11
        and row_5["ai_merge_status"] == "both"
    )
    records.append(
        {
            "check_id": 5,
            "title": "State + occupation cross-source lookup",
            "original": "MSA AREA=12540; CA; OCC_CODE=13-2011; Anthropic pct=0.11",
            "expected": "BLS values retained; claude_usage_pct=0.11; merge status both",
            "actual": f"state={row_5['PRIM_STATE']}; claude_usage_pct={row_5['claude_usage_pct']}; merge={row_5['ai_merge_status']}",
            "passed": bool(pass_5),
        }
    )

    result = pd.DataFrame(records)
    if not result["passed"].all():
        failed = result.loc[~result["passed"], "check_id"].tolist()
        raise AssertionError(f"Record checks failed: {failed}")
    return result


def make_sample(merged: pd.DataFrame) -> pd.DataFrame:
    """Build a deterministic, difficult-case sample with no more than 50 rows."""
    pieces = [
        merged.loc[merged["employment_suppressed"]].head(8),
        merged.loc[merged["wage_topcoded"]].head(8),
        merged.loc[merged["ai_merge_status"].eq("left_only")].head(8),
        merged.loc[merged["is_multistate_msa"]].head(8),
        merged.loc[
            merged["area_category"].eq("nonmetropolitan")
            & merged["ai_merge_status"].eq("both")
        ].head(8),
        merged.loc[
            merged["area_category"].eq("metropolitan")
            & merged["ai_merge_status"].eq("both")
        ].head(8),
        merged.loc[
            merged["AREA"].isin(["10180", "10540", "12540"])
            & merged["OCC_CODE"].isin(["13-1031", "29-1215", "13-2011"])
        ],
    ]
    sample = pd.concat(pieces, ignore_index=True)
    sample = sample.drop_duplicates(["area_category", "AREA", "OCC_CODE"]).head(50)
    columns = [
        "area_category",
        "AREA",
        "AREA_TITLE",
        "PRIM_STATE",
        "OCC_CODE",
        "OCC_TITLE",
        "TOT_EMP_raw",
        "TOT_EMP",
        "employment_suppressed",
        "A_MEDIAN_raw",
        "A_MEDIAN",
        "wage_unavailable",
        "wage_topcoded",
        "JOBS_1000",
        "LOC_QUOTIENT",
        "is_multistate_msa",
        "claude_usage_pct",
        "onet_occupation_count",
        "ai_merge_status",
    ]
    return sample[columns].copy()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    sources = require_sources(data_dir)
    dirs = ensure_output_dirs(output_root)

    anthropic, anthropic_audit = read_anthropic(sources["anthropic"], args.chunk_size)
    onet, onet_audit = read_onet(sources["onet"])
    ai, ai_audit = map_and_aggregate_ai(anthropic, onet)

    msa, msa_audit = read_bls_file(sources["msa"], "MSA_M2025_dl", "metropolitan")
    bos, bos_audit = read_bls_file(sources["bos"], "BOS_M2025_dl", "nonmetropolitan")
    bls = pd.concat([msa, bos], ignore_index=True)
    merged, merge_audit = merge_bls_ai(bls, ai)

    record_checks = make_record_checks(anthropic, onet, ai, merged)
    sample = make_sample(merged)

    ai_path = dirs["processed"] / "ai_state_soc6.csv"
    merged_path = dirs["processed"] / "area_occupation_clean.csv"
    sample_path = dirs["sample"] / "area_occupation_sample.csv"
    checks_path = dirs["reports"] / "record_checks.csv"
    audit_path = dirs["reports"] / "cleaning_audit.json"

    ai.to_csv(ai_path, index=False)
    merged.to_csv(merged_path, index=False)
    sample.to_csv(sample_path, index=False)
    record_checks.to_csv(checks_path, index=False)

    audit = {
        "source_files": {
            key: {"filename": path.name, "bytes": path.stat().st_size}
            for key, path in sources.items()
        },
        "rules": {
            "anthropic_period": [ANTHROPIC_START, ANTHROPIC_END],
            "anthropic_filters": {
                "geo_id": "US-XX",
                "geo_level": "subregion",
                "category_name": "soc_occupation",
                "hierarchy_level": "0",
                "metric_id": "pct",
            },
            "bls_filters": {
                "NAICS": "000000",
                "I_GROUP": "cross-industry",
                "OWN_CODE": "1235",
                "O_GROUP": "detailed",
            },
            "final_key": ["area_category", "AREA", "OCC_CODE"],
        },
        "anthropic": anthropic_audit,
        "onet": onet_audit,
        "ai_mapping_and_aggregation": ai_audit,
        "bls_metropolitan": msa_audit,
        "bls_nonmetropolitan": bos_audit,
        "final_merge": merge_audit,
        "sample": {
            "rows": len(sample),
            "area_category_counts": sample["area_category"].value_counts().to_dict(),
            "matched_rows": int(sample["ai_merge_status"].eq("both").sum()),
            "unmatched_rows": int(sample["ai_merge_status"].eq("left_only").sum()),
            "employment_suppressed_rows": int(sample["employment_suppressed"].sum()),
            "wage_topcoded_rows": int(sample["wage_topcoded"].sum()),
            "multistate_msa_rows": int(sample["is_multistate_msa"].sum()),
        },
        "record_checks": {
            "rows": len(record_checks),
            "passed": int(record_checks["passed"].sum()),
        },
        "outputs": {
            "ai_state_soc6": str(ai_path.relative_to(output_root)),
            "area_occupation_clean": str(merged_path.relative_to(output_root)),
            "sample": str(sample_path.relative_to(output_root)),
            "record_checks": str(checks_path.relative_to(output_root)),
            "audit": str(audit_path.relative_to(output_root)),
        },
    }
    audit_path.write_text(json.dumps(json_ready(audit), indent=2, sort_keys=True), encoding="utf-8")

    print(f"Anthropic filtered rows: {len(anthropic):,}")
    print(f"AI state + soc6 rows: {len(ai):,}")
    print(f"BLS detailed rows: {len(bls):,}")
    print(f"Final rows: {len(merged):,}")
    print(f"Matched AI rows: {merge_audit['matched_rows']:,}")
    print(f"Unmatched AI rows: {merge_audit['unmatched_bls_rows']:,}")
    print(f"Sample rows: {len(sample):,}")
    print(f"Record checks passed: {record_checks['passed'].sum()}/{len(record_checks)}")
    print(f"Audit: {audit_path.relative_to(output_root)}")


if __name__ == "__main__":
    main()
