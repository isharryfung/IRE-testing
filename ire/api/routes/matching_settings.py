from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=['matching-settings'])


class FeaturePayload(BaseModel):
    feature_id: str | None = None
    feature_name: str
    display_label: str | None = None
    feature_type: str = 'profile'
    is_enabled: bool = True
    priority: int = 10
    algorithm: str = 'sequence_matcher'
    is_auto_merge_eligible: bool = True
    is_manual_review_only: bool = False
    is_blocking: bool = False
    is_visible_in_review: bool = True
    is_active: bool = True
    actor: str = 'api'


class RulePayload(BaseModel):
    rule_id: str | None = None
    rule_name: str
    description: str = ''
    rule_type: str = 'probabilistic'
    conditions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    change_reason: str = 'Updated from API'
    actor: str = 'api'


class SimulationPayload(BaseModel):
    simulation_name: str
    rule_snapshot: Dict[str, Any] = Field(default_factory=dict)
    tighten_auto_merge: bool = False
    actor: str = 'api'


class ThresholdPayload(BaseModel):
    auto_merge: float | None = None
    manual_review: float | None = None
    new_golden: float | None = None
    multi_match_gap: float | None = None
    actor: str = 'api'


@router.get('/ire/matching-features')
def list_features(request: Request) -> list[dict]:
    return request.app.state.repo.list_matching_features()


@router.post('/ire/matching-features', status_code=201)
def create_feature(request: Request, payload: FeaturePayload) -> dict:
    return request.app.state.repo.create_matching_feature(payload.model_dump(), actor=payload.actor)


@router.get('/ire/matching-features/{feature_id}')
def get_feature(request: Request, feature_id: str) -> dict:
    feature = request.app.state.repo.get_matching_feature(feature_id)
    if feature is None:
        raise HTTPException(status_code=404, detail='Matching feature not found')
    return feature


@router.put('/ire/matching-features/{feature_id}')
def update_feature(request: Request, feature_id: str, payload: FeaturePayload) -> dict:
    try:
        return request.app.state.repo.update_matching_feature(feature_id, payload.model_dump(exclude_unset=True), actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Matching feature not found') from exc


@router.delete('/ire/matching-features/{feature_id}')
def delete_feature(request: Request, feature_id: str) -> dict:
    try:
        return request.app.state.repo.deactivate_matching_feature(feature_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Matching feature not found') from exc


@router.get('/ire/matching-rules')
def list_rules(request: Request) -> list[dict]:
    return request.app.state.repo.list_matching_rules()


@router.post('/ire/matching-rules', status_code=201)
def create_rule(request: Request, payload: RulePayload) -> dict:
    return request.app.state.repo.create_matching_rule(payload.model_dump(), actor=payload.actor)


@router.get('/ire/matching-rules/{rule_id}')
def get_rule(request: Request, rule_id: str) -> dict:
    rule = request.app.state.repo.get_matching_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail='Matching rule not found')
    return rule


@router.put('/ire/matching-rules/{rule_id}')
def update_rule(request: Request, rule_id: str, payload: RulePayload) -> dict:
    try:
        return request.app.state.repo.update_matching_rule(rule_id, payload.model_dump(exclude_unset=True), actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Matching rule not found') from exc


@router.delete('/ire/matching-rules/{rule_id}')
def delete_rule(request: Request, rule_id: str) -> dict:
    try:
        return request.app.state.repo.deactivate_matching_rule(rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Matching rule not found') from exc


@router.get('/ire/matching-rules/{rule_id}/versions')
def rule_versions(request: Request, rule_id: str) -> list[dict]:
    rule = request.app.state.repo.get_matching_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail='Matching rule not found')
    return request.app.state.repo.list_matching_rule_versions(rule_id)


@router.post('/ire/rule-simulation', status_code=201)
def create_simulation(request: Request, payload: SimulationPayload) -> dict:
    return request.app.state.repo.create_rule_simulation(payload.model_dump(), actor=payload.actor)


@router.get('/ire/rule-simulation/{simulation_id}')
def get_simulation(request: Request, simulation_id: str) -> dict:
    simulation = request.app.state.repo.get_rule_simulation(simulation_id)
    if simulation is None:
        raise HTTPException(status_code=404, detail='Simulation not found')
    return simulation


@router.get('/ire/rule-simulation/{simulation_id}/results')
def get_simulation_results(request: Request, simulation_id: str) -> list[dict]:
    simulation = request.app.state.repo.get_rule_simulation(simulation_id)
    if simulation is None:
        raise HTTPException(status_code=404, detail='Simulation not found')
    return request.app.state.repo.get_rule_simulation_results(simulation_id)


@router.get('/ire/settings/thresholds')
def get_thresholds(request: Request) -> list[dict]:
    return request.app.state.repo.get_thresholds()


@router.put('/ire/settings/thresholds')
def update_thresholds(request: Request, payload: ThresholdPayload) -> list[dict]:
    return request.app.state.repo.update_thresholds(payload.model_dump(exclude_none=True), actor=payload.actor)
