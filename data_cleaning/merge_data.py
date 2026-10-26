import pandas as pd


# --------------------------------------------------
# Prepare O*NET reference tables
# --------------------------------------------------

def prepare_onet_maps(onet_clean):
    """
    Prepare two O*NET reference tables:

    1. full_map:
       Used for Anthropic -> O*NET exact matching on full O*NET-SOC Code.

    2. base_map:
       Used for BLS -> O*NET matching.
       Only .00 base occupations are retained so each SOC6 maps
       to at most one O*NET occupation.
    """

    full_map = (
        onet_clean[
            [
                "O*NET-SOC Code",
                "SOC6",
                "Title",
                "Description",
            ]
        ]
        .copy()
        .rename(
            columns={
                "Title": "onet_title",
                "Description": "onet_description",
            }
        )
    )

    base_map = (
        full_map[
            full_map["O*NET-SOC Code"].str.endswith(
                ".00",
                na=False,
            )
        ]
        .copy()
    )

    # SOC6 must be unique in the base map
    if base_map["SOC6"].duplicated().any():
        raise ValueError(
            "O*NET base map contains repeated SOC6 values."
        )

    return full_map, base_map


# --------------------------------------------------
# Anthropic -> O*NET
# --------------------------------------------------

def merge_anthropic_onet(
    anthropic_clean,
    onet_clean,
):
    """
    Match Anthropic occupation records to O*NET using the
    full O*NET-SOC occupation code.

    Expected relationship:
    many Anthropic observations -> one O*NET occupation.
    """

    full_map, _ = prepare_onet_maps(
        onet_clean
    )

    merged = anthropic_clean.merge(
        full_map,
        how="left",
        left_on="node_external_id",
        right_on="O*NET-SOC Code",
        validate="many_to_one",
        indicator="_anthropic_onet_merge",
    )

    return merged


# --------------------------------------------------
# BLS -> O*NET
# --------------------------------------------------

def merge_bls_onet(
    bls_clean,
    onet_clean,
):
    """
    Match BLS occupations to O*NET base occupations.

    BLS uses six-digit SOC codes, while O*NET includes
    extensions such as .00 and .03.

    Only O*NET .00 base occupations are used for direct
    BLS matching to prevent one-to-many row expansion.

    Expected relationship:
    many BLS area-occupation rows -> one O*NET base occupation.
    """

    _, base_map = prepare_onet_maps(
        onet_clean
    )

    merged = bls_clean.merge(
        base_map,
        how="left",
        left_on="OCC_CODE",
        right_on="SOC6",
        validate="many_to_one",
        indicator="_bls_onet_merge",
    )

    return merged


# --------------------------------------------------
# Prepare Anthropic records that can map directly
# to BLS six-digit occupations
# --------------------------------------------------

def prepare_anthropic_for_bls(
    anthropic_onet,
):
    """
    Keep Anthropic observations associated with O*NET .00
    base occupations for direct BLS matching.

    The result remains long-format:
    one SOC6 x month x metric observation.
    """

    direct = anthropic_onet[
        anthropic_onet[
            "O*NET-SOC Code"
        ].str.endswith(
            ".00",
            na=False,
        )
    ].copy()

    keep_cols = [
        "SOC6",
        "O*NET-SOC Code",
        "onet_title",
        "date_start",
        "date_end",
        "geo_id",
        "geo_level",
        "metric_id",
        "value",
    ]

    direct = direct[
        keep_cols
    ].copy()

    return direct


# --------------------------------------------------
# BLS -> Anthropic
# --------------------------------------------------

def merge_bls_anthropic(
    bls_onet,
    anthropic_onet,
):
    """
    Merge BLS area-occupation records with Anthropic
    occupation-level observations using SOC6.

    Because Anthropic remains in long format, one BLS
    area-occupation record may match multiple month/metric rows.

    Expected output grain:
    AREA x OCC_CODE x date x geography x metric
    """

    anthropic_direct = (
        prepare_anthropic_for_bls(
            anthropic_onet
        )
    )

    merged = bls_onet.merge(
        anthropic_direct,
        how="left",
        left_on="OCC_CODE",
        right_on="SOC6",
        validate="many_to_many",
        indicator="_bls_anthropic_merge",
        suffixes=(
            "_bls",
            "_anthropic",
        ),
    )

    return merged


# --------------------------------------------------
# Complete integration pipeline
# --------------------------------------------------

