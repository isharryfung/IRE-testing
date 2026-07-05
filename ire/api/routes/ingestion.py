from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['ingestion'])


class IngestRequest(BaseModel):
    source_system: str
    source_pk: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = 'api'


class BatchRecordRequest(BaseModel):
    source_pk: str
    data: Dict[str, Any] = Field(default_factory=dict)


class BatchIngestRequest(BaseModel):
    source_system: str
    created_by: str = 'api'
    records: List[BatchRecordRequest] = Field(default_factory=list)


@router.post('/ire/ingest')
def ingest_record(request: Request, payload: IngestRequest) -> dict:
    try:
        decision = request.app.state.service.process_record(payload.source_system, payload.source_pk, payload.data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    source_record = request.app.state.repo.find_latest_source_record(payload.source_system, payload.source_pk)
    return {'decision': decision, 'source_record': source_record}


@router.post('/ire/ingest/batch')
def ingest_batch(request: Request, payload: BatchIngestRequest) -> dict:
    repo = request.app.state.repo
    try:
        source_system = repo._get_source_system_by_name(payload.source_system)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    batch = repo.create_ingestion_batch(source_system.system_id, len(payload.records), created_by=payload.created_by)
    decisions: List[Dict[str, Any]] = []
    for record in payload.records:
        try:
            decision = request.app.state.service.process_record(payload.source_system, record.source_pk, record.data)
            latest = repo.find_latest_source_record(payload.source_system, record.source_pk)
            if latest:
                repo.attach_record_to_batch(latest['source_record_id'], batch['batch_id'], payload.created_by)
            decisions.append({'source_pk': record.source_pk, 'decision': decision.decision, 'confidence': decision.confidence})
        except Exception:  # pragma: no cover - defensive for POC routes
            decisions.append({'source_pk': record.source_pk, 'decision': 'failed', 'error': 'Processing failed'})
    batch = repo.finalize_ingestion_batch(batch['batch_id'], decisions)
    return {'batch': batch, 'results': decisions}


@router.get('/ire/ingest/batches')
def list_batches(request: Request) -> list[dict]:
    return request.app.state.repo.list_ingestion_batches()


@router.get('/ire/ingest/batches/{batch_id}')
def get_batch(request: Request, batch_id: str) -> dict:
    batch = request.app.state.repo.get_ingestion_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail='Batch not found')
    return batch


@router.get('/ire/ingest/batches/{batch_id}/records')
def get_batch_records(request: Request, batch_id: str) -> list[dict]:
    batch = request.app.state.repo.get_ingestion_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail='Batch not found')
    return request.app.state.repo.list_batch_records(batch_id)
