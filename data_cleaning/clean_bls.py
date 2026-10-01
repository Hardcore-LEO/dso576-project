import pandas as pd


# --------------------------------------------------
# Columns used as numeric measures in this project
# --------------------------------------------------

NUMERIC_COLUMNS = [
    "TOT_EMP",
    "EMP_PRSE",
    "JOBS_1000",
    "LOC_QUOTIENT",
    "PCT_TOTAL",
    "PCT_RPT",
    "H_MEAN",
    "A_MEAN",
    "MEAN_PRSE",
    "H_PCT10",
    "H_PCT25",
    "H_MEDIAN",
    "H_PCT75",
    "H_PCT90",
    "A_PCT10",
    "A_PCT25",
    "A_MEDIAN",
    "A_PCT75",
    "A_PCT90",
]


# --------------------------------------------------
# Load data
# --------------------------------------------------

def load_bls(msa_path, nonmetro_path):
    """
    Load the original BLS OEWS metropolitan and nonmetropolitan files.
    """

    msa = pd.read_excel(
        msa_path,
        dtype={
            "AREA": "string",
            "OCC_CODE": "string",
        },
    )

    nonmetro = pd.read_excel(
        nonmetro_path,
        dtype={
            "AREA": "string",
            "OCC_CODE": "string",
        },
    )

    return msa, nonmetro


# --------------------------------------------------
# Clean one BLS source table
# --------------------------------------------------

def _clean_bls_table(df, area_type):
    """
    Apply the predefined BLS cleaning rules to one source table.
    """

    df = df.copy()

    # --------------------------------------------------
    # Rule 1: Keep California records
    # --------------------------------------------------

    df = df[
        df["PRIM_STATE"] == "CA"
    ].copy()

    # --------------------------------------------------
    # Rule 2: Keep detailed occupations
    # --------------------------------------------------

    df = df[
        df["O_GROUP"] == "detailed"
    ].copy()

    # --------------------------------------------------
    # Rule 3: Add area type before combining files
    # --------------------------------------------------

    df["area_type"] = area_type

    # Preserve identifiers as text
    df["AREA"] = df["AREA"].astype("string")
    df["OCC_CODE"] = df["OCC_CODE"].astype("string")

    # --------------------------------------------------
    # Rules 4-6:
    # Handle BLS special symbols before numeric conversion
    # --------------------------------------------------

    for col in NUMERIC_COLUMNS:

        if col not in df.columns:
            continue

        # Preserve the original source value for auditing
        df[f"{col}_raw"] = df[col]

        # Flags for BLS special values
        df[f"{col}_unavailable_flag"] = (
            df[col].astype(str).isin(["*", "**"])
        )

        df[f"{col}_high_wage_flag"] = (
            df[col].astype(str).eq("#")
        )

        # Convert special symbols to missing
        cleaned_values = df[col].replace(
            {
                "*": pd.NA,
                "**": pd.NA,
                "#": pd.NA,
            }
        )

        # Convert valid published values to numeric
        df[col] = pd.to_numeric(
            cleaned_values,
            errors="coerce",
        )

    return df


# --------------------------------------------------
# Clean and combine BLS data
# --------------------------------------------------

def clean_bls(msa, nonmetro):
    """
    Clean the metropolitan and nonmetropolitan OEWS files
    and combine them into one California detailed-occupation table.
    """

    msa_clean = _clean_bls_table(
        msa,
        area_type="metro",
    )

    nonmetro_clean = _clean_bls_table(
        nonmetro,
        area_type="nonmetro",
    )

    combined = pd.concat(
        [msa_clean, nonmetro_clean],
        ignore_index=True,
    )

    return combined


# --------------------------------------------------
# Audit
# --------------------------------------------------

