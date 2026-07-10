from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['matching'])


class MatchRequest(BaseModel):
    source_system: str
    source_pk: str = 'preview'
    data: Dict[str, Any] = Field(default_factory=dict)


@router.post('/ire/match')
def match_only(request: Request, payload: MatchRequest) -> dict:
    try:
        return request.app.state.repo.preview_match(payload.source_system, payload.data, source_pk=payload.source_pk)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/ire/match-candidates')
def list_match_candidates(request: Request, source_record_id: Optional[str] = None) -> list[dict]:
    return request.app.state.repo.list_match_candidates(source_record_id)


@router.get('/ire/match-candidates/{candidate_id}')
def get_match_candidate(request: Request, candidate_id: str) -> dict:
    candidate = request.app.state.repo.get_match_candidate_detail(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail='Match candidate not found')
    return candidate


@router.get('/ire/match-candidates/{candidate_id}/features')
def get_match_candidate_features(request: Request, candidate_id: str) -> list[dict]:
    candidate = request.app.state.repo.get_match_candidate_detail(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail='Match candidate not found')
    return request.app.state.repo.get_match_candidate_features(candidate_id)
