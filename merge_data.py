"""Combine BOS and MSA OEWS rows into one CSV with a source-workbook column."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from openpyxl import load_workbook


SHEETS = ("BOS_M2025_dl", "MSA_M2025_dl")


def merge(cleaned_dir: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_workbooks = [
        (cleaned_dir / f"{sheet}.xlsx", sheet)
        for sheet in SHEETS
    ]
    row_count = 0
    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        expected_header = None
        for workbook_path, sheet_name in source_workbooks:
            workbook = load_workbook(workbook_path, read_only=True, data_only=True)
            try:
                if sheet_name not in workbook.sheetnames:
                    raise ValueError(f"{workbook_path} is missing sheet {sheet_name!r}.")
                rows = workbook[sheet_name].iter_rows(values_only=True)
                header = next(rows, None)
                if header is None:
                    raise ValueError(f"{workbook_path}:{sheet_name} is empty.")
                if expected_header is None:
                    expected_header = tuple(header)
                    writer.writerow((*expected_header, "SOURCE_WORKBOOK"))
                elif tuple(header) != expected_header:
                    raise ValueError(f"{workbook_path}:{sheet_name} has a different column layout.")
                for row in rows:
                    if all(value is None for value in row):
                        continue
                    if len(row) != len(expected_header):
                        raise ValueError(f"{workbook_path}:{sheet_name} contains a malformed row.")
                    writer.writerow((*row, workbook_path.name))
                    row_count += 1
            finally:
                workbook.close()
    return row_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cleaned-dir", type=Path, default=Path(__file__).parent / "cleaned"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "cleaned" / "bls_combined.csv",
    )
    args = parser.parse_args()
    print({"rows_merged": merge(args.cleaned_dir, args.output)})


if __name__ == "__main__":
    main()