def audit_bls(msa_raw, nonmetro_raw, cleaned):
    """
    Return verification results for display in the notebook.
    """

    # ----------------------------
    # Counts after project filters
    # ----------------------------

    msa_project = msa_raw[
        (msa_raw["PRIM_STATE"] == "CA")
        & (msa_raw["O_GROUP"] == "detailed")
    ].copy()

    nonmetro_project = nonmetro_raw[
        (nonmetro_raw["PRIM_STATE"] == "CA")
        & (nonmetro_raw["O_GROUP"] == "detailed")
    ].copy()

    # ----------------------------
    # Candidate key
    # ----------------------------

    key_cols = [
        "AREA",
        "OCC_CODE",
    ]

    # ----------------------------
    # Special-symbol counts
    # ----------------------------

    special_symbol_rows = []

    for source_name, source_df in [
        ("metro", msa_project),
        ("nonmetro", nonmetro_project),
    ]:

        for col in NUMERIC_COLUMNS:

            if col not in source_df.columns:
                continue

            values = source_df[col].astype(str)

            special_symbol_rows.append({
                "area_type": source_name,
                "column": col,
                "*": (values == "*").sum(),
                "**": (values == "**").sum(),
                "#": (values == "#").sum(),
            })

    special_symbol_counts = pd.DataFrame(
        special_symbol_rows
    )

    # ----------------------------
    # Numeric conversion failures
    # ----------------------------

    conversion_rows = []

    for col in NUMERIC_COLUMNS:

        if col not in cleaned.columns:
            continue

        raw_col = f"{col}_raw"

        if raw_col not in cleaned.columns:
            continue

        original = cleaned[raw_col]

        # Values that are neither missing nor recognized special symbols
        normal_values = (
            original.notna()
            & ~original.astype(str).isin(["*", "**", "#"])
        )

        failed_conversion = (
            normal_values
            & cleaned[col].isna()
        )

        conversion_rows.append({
            "column": col,
            "failed_conversions": failed_conversion.sum(),
        })

    conversion_failures = pd.DataFrame(
        conversion_rows
    )

    # ----------------------------
    # Flag checks
    # ----------------------------

    flag_rows = []

    for col in NUMERIC_COLUMNS:

        if col not in cleaned.columns:
            continue

        raw_col = f"{col}_raw"
        unavailable_flag = f"{col}_unavailable_flag"
        high_wage_flag = f"{col}_high_wage_flag"

        if raw_col not in cleaned.columns:
            continue

        raw_values = cleaned[raw_col].astype(str)

        flag_rows.append({
            "column": col,

            "raw_unavailable_symbols": (
                raw_values.isin(["*", "**"])
            ).sum(),

            "unavailable_flags": (
                cleaned[unavailable_flag].sum()
            ),

            "raw_high_wage_symbols": (
                raw_values.eq("#")
            ).sum(),

            "high_wage_flags": (
                cleaned[high_wage_flag].sum()
            ),
        })

    flag_check = pd.DataFrame(
        flag_rows
    )

    # ----------------------------
    # Numeric summaries
    # ----------------------------

    available_numeric_columns = [
        col
        for col in NUMERIC_COLUMNS
        if col in cleaned.columns
    ]

    numeric_summary = cleaned[
        available_numeric_columns
    ].describe().T

    # ----------------------------
    # Final audit dictionary
    # ----------------------------

    audit = {
        # raw counts
        "msa_raw_rows": len(msa_raw),
        "nonmetro_raw_rows": len(nonmetro_raw),

        # filtered counts
        "msa_project_rows": len(msa_project),
        "nonmetro_project_rows": len(nonmetro_project),

        # final count
        "cleaned_rows": len(cleaned),
        "cleaned_columns": cleaned.shape[1],

        # geography
        "metro_areas": msa_project["AREA"].nunique(),
        "nonmetro_areas": nonmetro_project["AREA"].nunique(),
        "total_areas": cleaned["AREA"].nunique(),

        # occupation
        "unique_occupations": cleaned[
            "OCC_CODE"
        ].nunique(),

        # duplicate checks
        "exact_duplicates": cleaned.duplicated().sum(),

        "repeated_area_occupation_keys": (
            cleaned.duplicated(
                subset=key_cols
            ).sum()
        ),

        # project filters
        "states_remaining": sorted(
            cleaned["PRIM_STATE"]
            .dropna()
            .unique()
            .tolist()
        ),

        "occupation_groups_remaining": sorted(
            cleaned["O_GROUP"]
            .dropna()
            .unique()
            .tolist()
        ),

        "area_type_counts": (
            cleaned["area_type"]
            .value_counts()
            .rename_axis("area_type")
            .reset_index(name="rows")
        ),

        # missing
        "missing_values": (
            cleaned[
                available_numeric_columns
            ]
            .isna()
            .sum()
            .rename("missing_count")
            .to_frame()
        ),

        # special symbols
        "special_symbol_counts": special_symbol_counts,

        # failed numeric conversions
        "conversion_failures": conversion_failures,

        # verify special-value flags
        "flag_check": flag_check,

        # suspicious/extreme-value review
        "numeric_summary": numeric_summary,
    }

    return audit