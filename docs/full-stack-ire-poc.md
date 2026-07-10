# Full-Stack Identity Resolution Engine POC

## Purpose and target users
This POC exposes a backend tailored for a full-stack identity resolution demo. It is aimed at data stewards, reviewers, rule administrators, and solution stakeholders who need realistic ingestion, matching, golden-record, survivorship, and audit flows without requiring an Oracle deployment.

## Backend startup
```bash
pip install -r requirements-ire.txt
uvicorn ire.api.main:app --reload
```

## End-to-end process flow
1. A source system submits a source record or a batch.
2. The backend stores raw source data and a normalized identity projection.
3. Candidate generation narrows the golden-record search space.
4. Deterministic rules and weighted scoring produce candidate evidence.
5. Safety checks decide between auto-merge, manual review, or new golden creation.
6. When merged, the source record is linked to a golden record and survivorship updates the canonical profile.
7. When not safe, a manual review task is created with candidate and feature evidence.
8. Every important action writes merge history and audit events.
9. Duplicate-golden workflows allow post-match remediation.

## Database tables
### Source and ingestion
- `source_systems`: source registry with trust and activation flags.
- `ingestion_batches`: operational status for a source ingest run.
- `source_records`: raw inbound records plus payload and validation state.
- `normalized_identities`: normalized view used for candidate generation and scoring.

### Golden record and linkage
- `golden_records`: canonical person profile.
- `golden_field_values`: field-level provenance entries that show which source contributed a canonical value.
- `record_links`: active and inactive relationships between source records and goldens.

### Matching and evidence
- `matching_features`: configurable feature catalog.
- `matching_rules`: active rules that shape deterministic or probabilistic behavior.
- `matching_rule_versions`: immutable snapshots of rule changes.
- `threshold_settings`: global decision thresholds.
- `match_candidates`: candidate-level results and summary flags.
- `match_candidate_features`: feature-level evidence for a candidate.
- `rule_simulations`: simulation runs for proposed rule changes.
- `rule_simulation_results`: per-record simulation outcomes.

### Manual review and duplicate handling
- `manual_review_tasks`: reviewer work queue.
- `manual_review_decisions`: historical reviewer outcomes.
- `golden_duplicate_candidates`: suspected duplicate golden pairs.
- `golden_merge_events`: golden-to-golden consolidation events.

### Survivorship
- `survivorship_rules`: configurable survivorship strategies by field.
- `survivorship_rule_versions`: version history for survivorship changes.
- `survivorship_previews`: preview outputs before a survivorship change is applied.

### Audit and administration
- `merge_history`: operational record of link, unlink, merge, and decision actions.
- `audit_events`: broad audit stream for API and stewardship actions.
- `app_users`: application users.
- `app_roles`: role catalog.
- `app_user_roles`: user-to-role assignments.
- `rebatch_jobs`: operational jobs for replaying or reprocessing source data.

## Evidence model
The POC uses two layers of explainability:
- `match_candidates` stores the source record, candidate golden, total score, ranking, and safety hints.
- `match_candidate_features` stores field-by-field comparison evidence such as source value, normalized value, algorithm, similarity score, weighted contribution, and blocking/conflict flags.

This structure allows the UI to show both a concise match summary and reviewer-friendly evidence detail.

## Manual review workflow
Manual review tasks are created when the engine detects tier-1 conflicts, untrusted sources, multiple strong candidates, or narrow score gaps. Reviewers can:
- assign work,
- accept a merge,
- reject a candidate,
- create a new golden,
- merge or split goldens,
- escalate,
- request more information, or
- apply a manual override.

Decision history is preserved so reviewers and auditors can reconstruct why a record was resolved in a particular way.

## Link and unlink behavior
Links are soft state. Linking creates or updates a `record_links` row, enriches the golden record via survivorship, and writes merge history plus audit events. Unlinking does not delete the relationship. Instead it marks the link inactive, records an `unlink_reason`, and emits corresponding audit and merge-history entries.

## Matching configuration
Matching behavior is demonstrated with:
- 8 standard features (HKID, EmplId, StudentId, AlumniId, Email, Phone, Name, Address),
- deterministic and probabilistic matching rules,
- threshold settings for auto-merge, manual review, new golden creation, and multi-match gap handling, and
- rule simulation endpoints for showing “what-if” outcomes.

