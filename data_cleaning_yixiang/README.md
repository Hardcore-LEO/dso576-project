# Module 6 - Yixiang Lu

AI Workforce Investment Planner, **Vision A: California workforce**.
Individual cleaning work prepared with Codex assistance on branch `yixiang-lu`.
Read the pre-implementation choices in [cleaning_plan.md](cleaning_plan.md).
The student remains responsible for reviewing those choices and explaining the results.

## Scope and meaning

The main table contains one California OEWS area x detailed occupation. It retains
all BLS source columns plus raw numeric values, source record references, and
explicitly provisional California-wide Claude occupation-use context. It supports
descriptive comparisons of published employment, median annual wages, and AI use.
It does not compute exposure, local adoption, training ROI, or an investment score.

Two AEI occupation tables are combined with product identifiers; selected scopes
are CA, USA, GLOBAL for Claude.ai and GLOBAL for API, both April and May 2026,
all occupation metrics and both hierarchy levels. Four Signals context tables are
cleaned separately. Their different denominators/geographies must not be pooled.

## Obtain and preserve the originals

Download the original files from these sources, preserving this layout under a
folder such as `raw/`. The local submission used already-downloaded originals;
their original retrieval dates are unknown. SHA-256 hashes and sizes in
`outputs/evidence/source_manifest.json` identify the exact versions inspected on
October 4, 2026. Compare downloaded hashes before claiming identical reproduction.

```text
raw/
  2026-06-26/
    aei_claude_ai_2026-06-26.csv
    aei_1p_api_2026-06-26.csv
  oesm25ma.zip
  data-download-csv/public_release_csv/
    usa_share_of_messages_by_onet_iwa_month.csv
    usa_share_of_work_related_messages_by_onet_iwa_month.csv
    usa_share_of_messages_by_state_2025_rank.csv
    usa_share_of_messages_by_topic_state_2025.csv
```

- [Anthropic June 26, 2026 release](https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main/release_2026_06_26): download both CSVs from its data folder. [Schema and definitions](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2026_06_26/data_documentation.md). Attribution: Massenkoff et al., *Anthropic Economic Index report: Cadences*, June 26, 2026; data CC-BY. API excludes Claude Code; absent cells may reflect publication thresholds.
- [BLS May 2025 metro/nonmetro ZIP](https://www.bls.gov/oes/special.requests/oesm25ma.zip): keep the ZIP intact. The script reads both XLSX files directly; `file_descriptions.xlsx` documents the workbook contents. Attribution: U.S. Bureau of Labor Statistics, May 2025 OEWS.
- [OpenAI Signals download](https://openai.com/signals/data-download/): use the v2.0 package and retain its README.pdf. Copy the four CSVs above; do not use the `__MACOSX` metadata files. Attribution: OpenAI Signals. Shares are fractions; rare IWAs include `Other IWA`. Preserve source attribution and consult the package's terms when redistributing.

Originals are ignored by Git. They are never edited by these scripts. The complete
cleaned outputs can be recreated from these sources; the local submission ZIP
also includes them. The GitHub sample contains public aggregate data only.

## Environment and exact commands

Python 3.11 is the tested version. From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe clean_data.py --source-root "raw" --output-dir "outputs"
.\.venv\Scripts\python.exe validate_data.py --source-root "raw" --output-dir "outputs"
```

On the original computer, substitute `E:\USC Marshall\DSO 576\Project` for `raw`.
Allow several minutes for the original workbook scans and full-file checks.
No spreadsheet editing is needed. A schema/key/parse assertion failure stops the
run; investigate the input rather than disabling the assertion.

The submitted evidence was produced with Python 3.11, pandas 2.2.3 and openpyxl
3.1.5. `requirements.txt` pins direct dependencies; `requirements-lock.txt` records
the exact installed transitive environment used for the submission.
For exact Windows dependency versions, install with `-r requirements-lock.txt`
instead of `-r requirements.txt`.

### Notebook

Open `cleaning.ipynb` in VS Code and select this environment's Python kernel.
Set `DSO576_SOURCE_ROOT` before starting VS Code/Jupyter, or place originals under
`raw/`. Then **Restart Kernel and Run All**. The notebook runs both the full
cleaning and independent validation; its outputs are saved in the submitted copy.
`DSO576_OUTPUT_DIR` optionally selects a separate output directory.

For a second independent process run:

```powershell
.\.venv\Scripts\python.exe clean_data.py --source-root "raw" --output-dir "outputs/repeat"
.\.venv\Scripts\python.exe verify_reproduction.py
```

`verify_reproduction.py` compares the complete cleaned-file hash manifests and
sample across runs; it does not infer notebook execution. Fresh-kernel execution
evidence in the submitted JSON was recorded separately after that execution.

## Outputs and evidence

- `outputs/cleaned/`: `bls_ca_occupations.csv`, `anthropic_occupations.csv`,
  four cleaned Signals files, `ca_claude_soc_prefix.csv`, `ca_workforce_context.csv`.
- `outputs/cleaned_sample.csv`: 50 rows, every joined column, difficult cases first
  followed by sorted AREA/OCC_CODE. See `sample_selection.json`. Not representative.
- `outputs/evidence/full_data_checks.json`: full-source profiles, distinct duplicate
  checks, conversion counts, missing markers, exclusions, range flags and merge counts.
- `outputs/evidence/independent_validation.json`: independent original-to-output
  comparison for every BLS row/numeric column and every AI join value; five examples.
- `outputs/evidence/area_metric_support.csv`: counts supporting each area metric.
- `outputs/evidence/unmatched_*.csv`: both sides of the unmatched join.
- Source/output hashes, environment, sample selection and reproduction evidence
  are also under `outputs/evidence/`.
- `outputs/module6_individual_report.pdf`: all 14 checklist responses, decision log,
  five record checks and Codex verification; prepared for team reconciliation.

## Interpretation limits and final team step

The occupation-prefix mapping is **provisional**. Verify an official taxonomy
crosswalk before using the join for decisions. Unmatched Claude shares remain
missing; the state-level share is repeated across areas and must not be summed
over them. Source dates differ. BLS published employment sums exclude suppressed
cells. Average occupation median wages are unweighted, not employee-level medians.
These public aggregate data cannot prove training benefit, adoption or job loss.

Each team member must publish their independent work on their own branch.
Reconcile the members' rules and results before approving the group report.
See `team_reconciliation.md` for an initial comparison against Qiyue's published
branch, prepared after this independent implementation and validation.
The homework mentions both a ZIP bundle and a group checklist PDF for Gradescope;
this work prepares both locally, but does not claim a Gradescope upload or team
agreement. Do not merge this personal branch into main automatically.
