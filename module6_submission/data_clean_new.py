"""Create a compact cleaned California occupation-region dataset.

This pipeline reads the original occupation-exposure, Claude, and BLS files,
cleans only the fields needed for the final merged dataset, and does not
calculate percentiles, screening scores, ranks, or shortlists. It also writes
Excel-safe copies so that SOC codes are not automatically displayed as dates.

Run:
    python data_clean_new.py

Optional paths:
    python data_clean_new.py --source-dir <raw-data-folder> --output <file.csv>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "outputs" / "final_cleaned_core.csv"

REQUIRED_SOURCE_FILES = (
    "aei_claude_ai_2026-06-26.csv",
    "job_exposure.csv",
    "BOS_M2025_dl.xlsx",
    "MSA_M2025_dl.xlsx",
    "occupation.XLSX",
)

SOC_PATTERN = r"\d{2}-\d{4}"
MISSING_MARKERS = {
    "": "missing_blank",
    "*": "unavailable",
    "**": "employment_estimate_unavailable",
    "#": "censored_exact_value_unavailable",
    "~": "below_reporting_threshold",
}

FINAL_COLUMNS = [
    "release",
    "area_class",
    "AREA",
    "AREA_TITLE",
    "OCC_CODE",
    "OCC_TITLE",
    "job_exposure",
    "claude_usage_pct",
    "TOT_EMP",
    "A_MEAN",
    "employment_change_pct",
]


def find_source_dir(requested: Path | None) -> Path:
    """Find the folder containing all four required source files."""
    candidates = []
    if requested is not None:
        candidates.append(requested.resolve())
    candidates.extend(
        [
            SCRIPT_DIR.parent,
            SCRIPT_DIR.parents[1] / "clean_data",
        ]
    )

    for candidate in candidates:
        if all((candidate / name).is_file() for name in REQUIRED_SOURCE_FILES):
            return candidate

    checked = "\n".join(f"  - {candidate}" for candidate in candidates)
    raise FileNotFoundError(
        "Could not find all required source files. Checked:\n" + checked
    )


def numeric_with_status(series: pd.Series, column: str) -> tuple[pd.Series, pd.Series]:
    """Convert an OEWS field to numeric while preserving marker meaning."""
    raw = series.astype("string").str.strip()
    status = raw.map(MISSING_MARKERS).fillna("reported").astype("string")
    numeric = pd.to_numeric(raw.mask(raw.isin(MISSING_MARKERS)), errors="coerce")

    unrecognized = ~raw.isin(MISSING_MARKERS) & numeric.isna()
    if unrecognized.any():
        examples = sorted(raw.loc[unrecognized].dropna().unique().tolist())[:5]
        raise ValueError(f"Unrecognized values in {column}: {examples}")

    return numeric.astype("Float64"), status


def normalized_title(series: pd.Series) -> pd.Series:
    """Normalize display titles only for deterministic exact matching."""
    return (
        series.astype("string")
        .str.strip()
        .str.casefold()
        .str.replace(r"\s+", " ", regex=True)
    )


def clean_exposure(
    source_dir: Path, occupation_reference: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    """Clean exposure and safely recover date-corrupted SOC codes by title."""
    exposure = pd.read_csv(
        source_dir / "job_exposure.csv",
        dtype="string",
        keep_default_na=False,
    )
    exposure["title"] = exposure["title"].str.strip()
    exposure["observed_exposure"] = pd.to_numeric(
        exposure["observed_exposure"], errors="coerce"
    ).astype("Float64")

    valid_code = exposure["occ_code"].str.fullmatch(SOC_PATTERN, na=False)

    # Excel previously converted some management SOC codes such as 11-2021
    # into strings such as Nov-21. Recover a code only when the cleaned source
    # title maps to exactly one BLS SOC title; never infer from the date-like
    # string itself.
    reference = occupation_reference[["OCC_CODE", "OCC_TITLE"]].drop_duplicates()
    reference["title_key"] = normalized_title(reference["OCC_TITLE"])
    codes_per_title = reference.groupby("title_key")["OCC_CODE"].nunique()
    unique_reference = (
        reference.loc[reference["title_key"].map(codes_per_title).eq(1)]
        .drop_duplicates("title_key")
        .set_index("title_key")["OCC_CODE"]
    )
    recovered = normalized_title(exposure["title"]).map(unique_reference)
    exposure["clean_occ_code"] = exposure["occ_code"].where(valid_code, recovered)
    recovered_count = int((~valid_code & exposure["clean_occ_code"].notna()).sum())

    still_invalid = ~exposure["clean_occ_code"].str.fullmatch(SOC_PATTERN, na=False)
    if still_invalid.any():
        bad_titles = exposure.loc[still_invalid, "title"].tolist()
        raise ValueError(f"Unresolved exposure occupation codes: {bad_titles}")

    unique_code = ~exposure["clean_occ_code"].duplicated(keep=False)
    join_eligible = ~still_invalid & unique_code

    bad_exposure = ~exposure["observed_exposure"].between(0, 1)
    if bad_exposure.any():
        raise ValueError("AI exposure contains missing values or values outside 0-1.")

    lookup = exposure.loc[
        join_eligible, ["clean_occ_code", "observed_exposure"]
    ].rename(
        columns={
            "clean_occ_code": "occ_code",
            "observed_exposure": "job_exposure",
        }
    )
    if not lookup["occ_code"].is_unique:
        raise ValueError("Eligible exposure SOC codes are not unique.")

    return lookup, recovered_count


def clean_claude_usage(source_dir: Path) -> pd.DataFrame:
    """Return the latest California occupation usage share by six-digit SOC.

    Claude publishes California occupation shares at the detailed O*NET-SOC
    level (for example, 13-1041.07), while OEWS uses six-digit SOC codes (for
    example, 13-1041). Shares for detailed codes under the same six-digit SOC
    are therefore summed before the merge.
    """
    source = source_dir / "aei_claude_ai_2026-06-26.csv"
    usecols = [
        "date_end",
        "geo_id",
        "geo_level",
        "category_name",
        "hierarchy_level",
        "metric_id",
        "value",
        "node_external_id",
    ]
    selected_chunks = []

    for chunk in pd.read_csv(
        source,
        usecols=usecols,
        dtype="string",
        keep_default_na=False,
        chunksize=200_000,
    ):
        selected = (
            chunk["geo_id"].eq("US-CA")
            & chunk["geo_level"].eq("subregion")
            & chunk["category_name"].eq("soc_occupation")
            & chunk["hierarchy_level"].eq("0")
            & chunk["metric_id"].eq("pct")
        )
        if selected.any():
            selected_chunks.append(
                chunk.loc[selected, ["date_end", "node_external_id", "value"]]
            )

    if not selected_chunks:
        raise ValueError("No California Claude occupation percentage rows found.")

    claude = pd.concat(selected_chunks, ignore_index=True)
    latest_date = claude["date_end"].max()
    claude = claude.loc[claude["date_end"].eq(latest_date)].copy()
    claude["OCC_CODE"] = claude["node_external_id"].str.extract(
        rf"^({SOC_PATTERN})", expand=False
    )
    claude["claude_usage_pct"] = pd.to_numeric(
        claude["value"], errors="coerce"
    ).astype("Float64")

    invalid = claude["OCC_CODE"].isna() | claude["claude_usage_pct"].isna()
    if invalid.any():
        raise ValueError("Claude occupation rows contain invalid SOC codes or values.")

    lookup = (
        claude.groupby("OCC_CODE", as_index=False, sort=True)["claude_usage_pct"]
        .sum()
        .astype({"claude_usage_pct": "Float64"})
    )
    if not lookup["OCC_CODE"].is_unique:
        raise ValueError("Aggregated Claude SOC codes are not unique.")

    return lookup


def clean_oews(source_dir: Path) -> pd.DataFrame:
    """Clean the required OEWS fields and build the California base table."""
    source_specs = (
        ("BOS_M2025_dl.xlsx", "BOS_M2025_dl", "nonmetropolitan"),
        ("MSA_M2025_dl.xlsx", "MSA_M2025_dl", "metropolitan"),
    )
    required_columns = [
        "AREA",
        "AREA_TITLE",
        "PRIM_STATE",
        "NAICS",
        "I_GROUP",
        "OWN_CODE",
        "OCC_CODE",
        "OCC_TITLE",
        "O_GROUP",
        "TOT_EMP",
        "A_MEAN",
    ]
    frames = []

    for filename, sheet_name, area_class in source_specs:
        frame = pd.read_excel(
            source_dir / filename,
            sheet_name=sheet_name,
            usecols=required_columns,
            dtype="string",
            keep_default_na=False,
            engine="openpyxl",
        )
        frame["AREA_TITLE"] = frame["AREA_TITLE"].str.strip()
        frame["OCC_TITLE"] = frame["OCC_TITLE"].str.strip()
        frame["release"] = "May 2025"
        frame["area_class"] = area_class

        for column in ("TOT_EMP", "A_MEAN"):
            numeric, status = numeric_with_status(frame[column], column)
            frame[column] = numeric
            frame[f"{column}__status"] = status

        frames.append(frame)

    oews = pd.concat(frames, ignore_index=True)
    scope = (
        oews["PRIM_STATE"].eq("CA")
        & oews["NAICS"].eq("000000")
        & oews["I_GROUP"].eq("cross-industry")
        & oews["OWN_CODE"].eq("1235")
        & oews["O_GROUP"].eq("detailed")
    )
    base = oews.loc[scope].copy()

    if base.duplicated(["AREA", "OCC_CODE"]).any():
        raise ValueError("California OEWS base contains repeated AREA/OCC_CODE keys.")

    return base


def find_column(columns: list[str], required_text: tuple[str, ...]) -> str:
    """Find one column whose normalized name contains every required phrase."""
    matches = [
        column
        for column in columns
        if all(text in column.lower() for text in required_text)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one column containing {required_text}; found {matches}."
        )
    return matches[0]


def clean_projection(source_dir: Path) -> pd.DataFrame:
    """Clean Table 1.2 and return the SOC-level outlook lookup."""
    projection = pd.read_excel(
        source_dir / "occupation.XLSX",
        sheet_name="Table 1.2",
        header=1,
        dtype="string",
        keep_default_na=False,
        engine="openpyxl",
    )
    projection.columns = [str(column) for column in projection.columns]

    code_column = find_column(
        projection.columns.tolist(), ("national employment matrix code",)
    )
    growth_column = find_column(
        projection.columns.tolist(), ("employment change", "percent", "2025")
    )

    # Rows without a matrix code are worksheet titles, footers, notes, or blanks.
    projection = projection.loc[projection[code_column].ne("")].copy()
    projection[code_column] = projection[code_column].str.strip()
    projection[growth_column] = pd.to_numeric(
        projection[growth_column].replace({"": pd.NA, "—": pd.NA, "–": pd.NA}),
        errors="coerce",
    ).astype("Float64")

    lookup = projection[[code_column, growth_column]].rename(
        columns={
            code_column: "projection_occ_code",
            growth_column: "employment_change_pct",
        }
    )
    if not lookup["projection_occ_code"].is_unique:
        raise ValueError("Projection SOC codes in Table 1.2 are not unique.")

    return lookup


def build_dataset(source_dir: Path) -> pd.DataFrame:
    """Clean, left-join, validate, and return the compact final dataset."""
    base = clean_oews(source_dir)
    exposure, recovered_count = clean_exposure(source_dir, base)
    claude_usage = clean_claude_usage(source_dir)
    projection = clean_projection(source_dir)

    rows_before = len(base)
    employment_before = base["TOT_EMP"].sum(skipna=True)

    merged = base.merge(
        exposure,
        how="left",
        left_on="OCC_CODE",
        right_on="occ_code",
        validate="many_to_one",
    )
    merged = merged.merge(
        claude_usage,
        how="left",
        on="OCC_CODE",
        validate="many_to_one",
    )
    merged = merged.merge(
        projection,
        how="left",
        left_on="OCC_CODE",
        right_on="projection_occ_code",
        validate="many_to_one",
    )

    if len(merged) != rows_before:
        raise AssertionError("A join changed the number of California base rows.")
    if merged["TOT_EMP"].sum(skipna=True) != employment_before:
        raise AssertionError("A join changed the California employment checksum.")

    result = merged[FINAL_COLUMNS].sort_values(
        ["AREA_TITLE", "OCC_CODE"], kind="stable"
    )
    result.attrs["recovered_exposure_codes"] = recovered_count
    return result


def write_excel_text_safe(frame: pd.DataFrame, path: Path) -> None:
    """Write an XLSX copy with the SOC column explicitly formatted as text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="cleaned_data", index=False)
        sheet = writer.book["cleaned_data"]
        occ_column = FINAL_COLUMNS.index("OCC_CODE") + 1
        for row_number in range(2, len(frame) + 2):
            sheet.cell(row=row_number, column=occ_column).number_format = "@"
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a compact cleaned California occupation-region CSV."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Folder containing the four original source files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = find_source_dir(args.source_dir)
    output = args.output.resolve()

    result = build_dataset(source_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)

    numeric_fields = [
        "job_exposure",
        "claude_usage_pct",
        "TOT_EMP",
        "A_MEAN",
        "employment_change_pct",
    ]
    complete = result.dropna(subset=numeric_fields).copy()
    complete_output = output.with_name(f"{output.stem}_complete{output.suffix}")
    result_excel = output.with_suffix(".xlsx")
    complete_excel = complete_output.with_suffix(".xlsx")
    complete.to_csv(complete_output, index=False)
    write_excel_text_safe(result, result_excel)
    write_excel_text_safe(complete, complete_excel)

    print(f"Source folder: {source_dir}")
    print(f"Output file:   {output}")
    print(f"Excel-safe:    {result_excel}")
    print(f"Complete file: {complete_output}")
    print(f"Complete XLSX: {complete_excel}")
    print(f"Rows:          {len(result):,}")
    print(f"Columns:       {len(result.columns)}")
    print(
        "Recovered date-corrupted exposure SOC codes: "
        f"{result.attrs['recovered_exposure_codes']}"
    )
    print(f"Rows with all five measures: {len(complete):,}")
    print(f"Job exposure matches: {int(result['job_exposure'].notna().sum()):,}")
    print(f"Claude usage matches: {int(result['claude_usage_pct'].notna().sum()):,}")
    print(
        "Projection matches: "
        f"{int(result['employment_change_pct'].notna().sum()):,}"
    )


if __name__ == "__main__":
    main()
