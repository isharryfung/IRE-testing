# IRE Prototype

Prototype implementation of the Identity Resolution Engine (IRE), including a Python library, CLI runner, and FastAPI server.

## Prerequisites

Run from the **repository root** so that Python can locate `prototype/ire_lib.py`.

**Linux / macOS:**
```bash
pip install -r prototype/requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m pip install -r prototype\requirements.txt
```

---

## 1. Python CLI

Match incoming records against golden records and write a decisions CSV:

```bash
python prototype/cli.py \
  --golden prototype/golden_records.csv \
  --incoming prototype/incoming_records.csv \
  --out decisions.csv
```

Output columns: `source_pk`, `source_name`, `decision`, `best_golden_id`, `confidence`, `sims`, `reason`, `timestamp`.

---

## 2. API server (uvicorn)

**Linux / macOS:**
```bash
python -m pip install -r api/requirements.txt
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Windows (PowerShell):**
```powershell
python -m pip install -r api\requirements.txt
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: <http://localhost:8000/docs>

Environment variables:

```bash
IRE_AUTO_MERGE_THRESHOLD=0.85
IRE_MANUAL_REVIEW_THRESHOLD=0.50
ORACLE_USER=
ORACLE_PASSWORD=
ORACLE_DSN=
```

- If `ORACLE_USER`, `ORACLE_PASSWORD`, and `ORACLE_DSN` are all set, API runs in Oracle persistence mode.
- If Oracle env vars are missing, API runs in demo mode using CSV/in-memory records.

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Ingest and normalize a source record |
| POST | `/match` | Match an incoming record against golden records |
| POST | `/merge` | Merge an incoming record into a golden record |
| GET | `/golden/{golden_id}` | Retrieve a golden record |

---

## 3. Oracle schema setup (optional, Oracle mode)

Apply the schema before starting API in Oracle mode:

```bash
sqlplus "$ORACLE_USER/$ORACLE_PASSWORD@$ORACLE_DSN" @sql/oracle_ire_schema.sql
```

## 4. API server (Docker Compose)

```bash
docker compose -f docker/docker-compose.yml up --build
```

The API is available at <http://localhost:8000>.

---

## 5. Test API flow quickly

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/match -H 'Content-Type: application/json' -d '{"incoming":{"source_type":"HR","name":"John Smith","email":"jsmith@ust.hk"}}'
curl -s -X POST http://127.0.0.1:8000/ingest -H 'Content-Type: application/json' -d '{"source_name":"HR","source_pk":"1001","run_match":true,"payload":{"source_type":"HR","name":"John Smith","email":"jsmith@ust.hk"}}'
curl -s http://127.0.0.1:8000/review/tasks
```

---

## 6. React manual-review UI

```bash
cd ui
npm install
npm start       # development server at http://localhost:5173
npm run build   # production build → ui/dist/
```
