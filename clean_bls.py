"""Validate and copy the two OEWS workbooks while retaining all source sheets."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from openpyxl import load_workbook


WORKBOOKS = {
    "BOS_M2025_dl.xlsx": "BOS_M2025_dl",
    "MSA_M2025_dl.xlsx": "MSA_M2025_dl",
}


def validate_and_copy(source_dir: Path, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for filename, data_sheet in WORKBOOKS.items():
        source_path = source_dir / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        workbook = load_workbook(source_path, read_only=True, data_only=False)
        try:
            if data_sheet not in workbook.sheetnames:
                raise ValueError(f"{filename} is missing its expected sheet {data_sheet!r}.")
            sheet = workbook[data_sheet]
            rows = sheet.iter_rows(values_only=True)
            header = next(rows, None)
            if header is None:
                raise ValueError(f"{filename}:{data_sheet} has no header row.")
            seen: set[bytes] = set()
            duplicate_rows = trimmed_cells = data_rows = 0
            for row in rows:
                if all(value is None for value in row):
                    continue
                if len(row) != len(header):
                    raise ValueError(f"{filename}:{data_sheet} contains a malformed row.")
                normalized = tuple(value.strip() if isinstance(value, str) else value for value in row)
                trimmed_cells += sum(
                    isinstance(value, str) and value != normalized[index]
                    for index, value in enumerate(row)
                )
                digest = hashlib.sha256(repr(normalized).encode("utf-8")).digest()
                if digest in seen:
                    duplicate_rows += 1
                else:
                    seen.add(digest)
                data_rows += 1
            if trimmed_cells or duplicate_rows:
                raise ValueError(
                    f"{filename} needs {trimmed_cells} whitespace normalizations and "
                    f"{duplicate_rows} duplicate removals; review before rewriting workbook sheets."
                )
            shutil.copy2(source_path, output_dir / filename)
            summary[filename] = data_rows
        finally:
            workbook.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Folder containing the BOS and MSA workbooks")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "cleaned")
    args = parser.parse_args()
    print(validate_and_copy(args.source_dir, args.output_dir))


if __name__ == "__main__":
    main()
