# AI Workforce Investment Planner - data cleaning

This branch contains Yunyi Zhang's individual Module 6 project-data-cleaning work. The pipeline creates an analysis table at the grain of one metropolitan or nonmetropolitan area by six-digit SOC occupation. It combines a state-occupation Claude usage signal with local BLS workforce measures.

## Submission reference

- Student: Yunyi Zhang
- Branch: `yoona-zhang`
- Branch URL: https://github.com/Hardcore-LEO/dso576-project/tree/yoona-zhang
- Validated cleaning commit ID: `af4172162db67e9ce66fc537a012a28200619039`

This commit contains the tested cleaning workflow, notebook, sample, audit, record checks, dependencies, and documentation. Do not merge this homework branch into `main`.

## Source data and versions

The raw files are not committed. Place these four unchanged files in one local directory:

| Source | Version / file |
| --- | --- |
| Anthropic Economic Index | `aei_claude_ai_2026-06-26.csv`, June 26, 2026 release |
| O\*NET | `Occupation Data (1).xlsx`, O\*NET 31.0 Occupation Data |
| BLS OEWS metropolitan areas | `MSA_M2025_dl.xlsx`, May 2025 |
| BLS OEWS nonmetropolitan areas | `BOS_M2025_dl.xlsx`, May 2025 |

The cleaning script checks that all four filenames exist and reads them without modifying them.

## Environment

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync --frozen
```

Dependencies are pinned in `pyproject.toml` and `uv.lock`. They include pandas 2.2.3 and openpyxl 3.1.5.

## Run instructions

From the repository root, replace the data path with the directory containing the four files:

```bash
uv run python src/clean_project_data.py \
  --data-dir "/absolute/path/to/Data" \
  --output-root .
```

The command was tested on the full source data. It produced:

- 7,294 filtered Anthropic state-occupation rows;
- 6,607 state by six-digit SOC AI rows;
- 186,557 detailed BLS area-occupation rows;
- 49,866 matched BLS-AI rows and 136,691 BLS rows without a published AI match;
- 50 review-sample rows; and
- five passing original/expected/actual record checks.

To review the same workflow interactively, open `notebooks/project_data_cleaning.ipynb` in VS Code, select the repository `.venv`, set the `DSO576_DATA_DIR` environment variable, and run all cells from a restarted kernel. The Python script is the authoritative pipeline; the notebook runs it and displays the submitted checks.

## Expected output files

| File | Purpose | Git status |
| --- | --- | --- |
| `data/processed/ai_state_soc6.csv` | One row per state and six-digit SOC | Recreated locally; ignored because it is large |
| `data/processed/area_occupation_clean.csv` | One row per area and six-digit SOC | Recreated locally; ignored because it is large |
| `data/sample/area_occupation_sample.csv` | At most 50 difficult cases | Submitted |
| `reports/cleaning_audit.json` | Counts, missingness, duplicates, ranges, and merge checks | Submitted |
| `reports/record_checks.csv` | Five original/expected/actual checks | Submitted |

## Sample selection

The sample is deterministic and capped at 50 unique area-occupation rows. It prioritizes suppressed employment, top-coded wages, BLS rows without a published AI match, multistate MSAs, matched nonmetropolitan rows, matched metropolitan rows, and the five manually specified record-check cases. The submitted sample contains both area types, 29 matched rows, 21 unmatched rows, 9 suppressed-employment rows, 8 top-coded-wage rows, and 9 multistate-MSA rows.

## Important interpretation limits

- `claude_usage_pct` is a share of observed Claude usage, not a worker adoption rate or a causal exposure measure.
- Missing Anthropic state-occupation combinations remain missing; they are not filled with zero.
- Every BLS area in a state receives the same state-occupation AI value.
- A multistate MSA uses `PRIM_STATE` for the state-level AI join and is flagged as an approximation.
- BLS `**` and `*` values remain missing with explicit flags; `#` is retained as a top-coded wage flag without inventing an exact wage.

See `plan.md`, `cleaning_decision_log.md`, `reports/cleaning_audit.json`, and `reports/record_checks.csv` for the full decisions and evidence.
