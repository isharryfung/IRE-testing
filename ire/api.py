from __future__ import annotations

"""FastAPI surface for the IRE MVP package."""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from ire import __version__
from ire.config import config
from ire.demo_repository import DemoRepository
from ire.models import GoldenRecord
from ire.repository import IRERepository
from ire.service import IREService


app = FastAPI(title='Identity Resolution Engine', version=__version__)

_repo: Optional[IRERepository] = None
_service: Optional[IREService] = None


class IngestRequest(BaseModel):
    source_system: str
    source_pk: str
    data: Dict[str, Any] = Field(default_factory=dict)


class MatchRequest(BaseModel):
    source_system: str
    data: Dict[str, Any] = Field(default_factory=dict)
    golden_records: Optional[List[Dict[str, Any]]] = None


class ReviewDecisionRequest(BaseModel):
    reviewer: str
    decision: str
    golden_id: Optional[str] = None
    notes: str = ''



def _get_service() -> IREService:
    if _service is None:
        raise HTTPException(status_code=503, detail='IRE service not initialized')
    return _service



def _get_repo() -> IRERepository:
    if _repo is None:
        raise HTTPException(status_code=503, detail='IRE repository not initialized')
    return _repo


@app.on_event('startup')
def startup() -> None:
    global _repo, _service
    sample_dir = Path(__file__).resolve().parent / 'sample_data'
    golden_csv = sample_dir / 'golden_records.csv'
    source_systems_csv = sample_dir / 'source_systems.csv'
    _repo = DemoRepository(
        golden_csv=golden_csv if golden_csv.exists() else None,
        source_systems_csv=source_systems_csv if source_systems_csv.exists() else None,
    )
    _service = IREService(_repo, config)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'mode': config.IRE_MODE, 'version': __version__}


@app.post('/ire/ingest')
def ingest(request: IngestRequest) -> dict:
    decision = _get_service().process_record(request.source_system, request.source_pk, request.data)
    return asdict(decision)


@app.post('/ire/match')
def match_only(request: MatchRequest) -> dict:
    temp_repo = DemoRepository()
    for golden_data in request.golden_records or [asdict(record) for record in _get_repo().load_golden_records()]:
        temp_repo.create_golden_record(
            GoldenRecord(
                golden_id=golden_data.get('golden_id', ''),
                canonical_name=golden_data.get('canonical_name'),
                canonical_email=golden_data.get('canonical_email'),
                canonical_phone=golden_data.get('canonical_phone'),
                canonical_hkid=golden_data.get('canonical_hkid'),
                canonical_emplid=golden_data.get('canonical_emplid'),
                canonical_studentid=golden_data.get('canonical_studentid'),
                canonical_alumniid=golden_data.get('canonical_alumniid'),
                canonical_address=golden_data.get('canonical_address'),
                person_type=golden_data.get('person_type', 'person'),
                status=golden_data.get('status', 'active'),
            )
        )
    temp_service = IREService(temp_repo, config)
    source_pk = str(request.data.get('source_pk') or 'match-only')
    decision = temp_service.process_record(request.source_system, source_pk, request.data)
    return asdict(decision)


@app.get('/ire/golden/{golden_id}')
def get_golden(golden_id: str) -> dict:
    golden = _get_repo().get_golden_record(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail='Golden record not found')
    return asdict(golden)


@app.get('/ire/review/tasks')
def list_review_tasks(status: Optional[str] = Query(default='open')) -> list:
    tasks = _get_repo().list_manual_review_tasks(status=status)
    return [asdict(task) for task in tasks]


@app.post('/ire/review/{task_id}/decision')
def resolve_review(task_id: str, request: ReviewDecisionRequest) -> dict:
    try:
        task = _get_service().resolve_review_task(task_id, request.reviewer, request.decision, request.golden_id, request.notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return asdict(task)


@app.get('/ire/source/{source_record_id}')
def get_source_record(source_record_id: str) -> dict:
    record = _get_repo().get_source_record(source_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Source record not found')
    return asdict(record)
