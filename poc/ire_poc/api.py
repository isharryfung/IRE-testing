from __future__ import annotations

import os
import csv
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .demo_repository import DemoRepository
from .models import IdentityRecord
from .oracle_repository import OracleRepository
from .service import IREService


class IdentityPayload(BaseModel):
    source_system: str
    source_pk: str
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    hkid: str = ""
    emplid: str = ""
    student_id: str = ""
    alumni_id: str = ""
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    record: IdentityPayload


class MatchRequest(BaseModel):
    record: IdentityPayload


class ReviewDecisionRequest(BaseModel):
    decision: str
    reviewer: str = "system"
    selected_golden_id: Optional[str] = None
    rationale: str = ""


def _build_service() -> IREService:
    use_oracle = all(os.getenv(key) for key in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN"))
    if use_oracle:
        repository = OracleRepository()
    else:
        sample_path = Path(__file__).resolve().parents[1] / "sample_data" / "golden_records.csv"
        initial_goldens = []
        if sample_path.exists():
            with sample_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    initial_goldens.append(IdentityRecord(**row))
        repository = DemoRepository(initial_goldens=initial_goldens)
    return IREService(repository=repository)


app = FastAPI(title="IRE POC API", version="2.0.0")
SERVICE = _build_service()


@app.get("/health")
def health() -> Dict[str, str]:
    mode = "oracle" if SERVICE.repository.__class__.__name__ == "OracleRepository" else "demo"
    return {"status": "ok", "mode": mode}


@app.post("/poc/ingest")
def ingest(request: IngestRequest) -> Dict[str, Any]:
    record = IdentityRecord(**request.record.model_dump())
    return SERVICE.ingest(record)


@app.post("/poc/match")
def match(request: MatchRequest) -> Dict[str, Any]:
    record = IdentityRecord(**request.record.model_dump())
    return SERVICE.match(record)


@app.get("/poc/golden/{golden_id}")
def get_golden(golden_id: str) -> Dict[str, Any]:
    payload = SERVICE.get_golden(golden_id)
    if not payload:
        raise HTTPException(status_code=404, detail="golden record not found")
    return payload


@app.get("/poc/review/tasks")
def review_tasks() -> Dict[str, Any]:
    return {"tasks": SERVICE.list_review_tasks()}


@app.post("/poc/review/{task_id}/decision")
def submit_review(task_id: int, request: ReviewDecisionRequest) -> Dict[str, Any]:
    try:
        return SERVICE.submit_review_decision(
            task_id=task_id,
            decision=request.decision,
            reviewer=request.reviewer,
            selected_golden_id=request.selected_golden_id,
            rationale=request.rationale,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
