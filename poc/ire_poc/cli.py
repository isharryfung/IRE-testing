from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from .demo_repository import DemoRepository
from .models import IdentityRecord
from .service import IREService

OUTPUT_COLUMNS = [
    "source_pk",
    "source_system",
    "decision",
    "best_golden_id",
    "confidence",
    "reason",
    "candidate_count",
    "evidence_json",
]


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _identity_from_row(row: Dict[str, str]) -> IdentityRecord:
    return IdentityRecord(
        source_system=row.get("source_system", ""),
        source_pk=row.get("source_pk", ""),
        name=row.get("name", ""),
        email=row.get("email", ""),
        phone=row.get("phone", ""),
        address=row.get("address", ""),
        hkid=row.get("hkid", ""),
        emplid=row.get("emplid", ""),
        student_id=row.get("student_id", ""),
        alumni_id=row.get("alumni_id", ""),
        raw_payload={k: v for k, v in row.items()},
    )


def _write_output(path: Path, rows: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="IRE POC CLI demo")
    parser.add_argument("--golden", required=True, type=Path)
    parser.add_argument("--incoming", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    golden_records = [_identity_from_row(row) for row in _read_csv(args.golden)]
    incoming_records = [_identity_from_row(row) for row in _read_csv(args.incoming)]

    repository = DemoRepository(initial_goldens=golden_records)
    service = IREService(repository=repository)

    output_rows: List[Dict[str, str]] = []
    for incoming in incoming_records:
        result = service.match(incoming)
        output_rows.append(
            {
                "source_pk": result["source_pk"],
                "source_system": result["source_system"],
                "decision": result["decision"],
                "best_golden_id": result["best_golden_id"] or "",
                "confidence": str(result["confidence"]),
                "reason": result["reason"],
                "candidate_count": str(result["candidate_count"]),
                "evidence_json": json.dumps(result["evidence"], ensure_ascii=False),
            }
        )

    _write_output(args.out, output_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