def merge_datasets(
    anthropic_clean,
    bls_clean,
    onet_clean,
):
    """
    Run the complete occupation-matching workflow.

    Returns:
        anthropic_onet
        bls_onet
        integrated_long
    """

    anthropic_onet = merge_anthropic_onet(
        anthropic_clean,
        onet_clean,
    )

    bls_onet = merge_bls_onet(
        bls_clean,
        onet_clean,
    )

    integrated_long = merge_bls_anthropic(
        bls_onet,
        anthropic_onet,
    )

    return (
        anthropic_onet,
        bls_onet,
        integrated_long,
    )


# --------------------------------------------------
# Merge audit
# --------------------------------------------------

def audit_merge(
    anthropic_clean,
    bls_clean,
    anthropic_onet,
    bls_onet,
    integrated_long,
):
    """
    Return merge-verification evidence for display
    in the notebook.
    """

    # ----------------------------------------------
    # Anthropic -> O*NET
    # ----------------------------------------------

    anthropic_match_counts = (
        anthropic_onet[
            "_anthropic_onet_merge"
        ]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="rows")
    )

    anthropic_unmatched = (
        anthropic_onet[
            anthropic_onet[
                "_anthropic_onet_merge"
            ] == "left_only"
        ][
            [
                "node_external_id",
                "node_name",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "node_external_id"
        )
        .reset_index(drop=True)
    )

    # ----------------------------------------------
    # BLS -> O*NET
    # ----------------------------------------------

    bls_match_counts = (
        bls_onet[
            "_bls_onet_merge"
        ]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="rows")
    )

    bls_unmatched = (
        bls_onet[
            bls_onet[
                "_bls_onet_merge"
            ] == "left_only"
        ][
            [
                "OCC_CODE",
                "OCC_TITLE",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "OCC_CODE"
        )
        .reset_index(drop=True)
    )

    # ----------------------------------------------
    # BLS -> Anthropic
    # ----------------------------------------------

    bls_anthropic_match_counts = (
        integrated_long[
            "_bls_anthropic_merge"
        ]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="rows")
    )

    bls_without_anthropic = (
        integrated_long[
            integrated_long[
                "_bls_anthropic_merge"
            ] == "left_only"
        ][
            [
                "AREA",
                "AREA_TITLE",
                "OCC_CODE",
                "OCC_TITLE",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # ----------------------------------------------
    # Row-count checks
    # ----------------------------------------------

    row_counts = pd.DataFrame({
        "Stage": [
            "Clean Anthropic",
            "Anthropic after O*NET merge",
            "Clean BLS",
            "BLS after O*NET merge",
            "Integrated long table",
        ],
        "Rows": [
            len(anthropic_clean),
            len(anthropic_onet),
            len(bls_clean),
            len(bls_onet),
            len(integrated_long),
        ],
    })

    # O*NET reference joins should NOT expand rows
    anthropic_onet_expansion = (
        len(anthropic_onet)
        - len(anthropic_clean)
    )

    bls_onet_expansion = (
        len(bls_onet)
        - len(bls_clean)
    )

    # ----------------------------------------------
    # Key checks
    # ----------------------------------------------

    bls_key_duplicates_after_onet = (
        bls_onet.duplicated(
            subset=[
                "AREA",
                "OCC_CODE",
            ]
        ).sum()
    )

    integrated_key = [
        "AREA",
        "OCC_CODE",
        "date_start",
        "date_end",
        "geo_id",
        "geo_level",
        "metric_id",
    ]

    integrated_duplicate_keys = (
        integrated_long[
            integrated_long["metric_id"].notna()
        ]
        .duplicated(
            subset=integrated_key
        )
        .sum()
    )

    audit = {
        "row_counts": row_counts,

        "anthropic_match_counts":
            anthropic_match_counts,

        "anthropic_unmatched":
            anthropic_unmatched,

        "bls_match_counts":
            bls_match_counts,

        "bls_unmatched":
            bls_unmatched,

        "bls_anthropic_match_counts":
            bls_anthropic_match_counts,

        "bls_without_anthropic":
            bls_without_anthropic,

        "anthropic_onet_row_expansion":
            anthropic_onet_expansion,

        "bls_onet_row_expansion":
            bls_onet_expansion,

        "bls_key_duplicates_after_onet":
            bls_key_duplicates_after_onet,

        "integrated_duplicate_keys":
            integrated_duplicate_keys,
    }

    return audit