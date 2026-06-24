from __future__ import annotations

import subprocess
import sys


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "poc.ire_poc.cli",
        "--golden",
        "poc/sample_data/golden_records.csv",
        "--incoming",
        "poc/sample_data/incoming_records.csv",
        "--out",
        "poc/sample_data/poc_match_results.csv",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
