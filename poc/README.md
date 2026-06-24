# IRE POC (v2)

## Setup
From repository root:

```bash
python -m pip install -r poc/requirements.txt
```

## Run CLI demo

```bash
python -m poc.ire_poc.cli \
  --golden poc/sample_data/golden_records.csv \
  --incoming poc/sample_data/incoming_records.csv \
  --out poc/sample_data/poc_match_results.csv
```

Output columns:
`source_pk,source_system,decision,best_golden_id,confidence,reason,candidate_count,evidence_json`

## Run FastAPI demo

```bash
python -m uvicorn poc.ire_poc.api:app --reload --host 0.0.0.0 --port 8010
```

Endpoints:
- `GET /health`
- `POST /poc/ingest`
- `POST /poc/match`
- `GET /poc/golden/{golden_id}`
- `GET /poc/review/tasks`
- `POST /poc/review/{task_id}/decision`

### Example curl

```bash
curl -s http://localhost:8010/poc/match \
  -H 'content-type: application/json' \
  -d '{"record":{"source_system":"THIRDPARTY","source_pk":"TP-1","name":"John Chan","email":"john.chan@ust.hk","phone":"+852-5555-1234","hkid":"A123456(7)","address":"Kowloon"}}'

curl -s http://localhost:8010/poc/ingest \
  -H 'content-type: application/json' \
  -d '{"record":{"source_system":"CRM","source_pk":"CRM-2","name":"May Lee","email":"may.lee@ust.hk"}}'
```

## Apply Oracle schema v2

```sql
@sql/oracle_identity_resolution_schema_v2.sql
```

## Environment variables
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_DSN`
- `IRE_AUTO_MERGE_THRESHOLD` (default `0.85`)
- `IRE_MANUAL_REVIEW_THRESHOLD` (default `0.50`)

## Demo mode vs Oracle mode
- **Demo mode (default):** in-memory repository, fully runnable without Oracle.
- **Oracle mode:** when Oracle env vars are set, service uses Oracle repository hooks for persistence (schema + insert/query hooks provided).
