from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=['source-systems'])


class SourceSystemPayload(BaseModel):
    system_id: str | None = None
    name: str
    description: str = ''
    trust_level: str = 'standard'
    is_internal: bool = False
    auto_merge_allowed: bool = True
    is_active: bool = True
    actor: str = 'api'


@router.get('/ire/source-systems')
def list_source_systems(request: Request) -> list[dict]:
    return request.app.state.repo.list_source_systems_data()


@router.post('/ire/source-systems', status_code=201)
def create_source_system(request: Request, payload: SourceSystemPayload) -> dict:
    return request.app.state.repo.create_source_system(payload.model_dump(), actor=payload.actor)


@router.get('/ire/source-systems/{source_system_id}')
def get_source_system(request: Request, source_system_id: str) -> dict:
    detail = request.app.state.repo.get_source_system_detail(source_system_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Source system not found')
    return detail


@router.put('/ire/source-systems/{source_system_id}')
def update_source_system(request: Request, source_system_id: str, payload: SourceSystemPayload) -> dict:
    try:
        return request.app.state.repo.update_source_system(source_system_id, payload.model_dump(exclude_unset=True), actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source system not found') from exc


@router.delete('/ire/source-systems/{source_system_id}')
def delete_source_system(request: Request, source_system_id: str) -> dict:
    try:
        return request.app.state.repo.deactivate_source_system(source_system_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Source system not found') from exc
