#!/usr/bin/env python3
from __future__ import annotations

"""IRE MVP CLI - run identity resolution in demo mode."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

from ire.config import config
from ire.demo_repository import DemoRepository
from ire.evidence import build_evidence_json
from ire.oracle_repository import OracleRepository
from ire.service import IREService


OUTPUT_COLUMNS = [
    'source_pk',
    'source_system',
    'decision',
    'best_golden_id',
    'confidence',
    'reason',
    'candidate_count',
    'safety_flags_json',
    'evidence_json',
]



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run the IRE MVP CLI against CSV inputs.')
    parser.add_argument('--golden', required=True, help='Path to golden records CSV')
    parser.add_argument('--incoming', required=True, help='Path to incoming records CSV')
    parser.add_argument('--out', help='Output CSV path. Defaults to stdout.')
    parser.add_argument('--source-systems', help='Optional source systems CSV path')
    parser.add_argument('--mode', choices=['demo', 'oracle'], default='demo')
    return parser



def _load_rows(path: Path) -> Iterable[dict]:
    with path.open(newline='', encoding='utf-8') as handle:
        yield from csv.DictReader(handle)



def _build_service(args: argparse.Namespace) -> IREService:
    if args.mode == 'oracle':
        repo = OracleRepository(config.ORACLE_USER, config.ORACLE_PASSWORD, config.ORACLE_DSN)
    else:
        repo = DemoRepository(golden_csv=Path(args.golden), source_systems_csv=Path(args.source_systems) if args.source_systems else None)
    return IREService(repo, config)



def _result_row(source_pk: str, source_system: str, decision) -> dict:
    return {
        'source_pk': source_pk,
        'source_system': source_system,
        'decision': decision.decision,
        'best_golden_id': decision.best_golden_id or '',
        'confidence': f'{decision.confidence:.6f}',
        'reason': decision.reason,
        'candidate_count': decision.candidate_count,
        'safety_flags_json': json.dumps(decision.safety_flags),
        'evidence_json': build_evidence_json(decision.features),
    }



def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    service = _build_service(args)

    rows = []
    for row in _load_rows(Path(args.incoming)):
        source_pk = (row.get('source_pk') or '').strip()
        source_system = (row.get('source_system') or '').strip()
        payload = {
            'name': row.get('name', ''),
            'email': row.get('email', ''),
            'phone': row.get('phone', ''),
            'hkid': row.get('hkid', ''),
            'emplid': row.get('emplid', ''),
            'studentid': row.get('studentid', ''),
            'alumniid': row.get('alumniid', ''),
            'address': row.get('address', ''),
        }
        try:
            decision = service.process_record(source_system, source_pk, payload)
            rows.append(_result_row(source_pk, source_system, decision))
        except Exception as exc:  # pragma: no cover - CLI resilience path
            rows.append(
                {
                    'source_pk': source_pk,
                    'source_system': source_system,
                    'decision': 'error',
                    'best_golden_id': '',
                    'confidence': '0.000000',
                    'reason': str(exc),
                    'candidate_count': 0,
                    'safety_flags_json': '[]',
                    'evidence_json': '[]',
                }
            )

    if args.out:
        output_handle = Path(args.out).open('w', newline='', encoding='utf-8')
    else:
        output_handle = sys.stdout

    try:
        writer = csv.DictWriter(output_handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.out and output_handle is not sys.stdout:
            output_handle.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
