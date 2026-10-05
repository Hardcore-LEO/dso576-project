"""Stream-clean the AI activity CSV without loading the entire dataset in memory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def clean(input_path: Path, output_path: Path) -> dict[str, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    trimmed_cells = duplicates = rows_written = 0
    fd, temporary_output = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(fd)
    try:
        with tempfile.TemporaryDirectory(prefix="anthropic-clean-") as temp_dir:
            with closing(sqlite3.connect(Path(temp_dir) / "seen.sqlite3")) as seen:
                with seen:
                    seen.execute("CREATE TABLE hashes (digest BLOB PRIMARY KEY) WITHOUT ROWID")
                    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
                        reader = csv.reader(source)
                        try:
                            header = next(reader)
                        except StopIteration as exc:
                            raise ValueError(f"Input CSV is empty: {input_path}") from exc

                        with open(temporary_output, "w", encoding="utf-8", newline="") as target:
                            writer = csv.writer(target)
                            writer.writerow(header)
                            for line_number, row in enumerate(reader, start=2):
                                if len(row) != len(header):
                                    raise ValueError(
                                        f"Row {line_number} has {len(row)} fields; expected {len(header)}."
                                    )
                                normalized = [value.strip() for value in row]
                                trimmed_cells += sum(a != b for a, b in zip(row, normalized))
                                digest = hashlib.sha256(
                                    json.dumps(
                                        normalized, ensure_ascii=False, separators=(",", ":")
                                    ).encode("utf-8")
                                ).digest()
                                try:
                                    seen.execute("INSERT INTO hashes VALUES (?)", (digest,))
                                except sqlite3.IntegrityError:
                                    duplicates += 1
                                    continue
                                writer.writerow(normalized)
                                rows_written += 1
        os.replace(temporary_output, output_path)
    except Exception:
        Path(temporary_output).unlink(missing_ok=True)
        raise
    return {
        "rows_written": rows_written,
        "duplicates_removed": duplicates,
        "trimmed_cells": trimmed_cells,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source AI activity CSV")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "cleaned" / "aei_claude_ai_2026-06-26.csv",
    )
    args = parser.parse_args()
    print(clean(args.input, args.output))


if __name__ == "__main__":
    main()
