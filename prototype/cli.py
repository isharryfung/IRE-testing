#!/usr/bin/env python3
"""Command-line runner for the IRE prototype."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from ire_lib import match_record, merge_record


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description="Match incoming identity records to golden records")
    parser.add_argument("--golden", required=True, type=Path, help="CSV file containing golden records")
    parser.add_argument("--incoming", required=True, type=Path, help="CSV file containing incoming records")
    parser.add_argument("--merge", action="store_true", help="Include prototype merged output for auto-merge decisions")
    args = parser.parse_args()

    golden_records = read_csv(args.golden)
    incoming_records = read_csv(args.incoming)

    for incoming in incoming_records:
        result = match_record(incoming, golden_records)
        output = {
            "incoming_record_id": incoming.get("record_id"),
            "match": result.to_dict(),
        }
        if args.merge and result.decision == "auto_merge" and result.best_match_index is not None:
            output["merged_record"] = merge_record(incoming, golden_records[result.best_match_index])
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
