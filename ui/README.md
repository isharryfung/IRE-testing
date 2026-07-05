# IRE UI

## Setup
- `cd ui && npm install`
- `npm run dev`
- `npm run build`

## API configuration
Set `VITE_IRE_API_BASE_URL=http://localhost:8000` before starting the Vite dev server if the backend is running on a non-default host.

## Backend startup
Run `uvicorn ire.api.main:app --reload` from the repository root to start the FastAPI backend.

## Workflow walkthrough
1. Open the Dashboard to see ingestion, matching, and review counts.
2. Create a new source record from **New Source Record** to test the ingest flow.
3. Review **Manual Review Queue** items and inspect feature-level evidence.
4. Search **Golden Records** or **Source Records** for detailed profile and provenance views.
5. Use the settings pages to preview threshold, rule, survivorship, and source-system configuration changes.
