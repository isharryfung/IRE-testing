from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=['duplicates'])


class CreateDuplicatePayload(BaseModel):
    golden_id_a: str
    golden_id_b: str
    detection_method: str = 'manual-flag'
    actor: str = 'api'


class DuplicateDecisionPayload(BaseModel):
    decision: str
    target_golden_id: Optional[str] = None
    notes: str = ''
    actor: str = 'api'


@router.post('/ire/golden-duplicates', status_code=201)
def create_duplicate(request: Request, payload: CreateDuplicatePayload) -> dict:
    try:
        return request.app.state.repo.create_duplicate_candidate(
            payload.golden_id_a,
            payload.golden_id_b,
            detection_method=payload.detection_method,
            actor=payload.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record not found') from exc


@router.get('/ire/golden-duplicates')
def list_duplicates(request: Request) -> list[dict]:
    return request.app.state.repo.list_duplicate_candidates_data()


@router.get('/ire/golden-duplicates/{duplicate_id}')
def get_duplicate(request: Request, duplicate_id: str) -> dict:
    duplicate = request.app.state.repo.get_duplicate_candidate_detail(duplicate_id)
    if duplicate is None:
        raise HTTPException(status_code=404, detail='Duplicate candidate not found')
    return duplicate


@router.post('/ire/golden-duplicates/{duplicate_id}/decision')
def decide_duplicate(request: Request, duplicate_id: str, payload: DuplicateDecisionPayload) -> dict:
    try:
        return request.app.state.repo.decide_duplicate_candidate(duplicate_id, payload.decision, actor=payload.actor, target_golden_id=payload.target_golden_id, notes=payload.notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Duplicate candidate not found') from exc
