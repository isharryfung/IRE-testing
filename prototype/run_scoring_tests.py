#!/usr/bin/env python3
"""Run scoring regression cases for the IRE prototype matcher."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ire_lib import match_record  # noqa: E402

RESULT_COLUMNS = [
    "case_id",
    "scenario",
    "expected_decision",
    "actual_decision",
    "expected_best_golden_id",
    "actual_best_golden_id",
    "confidence",
    "reason",
    "status",
    "sims",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def decision_to_expected_label(decision: str) -> str:
    mapping = {
        "auto_merge": "auto-merge",
        "manual_review": "manual-review",
        "create_new_golden_record": "new-golden-record",
    }
    return mapping.get((decision or "").strip(), (decision or "").strip().replace("_", "-"))


def normalize_expected_decision(decision: str) -> str:
    return decision_to_expected_label((decision or "").strip().replace("-", "_"))


def map_golden(record: Dict[str, str]) -> Dict[str, str]:
    return {
        "golden_id": (record.get("golden_id") or "").strip(),
        "name": (record.get("canonical_name") or "").strip(),
        "email": (record.get("canonical_email") or "").strip(),
        "phone": (record.get("canonical_phone") or "").strip(),
        "hkid": (record.get("canonical_hkid") or "").strip(),
        "emplid": (record.get("canonical_emplid") or "").strip(),
        "studentid": (record.get("canonical_studentid") or "").strip(),
        "alumniid": (record.get("canonical_alumniid") or "").strip(),
        "address": (record.get("canonical_address") or "").strip(),
    }


def map_incoming(record: Dict[str, str]) -> Dict[str, str]:
    return {
        "record_id": (record.get("source_pk") or "").strip(),
        "source_name": (record.get("source_name") or "").strip(),
        "name": (record.get("name") or "").strip(),
        "email": (record.get("email") or "").strip(),
        "phone": (record.get("phone") or "").strip(),
        "hkid": (record.get("hkid") or "").strip(),
        "emplid": (record.get("emplid") or "").strip(),
        "studentid": (record.get("studentid") or "").strip(),
        "alumniid": (record.get("alumniid") or "").strip(),
        "address": (record.get("address") or "").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run IRE scoring regression cases")
    parser.add_argument("--golden", type=Path, default=Path("prototype/golden_records_extended.csv"), help="Extended golden records CSV")
    parser.add_argument("--incoming", type=Path, default=Path("prototype/incoming_records_scoring_cases.csv"), help="Incoming scoring cases CSV")
    parser.add_argument("--expected", type=Path, default=Path("prototype/expected_decisions.csv"), help="Expected decision matrix CSV")
    parser.add_argument("--out", type=Path, default=Path("prototype/scoring_test_results.csv"), help="Output CSV path")
    args = parser.parse_args()

    golden_records = [map_golden(row) for row in read_csv(args.golden)]
    incoming_records = read_csv(args.incoming)
    expected_rows = read_csv(args.expected)
    expected_by_case = {row.get("case_id", "").strip(): row for row in expected_rows}

    result_rows: List[Dict[str, str]] = []
    failures = 0

    for case in incoming_records:
        case_id = (case.get("case_id") or "").strip()
        expected = expected_by_case.get(case_id, {})

        expected_decision = normalize_expected_decision(expected.get("expected_decision") or case.get("expected_decision") or "")
        expected_best = (expected.get("expected_best_golden_id") or case.get("expected_best_golden_id") or "").strip()

        result = match_record(map_incoming(case), golden_records)
        actual_decision = decision_to_expected_label(result.decision)
        actual_best = (result.best_match_record_id or "").strip()
        if actual_decision == "new-golden-record":
            actual_best = ""

        pass_decision = actual_decision == expected_decision
        pass_best = actual_best == expected_best
        status = "PASS" if (pass_decision and pass_best) else "FAIL"
        if status == "FAIL":
            failures += 1

        result_rows.append({
            "case_id": case_id,
            "scenario": (case.get("scenario") or "").strip(),
            "expected_decision": expected_decision,
            "actual_decision": actual_decision,
            "expected_best_golden_id": expected_best,
            "actual_best_golden_id": actual_best,
            "confidence": f"{result.confidence:.6f}",
            "reason": result.explanation,
            "status": status,
            "sims": json.dumps(result.similarities, sort_keys=True),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(result_rows)

    passed = len(result_rows) - failures
    print(f"Scoring regression complete: {passed} passed, {failures} failed, {len(result_rows)} total")
    print(f"Results written to {args.out}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
