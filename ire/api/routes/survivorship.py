from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['survivorship'])


class SurvivorshipRulePayload(BaseModel):
    rule_id: str | None = None
    field_name: str
    rule_name: str
    strategy: str = 'most_recent'
    priority_source_systems: List[str] = Field(default_factory=list)
    is_active: bool = True
    actor: str = 'api'


class PreviewPayload(BaseModel):
    golden_id: str


@router.get('/ire/survivorship-rules')
def list_rules(request: Request) -> list[dict]:
    return request.app.state.repo.list_survivorship_rules()


@router.post('/ire/survivorship-rules', status_code=201)
def create_rule(request: Request, payload: SurvivorshipRulePayload) -> dict:
    return request.app.state.repo.create_survivorship_rule(payload.model_dump(), actor=payload.actor)


@router.get('/ire/survivorship-rules/{rule_id}')
def get_rule(request: Request, rule_id: str) -> dict:
    rule = request.app.state.repo.get_survivorship_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail='Survivorship rule not found')
    return rule


@router.put('/ire/survivorship-rules/{rule_id}')
def update_rule(request: Request, rule_id: str, payload: SurvivorshipRulePayload) -> dict:
    try:
        return request.app.state.repo.update_survivorship_rule(rule_id, payload.model_dump(exclude_unset=True), actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Survivorship rule not found') from exc


@router.delete('/ire/survivorship-rules/{rule_id}')
def delete_rule(request: Request, rule_id: str) -> dict:
    try:
        return request.app.state.repo.deactivate_survivorship_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Survivorship rule not found') from exc


@router.get('/ire/survivorship-rules/{rule_id}/versions')
def get_versions(request: Request, rule_id: str) -> list[dict]:
    rule = request.app.state.repo.get_survivorship_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail='Survivorship rule not found')
    return request.app.state.repo.list_survivorship_rule_versions(rule_id)


@router.post('/ire/survivorship/preview')
def preview_survivorship(request: Request, payload: PreviewPayload) -> dict:
    try:
        return request.app.state.repo.preview_survivorship(payload.golden_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Golden record not found') from exc
