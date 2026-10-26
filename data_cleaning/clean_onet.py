import pandas as pd


SOC_FULL_PATTERN = r"^\d{2}-\d{4}\.\d{2}$"
SOC6_PATTERN = r"^\d{2}-\d{4}$"


def load_onet(path):
    """
    Load the original O*NET Occupation Data file.
    Preserve O*NET-SOC Code as text.
    """

    df = pd.read_excel(
        path,
        dtype={
            "O*NET-SOC Code": "string",
            "Title": "string",
            "Description": "string",
        },
    )

    return df


def clean_onet(df):
    """
    Clean O*NET Occupation Data according to the predefined rules.

    Rules:
    1. Preserve the full O*NET-SOC Code as text.
    2. Derive a separate six-digit SOC code for BLS matching.
    3. Do not deduplicate solely on the derived six-digit SOC code.
    """

    cleaned = df.copy()

    # --------------------------------------------------
    # Rule 1: Preserve full O*NET-SOC code as text
    # --------------------------------------------------

    cleaned["O*NET-SOC Code"] = (
        cleaned["O*NET-SOC Code"]
        .astype("string")
        .str.strip()
    )

    cleaned["Title"] = (
        cleaned["Title"]
        .astype("string")
        .str.strip()
    )

    cleaned["Description"] = (
        cleaned["Description"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------
    # Rule 2: Derive six-digit SOC code for BLS matching
    # Example:
    # 11-1011.00 -> 11-1011
    # --------------------------------------------------

    cleaned["SOC6"] = (
        cleaned["O*NET-SOC Code"]
        .str.extract(r"^(\d{2}-\d{4})", expand=False)
        .astype("string")
    )

    # --------------------------------------------------
    # Rule 3:
    # Do NOT drop duplicates on SOC6.
    # Repeated SOC6 values are retained for later review.
    # --------------------------------------------------

    return cleaned


def audit_onet(raw, cleaned):
    """
    Return O*NET cleaning and verification results for display
    in the audit notebook.
    """

    # Full-code duplicate check
    duplicate_full_codes = raw[
        "O*NET-SOC Code"
    ].duplicated().sum()

    # Derived SOC6 repeated values
    repeated_soc6_rows = cleaned[
        "SOC6"
    ].duplicated(
        keep=False
    ).sum()

    repeated_soc6_codes = cleaned.loc[
        cleaned["SOC6"].duplicated(keep=False),
        "SOC6"
    ].nunique()

    # Format validation
    invalid_full_codes = (
        ~cleaned["O*NET-SOC Code"]
        .str.match(
            SOC_FULL_PATTERN,
            na=False,
        )
    ).sum()

    invalid_soc6_codes = (
        ~cleaned["SOC6"]
        .str.match(
            SOC6_PATTERN,
            na=False,
        )
    ).sum()

    # Missing values
    missing_values = (
        cleaned.isna()
        .sum()
        .rename("missing_count")
        .to_frame()
    )

    # Repeated SOC6 detail
    repeated_soc6_detail = (
        cleaned[
            cleaned["SOC6"]
            .duplicated(keep=False)
        ][
            [
                "SOC6",
                "O*NET-SOC Code",
                "Title",
            ]
        ]
        .sort_values(
            [
                "SOC6",
                "O*NET-SOC Code",
            ]
        )
        .reset_index(drop=True)
    )

    audit = {
        "raw_rows": len(raw),
        "raw_columns": raw.shape[1],

        "cleaned_rows": len(cleaned),
        "cleaned_columns": cleaned.shape[1],

        "exact_duplicates": cleaned.duplicated().sum(),

        "duplicate_full_codes": duplicate_full_codes,

        "invalid_full_codes": invalid_full_codes,
        "invalid_soc6_codes": invalid_soc6_codes,

        "unique_full_codes": cleaned[
            "O*NET-SOC Code"
        ].nunique(),

        "unique_soc6_codes": cleaned[
            "SOC6"
        ].nunique(),

        "repeated_soc6_rows": repeated_soc6_rows,
        "repeated_soc6_codes": repeated_soc6_codes,

        "missing_values": missing_values,

        "repeated_soc6_detail": repeated_soc6_detail,
    }

    return audit