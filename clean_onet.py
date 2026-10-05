"""Validate and copy the O*NET occupation workbook without changing its schema."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from openpyxl import load_workbook


def validate_and_copy(input_path: Path, output_path: Path) -> dict[str, int]:
    workbook = load_workbook(input_path, read_only=True, data_only=False)
    try:
        if "Occupation Data" not in workbook.sheetnames:
            raise ValueError(f"{input_path} has no 'Occupation Data' sheet.")
        rows = workbook["Occupation Data"].iter_rows(values_only=True)
        header = next(rows, None)
        if header != ("O*NET-SOC Code", "Title", "Description"):
            raise ValueError(f"Unexpected occupation-data header: {header!r}")
        seen: set[bytes] = set()
        duplicate_rows = trimmed_cells = data_rows = 0
        for row in rows:
            if len(row) != len(header):
                raise ValueError("Occupation Data contains a malformed row.")
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
                f"Occupation Data needs {trimmed_cells} whitespace normalizations and "
                f"{duplicate_rows} duplicate removals; review before rewriting workbook."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, output_path)
        return {"rows": data_rows, "duplicates_removed": duplicate_rows, "trimmed_cells": trimmed_cells}
    finally:
        workbook.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="O*NET occupation workbook")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "cleaned" / "Occupation Data.xlsx",
    )
    args = parser.parse_args()
    print(validate_and_copy(args.input, args.output))


if __name__ == "__main__":
    main()
