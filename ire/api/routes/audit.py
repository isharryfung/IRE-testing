from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=['audit'])


@router.get('/ire/audit-events')
def list_audit_events(
    request: Request,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor: Optional[str] = None,
) -> list[dict]:
    return request.app.state.repo.list_audit_events({
        'event_type': event_type,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'actor': actor,
    })


@router.get('/ire/audit-events/{event_id}')
def get_audit_event(request: Request, event_id: str) -> dict:
    event = request.app.state.repo.get_audit_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail='Audit event not found')
    return event
