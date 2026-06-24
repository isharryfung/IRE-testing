# Database Design (Oracle Schema v2)

## Overview
`sql/oracle_identity_resolution_schema_v2.sql` defines the POC/MVP schema for the Identity Resolution Engine (IRE). It separates raw source ingestion, normalized identities, resolved golden records, candidate evidence, manual review, and audit history.

## Table purposes
- **source_systems**: source registry with trust level and internal/external marker.
- **source_records**: immutable raw ingestion records (`raw_payload` JSON).
- **normalized_identities**: normalized searchable identity attributes derived from a source record.
- **golden_records**: canonical person-level resolved profile.
- **golden_field_values**: field-level survivorship/provenance for golden attributes.
- **record_links**: link between source record and golden record with confidence + method.
- **match_candidates**: candidate-level summary (rank, confidence, blocked reason, summary JSON).
- **match_candidate_features**: dynamic field/rule evidence rows for each candidate.
- **manual_review_tasks**: queue of review tasks with payload context.
- **manual_review_decisions**: reviewer action history per task.
- **merge_history**: audit trail of merge/link/unmerge events.
- **matching_rules**: rule catalog for deterministic, probabilistic, and safety checks.
- **survivorship_rules**: rule catalog for selecting canonical values.
- **rebatch_jobs**: operational history of rematching/rebatch runs.

## Key relationships
- `source_records.source_system_id -> source_systems.source_system_id`
- `normalized_identities.source_record_id -> source_records.source_record_id`
- `record_links.(source_record_id, golden_id) -> source_records/golden_records`
- `match_candidates.(source_record_id, golden_id) -> source_records/golden_records`
- `match_candidate_features.match_candidate_id -> match_candidates.match_candidate_id`
- `manual_review_tasks.source_record_id -> source_records.source_record_id`
- `manual_review_decisions.task_id -> manual_review_tasks.task_id`
- `golden_field_values` links each canonical field value to the contributing source record/system.

## Ingestion flow
1. Register source in `source_systems`.
2. Insert incoming payload into `source_records` (raw preserved).
3. Normalize and store searchable attributes in `normalized_identities`.

## Matching flow
1. Generate candidates and save summary rows in `match_candidates`.
2. Save flexible evidence in `match_candidate_features` (field, rule, similarity, weight, JSON evidence).
3. If matched, create `record_links` and update `golden_records` / `golden_field_values`.

## Flexible evidence model
The schema intentionally avoids fixed columns like `name_score`, `email_score`, etc.
- `match_candidates` stores candidate-level result.
- `match_candidate_features` stores dynamic evidence rows (any field/rule combination), enabling rule evolution without schema changes.

## Manual review flow
1. Safety checks create `manual_review_tasks`.
2. Reviewer submits action in `manual_review_decisions`.
3. System applies decision (e.g., merge/new golden) and writes `record_links` + `merge_history`.

## Audit/provenance
- Raw payload retained in `source_records.raw_payload`.
- Field-level provenance retained in `golden_field_values`.
- Decision/merge lineage retained in `manual_review_decisions` + `merge_history`.

## Survivorship model
`survivorship_rules` provides configurable per-field strategy metadata (trust-best-source, most-recent, most-complete, etc.). `golden_field_values` stores which rule was applied and source evidence.

## Applying the Oracle schema
From SQL*Plus or SQLcl:

```sql
@sql/oracle_identity_resolution_schema_v2.sql
```

The script creates tables/indexes and inserts seed rows for `source_systems`, `matching_rules`, and `survivorship_rules`.
