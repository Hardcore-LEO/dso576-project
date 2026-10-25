# Module 6 - Project Data Cleaning

**Project:** AI Workforce Investment  
**Student:** Qiyue Zhao  
**GitHub branch:** `Qiyue-Zhao`  
**Branch URL:** https://github.com/Hardcore-LEO/dso576-project/tree/Qiyue-Zhao  
**Commit ID:** 5cc879a  

## Overview

This folder contains my individual Module 6 data-cleaning work for the DSO 576 group project.

The workflow cleans and verifies occupation-level AI-use, employment/wage, and occupation-reference data, then integrates the cleaned sources using harmonized occupation codes.

## Files

- `clean_anthropic.py` - functions to load, clean, and audit the Anthropic data.
- `clean_bls.py` - functions to load, clean, combine, and audit BLS metropolitan and nonmetropolitan OEWS data.
- `clean_onet.py` - functions to load, clean, and audit O*NET Occupation Data and derive a six-digit SOC key.
- `merge_data.py` - functions to merge the cleaned sources and audit merge results.
- `DataCleaning.ipynb` - full inspection, cleaning, verification, record checks, and reproducibility workflow.
- `cleaned_sample.csv` - up to 50 cleaned rows selected to include both typical and difficult cases.
- `requirements.txt` - Python package dependencies.

## Data Sources

The original source files are not included in this GitHub folder.

1. **Anthropic Economic Index**
   - File: `aei_claude_ai_2026-06-26.csv`
   - Release/version: June 26, 2026
   - Used for occupation-level Claude.ai usage, augmentation, automation, and autonomy metrics.

2. **U.S. Bureau of Labor Statistics (BLS) - Occupational Employment and Wage Statistics (OEWS)**
   - Files:
     - `MSA_M2025_dl.xlsx`
     - `BOS_M2025_dl.xlsx`
   - Version: May 2025
   - Used for California metropolitan and nonmetropolitan employment and wage estimates by detailed occupation.

3. **O*NET Occupation Data**
   - File: `Occupation Data.xlsx`
   - Version: O*NET 31.0
   - Used as the occupation reference table and for occupation-code harmonization.

## Expected Raw-Data Location

To reproduce the notebook, place the four original source files in the same directory as `DataCleaning.ipynb`:

```text
aei_claude_ai_2026-06-26.csv
MSA_M2025_dl.xlsx
BOS_M2025_dl.xlsx
Occupation Data.xlsx
```

The cleaning scripts do not overwrite the original source files.

## Setup

Python 3 is required.

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Run Instructions

1. Place the four original source files in the same folder as the notebook.
2. Open `DataCleaning.ipynb`.
3. Restart the notebook kernel.
4. Run all cells from top to bottom.

The notebook imports and uses the functions defined in the four Python scripts.

## Expected Outputs

Running the notebook creates a `cleaned_output` folder containing:

```text
cleaned_output/
├── anthropic_clean.csv
├── bls_clean.csv
├── onet_clean.csv
├── integrated_long.csv
└── cleaned_sample.csv
```

Expected row counts from the submitted cleaning workflow:

- `anthropic_clean.csv`: 5,121 rows
- `bls_clean.csv`: 11,847 rows
- `onet_clean.csv`: 1,016 rows
- `integrated_long.csv`: 67,194 rows

The notebook also checks duplicate keys, missing values, BLS special-value handling, occupation-code formats, unmatched merge keys, merge row expansion, and five individual records.

## Cleaned Sample

`cleaned_sample.csv` contains no more than 50 rows. The sample was selected deliberately to include typical and difficult cases, including:

- normal metropolitan records,
- normal nonmetropolitan records,
- unavailable BLS employment values,
- BLS high-wage flags, and
- records without an Anthropic match.

## Reproducibility

Before submission, I restarted the kernel and ran the notebook from the original source files. The workflow is designed to recreate the submitted cleaned outputs and validation results.

The final Git commit ID used for submission should be added at the top of this README and in the submitted PDF.
