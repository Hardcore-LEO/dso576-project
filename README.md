# DSO 576 dataset cleaning

This folder contains the four source-specific cleaning/validation scripts, a notebook
entry point, a BLS workbook merge utility, and the cleaned dataset copies in
[`cleaned/`](./cleaned/). [`cleaned_sample.csv`](./cleaned_sample.csv) contains the
first 100 data rows from the BOS workbook for quick inspection.

## Datasets and cleaning decisions

- **Anthropic AI activity:** CSV rows are streamed, text fields are trimmed, and exact
  duplicate rows are removed. The script uses a temporary SQLite index so the large
  CSV does not need to fit in memory.
- **BLS OEWS:** the BOS and MSA workbook sheets are checked for duplicate rows,
  malformed records, and boundary whitespace. The current inputs need no changes, so
  the workbooks are copied byte-for-byte to preserve every worksheet and workbook
  feature. If a data change is detected, the script stops and asks for review rather
  than silently rewriting workbook contents.
- **O*NET occupations:** the occupation sheet is validated, then copied unchanged
  where it already passes the conservative checks.
- **Merge:** `merge_data.py` appends the BOS and MSA data sheets to a single CSV and
  adds `SOURCE_WORKBOOK`; it does not join occupation records to the AI activity
  dataset because there is no single verified, lossless join key for every AI metric.

Blank BLS fields and markers such as `*`, `**`, `#`, and `TRUE` are meaningful source
values and are deliberately retained. See [`cleaned/cleaning_report.md`](./cleaned/cleaning_report.md)
for the profile and row counts.

## Run

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Pass the directory holding the original source files to each cleaner. Outputs default
to this project's `cleaned` folder:

```powershell
python clean_anthropic.py "E:\USC Marshall\DSO 576\Project\dataset to clean\aei_claude_ai_2026-06-26.csv"
python clean_bls.py "E:\USC Marshall\DSO 576\Project\dataset to clean"
python clean_onet.py "E:\USC Marshall\DSO 576\Project\dataset to clean\Occupation Data.xlsx"
python merge_data.py
```

The source location can be changed on each command. Cleaning never overwrites the
source files.
