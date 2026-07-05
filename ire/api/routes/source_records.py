from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['source-records'])


class SourceLinkPayload(BaseModel):
    golden_id: str
    method: str = 'manual-link'
    confidence: float = 1.0
    actor: str = 'api'
    evidence: dict[str, Any] = Field(default_factory=dict)


class SourceUnlinkPayload(BaseModel):
    golden_id: Optional[str] = None
    reason: str
    actor: str = 'api'


class CreateGoldenPayload(BaseModel):
    actor: str = 'api'


@router.get('/ire/source-records')
def list_source_records(
    request: Request,
    source_pk: Optional[str] = None,
    source_system: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    hkid: Optional[str] = None,
    emplid: Optional[str] = None,
    studentid: Optional[str] = None,
    alumniid: Optional[str] = None,
    batch_id: Optional[str] = None,
    ingestion_status: Optional[str] = None,
) -> list[dict]:
    return request.app.state.repo.list_source_records({
        'source_pk': source_pk,
        'source_system': source_system,
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'hkid': hkid,
        'emplid': emplid,
        'studentid': studentid,
        'alumniid': alumniid,
        'batch_id': batch_id,
        'ingestion_status': ingestion_status,
    })


@router.get('/ire/source-records/{source_record_id}')
def get_source_record(request: Request, source_record_id: str) -> dict:
    record = request.app.state.repo.get_source_record_detail(source_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Source record not found')
    return record


@router.get('/ire/source-records/{source_record_id}/normalized')
def get_normalized(request: Request, source_record_id: str) -> dict:
    normalized = request.app.state.repo.get_normalized_identity_detail(source_record_id)
    if normalized is None:
        raise HTTPException(status_code=404, detail='Normalized identity not found')
    return normalized


@router.get('/ire/source-records/{source_record_id}/candidates')
def get_candidates(request: Request, source_record_id: str) -> list[dict]:
    record = request.app.state.repo.get_source_record_detail(source_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Source record not found')
    return request.app.state.repo.list_match_candidates(source_record_id)


@router.get('/ire/source-records/{source_record_id}/history')
def get_history(request: Request, source_record_id: str) -> list[dict]:
    record = request.app.state.repo.get_source_record_detail(source_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Source record not found')
    return request.app.state.repo.get_source_history(source_record_id)


@router.post('/ire/source-records/{source_record_id}/link')
def link_source_record(request: Request, source_record_id: str, payload: SourceLinkPayload) -> dict:
    try:
        return request.app.state.repo.link_source_to_golden(source_record_id, payload.golden_id, actor=payload.actor, method=payload.method, confidence=payload.confidence, evidence=payload.evidence)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source record or golden record not found') from exc


@router.post('/ire/source-records/{source_record_id}/unlink')
def unlink_source_record(request: Request, source_record_id: str, payload: SourceUnlinkPayload) -> list[dict]:
    try:
        return request.app.state.repo.unlink_source_from_golden(source_record_id, payload.golden_id, payload.reason, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Active link not found') from exc


@router.post('/ire/source-records/{source_record_id}/create-golden')
def create_golden_from_source(request: Request, source_record_id: str, payload: CreateGoldenPayload) -> dict:
    try:
        return request.app.state.repo.create_golden_from_source(source_record_id, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source record not found') from exc


@router.post('/ire/source-records/{source_record_id}/rematch')
def rematch_source_record(request: Request, source_record_id: str) -> dict:
    try:
        return request.app.state.repo.rematch_source_record(source_record_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source record not found') from exc
