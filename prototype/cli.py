#!/usr/bin/env python3
"""Command-line runner for the IRE prototype."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Allow running from the prototype/ directory or from the repo root.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from ire_lib import match_record, merge_record  # noqa: E402

DECISIONS_COLUMNS = [
    "source_pk",
    "source_name",
    "decision",
    "best_golden_id",
    "confidence",
    "sims",
    "reason",
    "timestamp",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_decisions_csv(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISIONS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Match incoming identity records to golden records")
    parser.add_argument("--golden", required=True, type=Path, help="CSV file containing golden records")
    parser.add_argument("--incoming", required=True, type=Path, help="CSV file containing incoming records")
    parser.add_argument("--out", type=Path, default=None, help="Output CSV path for decisions (default: print JSON to stdout)")
    args = parser.parse_args()

    golden_records = read_csv(args.golden)
    incoming_records = read_csv(args.incoming)

    decision_rows: List[Dict] = []
    ts = datetime.now(timezone.utc).isoformat()

    for incoming in incoming_records:
        result = match_record(incoming, golden_records)
        if args.out:
            decision_rows.append({
                "source_pk": incoming.get("record_id", ""),
                "source_name": incoming.get("source_type") or incoming.get("source_name", ""),
                "decision": result.decision,
                "best_golden_id": result.best_match_record_id or "",
                "confidence": result.confidence,
                "sims": json.dumps(result.similarities),
                "reason": result.explanation,
                "timestamp": ts,
            })
        else:
            print(json.dumps({
                "incoming_record_id": incoming.get("record_id"),
                "match": result.to_dict(),
            }, ensure_ascii=False, sort_keys=True))

    if args.out:
        out_path = Path(args.out)
        write_decisions_csv(out_path, decision_rows)
        print(f"Wrote {len(decision_rows)} decisions to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
