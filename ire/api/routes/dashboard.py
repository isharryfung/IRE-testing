from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=['dashboard'])


@router.get('/ire/dashboard/summary')
def dashboard_summary(request: Request) -> dict:
    return request.app.state.repo.dashboard_summary()


@router.get('/ire/dashboard/process-counts')
def dashboard_process_counts(request: Request) -> dict:
    return request.app.state.repo.dashboard_process_counts()


@router.get('/ire/dashboard/recent-activity')
def dashboard_recent_activity(request: Request) -> list[dict]:
    return request.app.state.repo.dashboard_recent_activity(limit=20)
