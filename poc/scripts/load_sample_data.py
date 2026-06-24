from __future__ import annotations

import csv
from pathlib import Path

from poc.ire_poc.demo_repository import DemoRepository
from poc.ire_poc.models import IdentityRecord
from poc.ire_poc.service import IREService


def _read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    golden_path = Path("poc/sample_data/golden_records.csv")
    incoming_path = Path("poc/sample_data/incoming_records.csv")

    goldens = [IdentityRecord(**row) for row in _read_csv(golden_path)]
    repo = DemoRepository(initial_goldens=goldens)
    service = IREService(repo)

    for row in _read_csv(incoming_path):
        service.ingest(IdentityRecord(**row))

    print("Loaded sample records into demo repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