## Survivorship model
The POC reuses the existing service survivorship approach. Trusted internal identifiers prefer trusted systems, while fields such as email, phone, and address can accept the most recent authoritative update. The survivorship preview endpoint lets the UI show prospective field changes before a steward commits them.

## Demo mode vs Oracle mode
- **Demo mode**: `ire.api.main:app` loads `FullDemoRepository`, which reads rich JSON fixtures from `ire/sample_data/full_poc/`.
- **Oracle mode**: the supplied schema in `sql/oracle_identity_resolution_full_poc_schema.sql` provides an Oracle-compatible target model for a future repository implementation.

The existing MVP modules (`ire.config`, `ire.service`, `ire.models`) are still reused in demo mode so matching logic stays aligned with the core package.

## API quick reference
### Dashboard
- `GET /ire/dashboard/summary`
- `GET /ire/dashboard/process-counts`
- `GET /ire/dashboard/recent-activity`

### Ingestion
- `POST /ire/ingest`
- `POST /ire/ingest/batch`
- `GET /ire/ingest/batches`
- `GET /ire/ingest/batches/{batch_id}`
- `GET /ire/ingest/batches/{batch_id}/records`

### Golden records
- `GET /ire/golden`
- `GET /ire/golden/{golden_id}`
- `POST /ire/golden`
- `PATCH /ire/golden/{golden_id}`
- `POST /ire/golden/{golden_id}/link-source`
- `POST /ire/golden/{golden_id}/unlink-source`
- `GET /ire/golden/{golden_id}/source-links`
- `GET /ire/golden/{golden_id}/history`
- `GET /ire/golden/{golden_id}/field-provenance`
- `POST /ire/golden/{golden_id}/field-override`
- `POST /ire/golden/{golden_id}/merge`
- `POST /ire/golden/{golden_id}/split`

### Source records and matching
- `GET /ire/source-records`
- `GET /ire/source-records/{source_record_id}`
- `GET /ire/source-records/{source_record_id}/normalized`
- `GET /ire/source-records/{source_record_id}/candidates`
- `GET /ire/source-records/{source_record_id}/history`
- `POST /ire/source-records/{source_record_id}/link`
- `POST /ire/source-records/{source_record_id}/unlink`
- `POST /ire/source-records/{source_record_id}/create-golden`
- `POST /ire/source-records/{source_record_id}/rematch`
- `POST /ire/match`
- `GET /ire/match-candidates`
- `GET /ire/match-candidates/{candidate_id}`
- `GET /ire/match-candidates/{candidate_id}/features`

### Manual review and duplicates
- `GET /ire/review/tasks`
- `GET /ire/review/tasks/{task_id}`
- `POST /ire/review/tasks/{task_id}/assign`
- `POST /ire/review/tasks/{task_id}/decision`
- `GET /ire/review/tasks/{task_id}/history`
- `GET /ire/review/decisions`
- `GET /ire/golden-duplicates`
- `GET /ire/golden-duplicates/{duplicate_id}`
- `POST /ire/golden-duplicates/{duplicate_id}/decision`

### Configuration and audit
- `GET/POST/PUT/DELETE /ire/matching-features...`
- `GET/POST/PUT/DELETE /ire/matching-rules...`
- `POST /ire/rule-simulation`
- `GET /ire/rule-simulation/{simulation_id}`
- `GET /ire/rule-simulation/{simulation_id}/results`
- `GET/PUT /ire/settings/thresholds`
- `GET/POST/PUT/DELETE /ire/survivorship-rules...`
- `POST /ire/survivorship/preview`
- `GET/POST/PUT/DELETE /ire/source-systems...`
- `GET /ire/audit-events`
- `GET /ire/audit-events/{event_id}`

## Demo data storyline
The seeded demo data covers the requested frontend cases:
- John Michael Smith (`GR-001`) linked from HR and SIS.
- Jane Chan Mei Lin (`GR-002`) linked from SIS and Alumni.
- David Wong Kwok Wai (`GR-003`) linked from HR, with a third-party HKID conflict under review.
- A strong CRM contact auto-merge for Peter Lee.
- An ambiguous Alex case with multiple high candidates.
- A weak CRM match that created Sarah Ng as a new golden record.
- A third-party record requiring supporting evidence before merge.
- A deactivated CRM link with an unlink reason.
- Duplicate golden review pairs for Michael/Mike and two Alex records.
