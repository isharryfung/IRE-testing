# IRE Frontend

Browser UI for the IRE MVP workflows:
- Dashboard
- Ingest Record
- Match Record
- Manual Review Queue
- Review Task Detail
- Golden Record View

## Run frontend

```bash
cd ui
npm install
npm run dev
```

## Run backend API

From repository root:

```bash
uvicorn ire.api:app --reload
```

## API base URL

Set the frontend API base URL with:

```bash
VITE_IRE_API_BASE_URL=http://localhost:8000
```

If the backend is unreachable, the UI switches to demo mode and shows sample data/messages for walkthroughs.

## Quick workflow

1. Start backend (`uvicorn ire.api:app --reload`)
2. Start frontend (`cd ui && npm run dev`)
3. Open Dashboard and check API status
4. Submit records from **Ingest Record** or **Match Record**
5. Open **Manual Review Queue** and review a task in **Review Task Detail**
6. Open **Golden Record View** and look up a `golden_id`

## Validation

```bash
cd ui
npm install
npm run build
```
