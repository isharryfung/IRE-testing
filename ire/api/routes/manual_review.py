from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=['manual-review'])


class AssignPayload(BaseModel):
    assigned_to: str
    actor: str = 'api'


class DecisionPayload(BaseModel):
    reviewer: str
    decision: str
    selected_golden_id: Optional[str] = None
    notes: str = ''


@router.get('/ire/review/tasks')
def list_tasks(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    reason_code: Optional[str] = None,
    assigned_to: Optional[str] = None,
    source_system: Optional[str] = None,
) -> list[dict]:
    return request.app.state.repo.list_review_tasks_data({
        'status': status,
        'priority': priority,
        'reason_code': reason_code,
        'assigned_to': assigned_to,
        'source_system': source_system,
    })


@router.get('/ire/review/tasks/{task_id}')
def get_task(request: Request, task_id: str) -> dict:
    task = request.app.state.repo.get_review_task_detail(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Review task not found')
    return task


@router.post('/ire/review/tasks/{task_id}/assign')
def assign_task(request: Request, task_id: str, payload: AssignPayload) -> dict:
    try:
        return request.app.state.repo.assign_review_task(task_id, payload.assigned_to, actor=payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Review task not found') from exc


@router.post('/ire/review/tasks/{task_id}/decision')
def submit_decision(request: Request, task_id: str, payload: DecisionPayload) -> dict:
    try:
        return request.app.state.repo.submit_review_decision(task_id, payload.model_dump(), actor=payload.reviewer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Review task not found') from exc


@router.get('/ire/review/tasks/{task_id}/history')
def get_task_history(request: Request, task_id: str) -> list[dict]:
    task = request.app.state.repo.get_review_task_detail(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Review task not found')
    return request.app.state.repo.list_review_task_history(task_id)


@router.get('/ire/review/decisions')
def list_decisions(request: Request) -> list[dict]:
    return request.app.state.repo.list_review_decisions()
