from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['golden-records'])


class GoldenPayload(BaseModel):
    golden_id: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_email: Optional[str] = None
    canonical_phone: Optional[str] = None
    canonical_hkid: Optional[str] = None
    canonical_emplid: Optional[str] = None
    canonical_studentid: Optional[str] = None
    canonical_alumniid: Optional[str] = None
    canonical_address: Optional[str] = None
    person_type: str = 'person'
    status: str = 'active'
    is_possible_duplicate: bool = False
    confidence_level: str = 'medium'
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = 'api'


class LinkPayload(BaseModel):
    source_record_id: str
    method: str = 'manual-link'
    confidence: float = 1.0
    review_task_id: Optional[str] = None
    candidate_id: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    actor: str = 'api'


class UnlinkPayload(BaseModel):
    source_record_id: str
    reason: str
    actor: str = 'api'


class FieldOverridePayload(BaseModel):
    field_name: str
    value: Any
    actor: str = 'api'


class MergePayload(BaseModel):
    target_golden_id: str
    merge_reason: str = 'Manual merge'
    actor: str = 'api'


class SplitPayload(BaseModel):
    source_record_ids: List[str] = Field(default_factory=list)
    actor: str = 'api'


@router.get('/ire/golden')
def list_golden(
    request: Request,
    name: Optional[str] = None,
    email: Optional[str] = None,
    hkid: Optional[str] = None,
    emplid: Optional[str] = None,
    studentid: Optional[str] = None,
    alumniid: Optional[str] = None,
    status: Optional[str] = None,
    person_type: Optional[str] = None,
    possible_duplicate: Optional[bool] = Query(default=None),
) -> list[dict]:
    filters = {
        'name': name,
        'email': email,
        'hkid': hkid,
        'emplid': emplid,
        'studentid': studentid,
        'alumniid': alumniid,
        'status': status,
        'person_type': person_type,
        'possible_duplicate': possible_duplicate,
    }
    return request.app.state.repo.list_golden_record_details(filters)


@router.get('/ire/golden/{golden_id}')
def get_golden(request: Request, golden_id: str) -> dict:
    golden = request.app.state.repo.get_golden_record_detail(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail='Golden record not found')
    return golden


@router.post('/ire/golden', status_code=201)
def create_golden(request: Request, payload: GoldenPayload) -> dict:
    return request.app.state.repo.create_golden_record_full(payload.model_dump(), actor=payload.created_by)


@router.patch('/ire/golden/{golden_id}')
def update_golden(request: Request, golden_id: str, payload: GoldenPayload) -> dict:
    try:
        return request.app.state.repo.update_golden_record_detail(golden_id, payload.model_dump(exclude_unset=True), actor=payload.created_by)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record not found') from exc


@router.post('/ire/golden/{golden_id}/link-source')
def link_source(request: Request, golden_id: str, payload: LinkPayload) -> dict:
    try:
        return request.app.state.repo.link_source_to_golden(payload.source_record_id, golden_id, actor=payload.actor, method=payload.method, confidence=payload.confidence, review_task_id=payload.review_task_id, candidate_id=payload.candidate_id, evidence=payload.evidence)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source record or golden record not found') from exc


@router.post('/ire/golden/{golden_id}/unlink-source')
def unlink_source(request: Request, golden_id: str, payload: UnlinkPayload) -> list[dict]:
    try:
        return request.app.state.repo.unlink_source_from_golden(payload.source_record_id, golden_id, payload.reason, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Active link not found') from exc


@router.get('/ire/golden/{golden_id}/source-links')
def source_links(request: Request, golden_id: str) -> list[dict]:
    golden = request.app.state.repo.get_golden_record_detail(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail='Golden record not found')
    return request.app.state.repo.get_golden_source_links(golden_id)


@router.get('/ire/golden/{golden_id}/history')
def golden_history(request: Request, golden_id: str) -> list[dict]:
    golden = request.app.state.repo.get_golden_record_detail(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail='Golden record not found')
    return request.app.state.repo.get_golden_history(golden_id)


@router.get('/ire/golden/{golden_id}/field-provenance')
def field_provenance(request: Request, golden_id: str) -> dict:
    golden = request.app.state.repo.get_golden_record_detail(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail='Golden record not found')
    return request.app.state.repo.get_golden_field_provenance(golden_id)


@router.post('/ire/golden/{golden_id}/field-override')
def field_override(request: Request, golden_id: str, payload: FieldOverridePayload) -> dict:
    try:
        return request.app.state.repo.override_golden_field(golden_id, payload.field_name, payload.value, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record or field not found') from exc


@router.post('/ire/golden/{golden_id}/merge')
def merge_golden(request: Request, golden_id: str, payload: MergePayload) -> dict:
    try:
        return request.app.state.repo.merge_golden_records(golden_id, payload.target_golden_id, payload.merge_reason, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record not found') from exc


@router.post('/ire/golden/{golden_id}/split')
def split_golden(request: Request, golden_id: str, payload: SplitPayload) -> dict:
    try:
        return request.app.state.repo.split_golden(golden_id, payload.source_record_ids, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record not found') from exc
