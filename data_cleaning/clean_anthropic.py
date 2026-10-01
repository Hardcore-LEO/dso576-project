import pandas as pd


GLOBAL_METRICS = [
    "ai_autonomy_mean",
    "collaboration_bucket_augmentation_pct",
    "collaboration_bucket_automation_pct",
]

SOC_PATTERN = r"^\d{2}-\d{4}\.\d{2}$"


def load_anthropic(path):
    """
    Load the original Anthropic Economic Index data.
    Preserve node_external_id as text.
    """
    df = pd.read_csv(
        path,
        dtype={"node_external_id": "string"},
    )

    return df


def clean_anthropic(df):
    """
    Clean the Anthropic data according to the predefined project rules.

    Rules:
    1. Keep detailed occupation records only.
    2. Keep project-relevant geography/metric combinations only.
    3. Preserve the full O*NET-SOC code as text.
    """

    # Work on a copy so the original DataFrame is not modified
    df = df.copy()

    # --------------------------------------------------
    # Rule 1: Keep detailed occupation records
    # --------------------------------------------------

    occupation = df[
        (df["category_name"] == "soc_occupation")
        & (df["hierarchy_level"] == 0)
    ].copy()

    # --------------------------------------------------
    # Rule 2: Keep project-relevant metrics/geographies
    # --------------------------------------------------

    # Global occupation-level AI measures
    global_data = occupation[
        (occupation["geo_level"] == "global")
        & (occupation["metric_id"].isin(GLOBAL_METRICS))
    ].copy()

    # California occupation-level Claude.ai usage share
    california_data = occupation[
        (occupation["geo_level"] == "subregion")
        & (occupation["geo_id"] == "US-CA")
        & (occupation["metric_id"] == "pct")
    ].copy()

    cleaned = pd.concat(
        [global_data, california_data],
        ignore_index=True,
    )

    # --------------------------------------------------
    # Rule 3: Preserve full O*NET-SOC code as text
    # --------------------------------------------------

    cleaned["node_external_id"] = (
        cleaned["node_external_id"].astype("string")
    )

    return cleaned


def audit_anthropic(raw, cleaned):
    """
    Return cleaning and verification results for display
    in the audit notebook.
    """

    # Detailed occupation subset before metric filtering
    occupation = raw[
        (raw["category_name"] == "soc_occupation")
        & (raw["hierarchy_level"] == 0)
    ].copy()

    candidate_key = [
        "date_start",
        "date_end",
        "geo_id",
        "geo_level",
        "metric_id",
        "node_external_id",
    ]

    audit = {
        "raw_rows": len(raw),
        "raw_columns": raw.shape[1],

        "occupation_rows": len(occupation),

        "cleaned_rows": len(cleaned),
        "cleaned_columns": cleaned.shape[1],

        "exact_duplicates": cleaned.duplicated().sum(),

        "repeated_candidate_keys": cleaned.duplicated(
            subset=candidate_key
        ).sum(),

        "invalid_soc_codes": (
            ~cleaned["node_external_id"]
            .str.match(SOC_PATTERN, na=False)
        ).sum(),

        "unique_occupations": cleaned[
            "node_external_id"
        ].nunique(),

        "missing_values": cleaned.isna().sum(),

        "metric_combinations": (
            cleaned.groupby(
                ["geo_level", "geo_id", "metric_id"],
                dropna=False,
            )
            .size()
            .rename("rows")
            .reset_index()
        ),

        "rows_by_period": (
            cleaned.groupby(
                ["date_start", "date_end", "geo_level", "metric_id"],
                dropna=False,
            )
            .size()
            .rename("rows")
            .reset_index()
        ),
    }

    return audit