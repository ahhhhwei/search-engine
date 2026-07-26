#!/usr/bin/env python3
"""Convert the existing C++ parser output (Crawler/raw.txt) to web JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SEPARATOR = "\x03"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Crawler/raw.txt", help="parser output path")
    parser.add_argument(
        "--output", default="web/data/documents.json", help="JSON output path"
    )
    parser.add_argument("--limit", type=int, default=0, help="0 means no limit")
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_file():
        raise SystemExit(f"input file does not exist: {input_path}")

    documents: list[dict[str, str]] = []
    with input_path.open("r", encoding="utf-8", errors="replace") as source:
        for line_number, line in enumerate(source, start=1):
            line = line.rstrip("\n")
            fields = line.split(SEPARATOR)
            if len(fields) != 3:
                print(f"skip malformed line {line_number}: expected 3 fields")
                continue
            title, content, url = fields
            documents.append({"title": title, "url": url, "content": content})
            if args.limit > 0 and len(documents) >= args.limit:
                break

    if not documents:
        raise SystemExit("no valid documents were produced")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(documents)} documents to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
