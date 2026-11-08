"""Copy the canonical standalone dashboard to a requested location."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="AI_Workforce_Investment_Planner.html")
    args = parser.parse_args()
    source = Path(__file__).with_name("AI_Workforce_Investment_Planner.html")
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output != source.resolve():
        output.write_bytes(source.read_bytes())
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
