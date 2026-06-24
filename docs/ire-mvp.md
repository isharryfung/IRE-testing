# IRE MVP

## Overview
The MVP `ire/` package provides a clean, importable identity resolution workflow for demo and future Oracle-backed deployments. It preserves the legacy prototype while introducing typed dataclasses, normalization, blocking, deterministic rules, weighted scoring, safety checks, survivorship, repositories, a service orchestrator, API endpoints, and a CLI.

## Package structure
- `ire/models.py`: stdlib dataclasses for operational records, candidates, decisions, and review tasks.
- `ire/config.py`: environment-driven configuration singleton (`from ire.config import config`).
- `ire/normalizer.py`: normalization helpers for names, email, phone, addresses, HKID, and institution IDs.
- `ire/candidate_generation.py`: blocking rules for Tier 1 IDs, email, phone, and name tokens.
- `ire/deterministic.py`: exact Tier 1 rules and conflict detection.
- `ire/scoring.py`: dynamic weighted scoring using `difflib.SequenceMatcher`.
- `ire/safety.py`: post-score safety flags.
- `ire/decision.py`: final match decision policy.
- `ire/survivorship.py`: canonical update policy and provenance generation.
- `ire/repository.py`: persistence abstraction.
- `ire/demo_repository.py`: in-memory demo repository with CSV bootstrap support.
- `ire/oracle_repository.py`: documented Oracle persistence contract.
- `ire/service.py`: orchestration pipeline.
- `ire/api.py`: FastAPI endpoints.
- `ire/cli.py`: batch CSV CLI.

## Configuration
The package reads the following environment variables:
- `IRE_MODE` (default: `demo`)
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_DSN`
- `IRE_AUTO_MERGE_THRESHOLD` (default: `0.85`)
- `IRE_MANUAL_REVIEW_THRESHOLD` (default: `0.50`)
- `IRE_MULTI_MATCH_GAP_THRESHOLD` (default: `0.10`)

## Data model
The dataclasses cover source systems, source records, normalized identities, golden records, record links, candidate summaries, candidate feature evidence, manual review tasks and decisions, merge history events, and the final `MatchDecision` object returned by the service/API/CLI.

## Matching pipeline
1. Resolve the source system metadata.
2. Ingest and persist a `SourceRecord`.
3. Normalize the record into `NormalizedIdentity`.
4. Load golden records.
5. Generate candidates with simple blocking.
6. Run deterministic Tier 1 checks.
7. Score each candidate dynamically.
8. Apply safety flags.
9. Make the final decision.
10. Persist the candidate summary and feature evidence.
11. Auto-merge, queue manual review, or create a new golden record.
12. Write merge history events.

## Normalization rules
- **Name**: lowercase, trim, collapse whitespace.
- **Email**: lowercase, trim.
- **Phone**: digits only.
- **Address**: lowercase, trim, collapse whitespace.
- **HKID**: uppercase alphanumeric only.
- **EMPLID / STUDENTID / ALUMNIID**: trimmed uppercase.

## Candidate generation
Blocking strategies are intentionally simple for MVP/demo use:
- exact Tier 1 ID match (`hkid`, `emplid`, `studentid`, `alumniid`)
- exact normalized email match
- exact phone or matching last 8 digits
- name-token overlap with the canonical name
- fallback to all golden records when the blocked set is empty

## Deterministic rules
Tier 1 identifiers take precedence:
- internal sources auto-match when a Tier 1 ID matches and there is no Tier 1 conflict
- external sources require exact supporting name and email to elevate a Tier 1 match into a deterministic match
- any conflicting non-empty Tier 1 attribute of the same type triggers deterministic conflict handling

## Scoring model
Scoring uses only fields present on both sides. Each present field receives a dynamic weight derived from its priority:
- Tier 1 IDs: 100
- email: 80
- phone: 60
- name: 40
- address: 20

Similarity functions:
- exact match for Tier 1 IDs and email
- phone exact or last-8-digit match
- `difflib.SequenceMatcher` ratio for name and address

Feature-level evidence records the normalized values, algorithm, weight, weighted score, match flag, and Tier 1 conflict flags.

## Safety policy
Safety checks produce flags for:
- Tier 1 conflicts
- multiple high-confidence candidates
- low score gap between the top two candidates
- untrusted or external sources

These flags are used to prevent unsafe auto-merges.

## Decision policy
The policy prefers deterministic conflict handling, then deterministic matches, then threshold-based scoring with safety gating:
- deterministic conflict → `manual-review`
- deterministic match (without Tier 1 conflict flag) → `auto-merge`
- low/no score → `new-golden-record`
- ambiguous high-score situations → `manual-review`
- strong score without safety flags → `auto-merge`
- otherwise medium score → `manual-review`

## Survivorship and provenance
Survivorship uses two strategies:
- `trust_best_source`: prefer incoming non-empty values only from internal sources
- `most_recent`: prefer incoming non-empty values regardless of source

Empty canonical values are always backfilled. Provenance is stored as field-level metadata containing the source system, source PK, and source record identifier.

## Demo repository
`DemoRepository` is fully in memory and can bootstrap from CSV files. It supports:
- loading source systems
- loading and updating golden records
- ingesting source records
- persisting normalized identities
- saving candidate summaries and features
- creating review tasks
- recording merge history

## Oracle repository
`OracleRepository` documents the intended SQL for the reference Oracle schema in `sql/oracle_ire_schema.sql`. Methods intentionally raise `NotImplementedError` in this environment because the repository cannot be validated end-to-end here.

## API
The FastAPI app exposes:
- `GET /health`
- `POST /ire/ingest`
- `POST /ire/match`
- `GET /ire/golden/{golden_id}`
- `GET /ire/review/tasks`
- `POST /ire/review/{task_id}/decision`
- `GET /ire/source/{source_record_id}`

## CLI
Example:

```bash
python -m ire.cli   --golden ire/sample_data/golden_records.csv   --incoming ire/sample_data/incoming_records.csv   --out ire/sample_data/ire_match_results.csv
```

The CLI reads incoming rows, executes the service pipeline, and writes CSV output with:
- source keys and systems
- final decision
- best golden ID
- confidence and reason
- candidate count
- safety flags JSON
- evidence JSON

## Sample data coverage
The included sample CSVs cover:
1. internal exact EMPLID auto-merge
2. internal multi-attribute auto-merge
3. external Tier 1 hit requiring manual review
4. multi-candidate CRM ambiguity
5. weak external match creating a new golden record
6. external Tier 1/name conflict requiring review

## Testing
Unit tests cover normalization, deterministic rules, scoring, safety flags, and decision logic. The package is importable from the repository root and can be exercised through both the CLI and FastAPI app.
