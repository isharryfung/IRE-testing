# Scoring regression test plan

## Why this dataset exists

The prototype matcher currently combines deterministic identifier checks and weighted field similarity scoring. This dataset provides a stable regression baseline so scoring and threshold changes can be measured against realistic identity-resolution scenarios before behavior changes are accepted.

## How to run the regression runner

From the repository root:

```bash
python prototype/run_scoring_tests.py \
  --golden prototype/golden_records_extended.csv \
  --incoming prototype/incoming_records_scoring_cases.csv \
  --expected prototype/expected_decisions.csv \
  --out prototype/scoring_test_results.csv
```

## Expected output and pass/fail behavior

- The runner writes one result row per case to `prototype/scoring_test_results.csv` (or `--out`).
- `status=PASS` means both decision and best golden ID matched expected values.
- `status=FAIL` means either the decision or selected golden ID differed.
- The script exits with code `0` only when all cases pass; otherwise it exits non-zero for CI use.

## Scenario categories covered

- Internal trusted identifier exact matches
- Third-party identifier and exact identity combinations
- Strong email/phone/name agreement
- Email conflicts and phone conflicts
- Weak name-only comparisons
- Staff/student/alumni cross-identifier scenarios
- Conflicting HKID from third-party source
- Completely new-person creation scenarios

## Known current prototype gaps

The current matcher is intentionally simple and currently misses case `C003` in this suite (`auto-merge` expected, `manual-review` actual). The record has strong email/phone/address agreement but no deterministic ID intersection with the golden record, and the present weighted score remains below the `AUTO_MERGE_THRESHOLD`.

Use this dataset as a regression benchmark and update expected outcomes or matching logic intentionally as scoring thresholds and survivorship policies evolve.

## Evolution guidance

Expand this dataset whenever scoring thresholds, deterministic rules, source-trust policies, or survivorship behavior are changed so regression coverage keeps pace with prototype evolution.
