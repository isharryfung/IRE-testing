from __future__ import annotations

import csv
import os
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .db import SETTINGS, oracle_enabled
    from .repository import DemoRepository, OracleRepository
except ImportError:  # pragma: no cover - support direct execution
    from db import SETTINGS, oracle_enabled
    from repository import DemoRepository, OracleRepository

app = FastAPI(title="Identity Resolution Engine API", version="1.1.0")

AUTO_MERGE_THRESHOLD = SETTINGS.auto_merge_threshold
MANUAL_REVIEW_THRESHOLD = SETTINGS.manual_review_threshold
FIELD_PRIORITIES = {"id": 100, "email": 80, "phone": 60, "name": 40, "address": 20}
ID_FIELDS = ("hkid", "emplid", "studentid", "alumniid")
INTERNAL_SOURCES = {"internal", "hr", "sis", "student", "alumni"}


class PersonRecord(BaseModel):
    record_id: Optional[str] = None
    source_type: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hkid: Optional[str] = None
    emplid: Optional[str] = None
    studentid: Optional[str] = None
    alumniid: Optional[str] = None
    address: Optional[str] = None


class MatchRequest(BaseModel):
    incoming: PersonRecord
    golden_records: List[PersonRecord] = Field(default_factory=list)


class IngestRequest(BaseModel):
    source_name: str
    source_pk: str
    payload: PersonRecord
    run_match: bool = False
    ingest_user: str = "ingest_service"


class MergeRequest(BaseModel):
    golden_id: str
    incoming: PersonRecord
    source_record_id: Optional[int] = None
    confidence: float = 1.0
    link_method: str = "manual"
    actor: str = "system"
    evidence: Dict[str, float] = Field(default_factory=dict)


class ReviewDecisionRequest(BaseModel):
    decision: str
    reviewer_id: str
    notes: Optional[str] = None
    golden_id: Optional[str] = None


@dataclass(frozen=True)
class MatchResult:
    decision: str
    confidence: float
    best_match_index: Optional[int]
    best_match_record_id: Optional[str]
    similarities: Dict[str, float]
    explanation: str


_GOLDEN_RECORDS: Dict[str, PersonRecord] = {}
_REPO: Optional[object] = None
_ORACLE_MODE = False


def _load_golden_records_csv(path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rec = PersonRecord(
                record_id=row.get("record_id") or None,
                source_type=row.get("source_type") or None,
                name=row.get("name") or None,
                email=row.get("email") or None,
                phone=row.get("phone") or None,
                hkid=row.get("hkid") or None,
                emplid=row.get("emplid") or None,
                studentid=row.get("studentid") or None,
                alumniid=row.get("alumniid") or None,
                address=row.get("address") or None,
            )
            if rec.record_id:
                _GOLDEN_RECORDS[rec.record_id] = rec


_CSV_PATH = Path(
    os.environ.get(
        "GOLDEN_CSV",
        str(Path(__file__).parent.parent / "prototype" / "golden_records.csv"),
    )
)


@app.on_event("startup")
def startup_event() -> None:
    global _REPO, _ORACLE_MODE
    _load_golden_records_csv(_CSV_PATH)
    _ORACLE_MODE = oracle_enabled()
    _REPO = OracleRepository() if _ORACLE_MODE else DemoRepository(_GOLDEN_RECORDS)


def normalize_text(value: Optional[str]) -> str:
    return " ".join((value or "").strip().lower().split())


def normalize_phone(value: Optional[str]) -> str:
    return re.sub(r"\D+", "", value or "")


def present(value: Optional[str]) -> bool:
    return bool(normalize_text(value))


def exact_similarity(left: Optional[str], right: Optional[str]) -> Optional[float]:
    if not present(left) or not present(right):
        return None
    return 1.0 if normalize_text(left) == normalize_text(right) else 0.0


def text_similarity(left: Optional[str], right: Optional[str]) -> Optional[float]:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return None
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def phone_similarity(left: Optional[str], right: Optional[str]) -> Optional[float]:
    left_norm = normalize_phone(left)
    right_norm = normalize_phone(right)
    if not left_norm or not right_norm:
        return None
    if left_norm == right_norm:
        return 1.0
    if len(left_norm) >= 7 and len(right_norm) >= 7 and left_norm[-7:] == right_norm[-7:]:
        return 0.85
    return 0.0


def id_similarity(incoming: PersonRecord, golden: PersonRecord) -> Optional[float]:
    incoming_ids = [
        normalize_text(getattr(incoming, field))
        for field in ID_FIELDS
        if normalize_text(getattr(incoming, field))
    ]
    golden_ids = [
        normalize_text(getattr(golden, field))
        for field in ID_FIELDS
        if normalize_text(getattr(golden, field))
    ]
    if not incoming_ids or not golden_ids:
        return None
    return 1.0 if set(incoming_ids).intersection(golden_ids) else 0.0


def deterministic_match(incoming: PersonRecord, golden: PersonRecord) -> bool:
    if id_similarity(incoming, golden) != 1.0:
        return False
    if normalize_text(incoming.source_type) in INTERNAL_SOURCES:
        return True
    return (
        exact_similarity(incoming.name, golden.name) == 1.0
        and exact_similarity(incoming.email, golden.email) == 1.0
    )


def field_similarities(incoming: PersonRecord, golden: PersonRecord) -> Dict[str, float]:
    raw: Dict[str, Optional[float]] = {
        "id": id_similarity(incoming, golden),
        "email": exact_similarity(incoming.email, golden.email),
        "phone": phone_similarity(incoming.phone, golden.phone),
        "name": text_similarity(incoming.name, golden.name),
        "address": text_similarity(incoming.address, golden.address),
    }
    return {field: score for field, score in raw.items() if score is not None}


def weighted_confidence(similarities: Dict[str, float]) -> float:
    if not similarities:
        return 0.0
    priority_sum = sum(FIELD_PRIORITIES[field] for field in similarities)
    return sum(
        (FIELD_PRIORITIES[field] / priority_sum) * score
        for field, score in similarities.items()
    )


def match_records(incoming: PersonRecord, golden_records: List[PersonRecord]) -> MatchResult:
    best_index: Optional[int] = None
    best_record_id: Optional[str] = None
    best_confidence = -1.0
    best_similarities: Dict[str, float] = {}

    for index, golden in enumerate(golden_records):
        if deterministic_match(incoming, golden):
            return MatchResult(
                "auto_merge",
                1.0,
                index,
                golden.record_id,
                {"deterministic_id_rule": 1.0},
                "Deterministic identity rule matched",
            )
        similarities = field_similarities(incoming, golden)
        confidence = weighted_confidence(similarities)
        if confidence > best_confidence:
            best_index = index
            best_record_id = golden.record_id
            best_confidence = confidence
            best_similarities = similarities

    best_confidence = max(best_confidence, 0.0)
    if best_confidence >= AUTO_MERGE_THRESHOLD:
        decision = "auto_merge"
    elif best_confidence >= MANUAL_REVIEW_THRESHOLD:
        decision = "manual_review"
    else:
        decision = "create_new_golden_record"

    return MatchResult(
        decision=decision,
        confidence=round(best_confidence, 6),
        best_match_index=best_index,
        best_match_record_id=best_record_id,
        similarities={field: round(score, 6) for field, score in best_similarities.items()},
        explanation=f"Weighted dynamic-priority score produced {decision}",
    )


def _build_candidates(incoming: PersonRecord, golden_records: List[PersonRecord]) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    for golden in golden_records:
        if deterministic_match(incoming, golden):
            candidates.append(
                {
                    "golden_id": golden.record_id,
                    "confidence": 1.0,
                    "reason": "deterministic_id_rule",
                    "sims": {"deterministic_id_rule": 1.0},
                }
            )
            continue
        sims = field_similarities(incoming, golden)
        candidates.append(
            {
                "golden_id": golden.record_id,
                "confidence": round(weighted_confidence(sims), 6),
                "reason": "weighted_similarity",
                "sims": {field: round(score, 6) for field, score in sims.items()},
            }
        )
    candidates.sort(key=lambda item: float(item["confidence"]), reverse=True)
    return candidates[:5]


def _survivorship_merge(incoming: PersonRecord, golden: PersonRecord) -> PersonRecord:
    data = golden.model_dump()
    for field in ("name", "email", "phone", "hkid", "emplid", "studentid", "alumniid", "address"):
        inc_val = getattr(incoming, field)
        gold_val = data.get(field)
        if not present(gold_val) and present(inc_val):
            data[field] = inc_val
        elif field in ID_FIELDS and normalize_text(incoming.source_type) in INTERNAL_SOURCES and present(inc_val):
            data[field] = inc_val
        elif field in {"name", "address"} and inc_val and gold_val and len(str(inc_val)) > len(str(gold_val)):
            data[field] = inc_val
    return PersonRecord(**data)


def _rows_to_person_records(rows: List[Dict[str, object]]) -> List[PersonRecord]:
    return [
        PersonRecord(
            record_id=str(row.get("golden_id") or row.get("record_id") or ""),
            source_type=row.get("source_type"),
            name=row.get("name"),
            email=row.get("email"),
            phone=row.get("phone"),
            hkid=row.get("hkid"),
            emplid=row.get("emplid"),
            studentid=row.get("studentid"),
            alumniid=row.get("alumniid"),
            address=row.get("address"),
        )
        for row in rows
    ]


def _repo() -> object:
    if _REPO is None:
        raise HTTPException(status_code=503, detail="Repository not initialized")
    return _REPO


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "ire-api",
        "mode": "oracle" if _ORACLE_MODE else "demo",
    }


@app.post("/ingest")
def ingest(request: IngestRequest) -> Dict[str, object]:
    normalized_payload = {
        "name": normalize_text(request.payload.name),
        "email": normalize_text(request.payload.email),
        "phone": normalize_phone(request.payload.phone),
    }

    source_record_id = _repo().insert_source_record(
        source_name=request.source_name,
        source_pk=request.source_pk,
        raw_payload=request.payload.model_dump_json(),
        normalized_name=normalized_payload["name"] or None,
        normalized_email=normalized_payload["email"] or None,
        normalized_phone=normalized_payload["phone"] or None,
        hkid=request.payload.hkid,
        emplid=request.payload.emplid,
        studentid=request.payload.studentid,
        alumniid=request.payload.alumniid,
        address=request.payload.address,
        ingest_user=request.ingest_user,
    )

    response: Dict[str, object] = {
        "status": "accepted",
        "source_name": request.source_name,
        "source_pk": request.source_pk,
        "source_record_id": source_record_id,
        "persistence_mode": "oracle" if _ORACLE_MODE else "demo",
        "normalized": normalized_payload,
    }

    if request.run_match:
        golden_rows = _repo().list_golden_records()
        candidates = _rows_to_person_records(golden_rows)
        match_result = match_records(request.payload, candidates)
        ranked_candidates = _build_candidates(request.payload, candidates)
        match_payload: Dict[str, object] = {
            "decision": match_result.decision,
            "reason": match_result.explanation,
            "confidence": match_result.confidence,
            "best_match_record_id": match_result.best_match_record_id,
            "sims": match_result.similarities,
            "candidates": ranked_candidates,
        }
        if match_result.decision == "manual_review":
            task_id = _repo().insert_manual_review_task(
                source_record_id=source_record_id,
                candidate_goldens=[c["golden_id"] for c in ranked_candidates if c.get("golden_id")],
                best_confidence=match_result.confidence,
            )
            match_payload["manual_review_task_id"] = task_id
            _repo().insert_merge_history_event(
                "review",
                "system",
                {
                    "task_id": task_id,
                    "source_record_id": source_record_id,
                    "decision": match_result.decision,
                },
            )
        response["match"] = match_payload

    return response


@app.post("/match")
def match(request: MatchRequest) -> Dict[str, object]:
    if request.golden_records:
        candidates = request.golden_records
    else:
        candidates = _rows_to_person_records(_repo().list_golden_records())

    result = match_records(request.incoming, candidates)
    payload = asdict(result)
    payload["reason"] = result.explanation
    payload["evidence"] = result.similarities
    payload["sims"] = result.similarities
    payload["candidates"] = _build_candidates(request.incoming, candidates)
    return payload


@app.post("/merge")
def merge(request: MergeRequest) -> Dict[str, object]:
    golden_row = _repo().get_golden_record(request.golden_id)
    if golden_row is None:
        raise HTTPException(status_code=404, detail=f"Golden record '{request.golden_id}' not found")

    golden = PersonRecord(record_id=str(golden_row.get("golden_id")), **{k: v for k, v in golden_row.items() if k != "golden_id"})
    merged = _survivorship_merge(request.incoming, golden)
    _repo().update_golden_record(request.golden_id, {"record": merged})

    if request.source_record_id is not None:
        _repo().insert_record_link(
            source_record_id=request.source_record_id,
            golden_id=request.golden_id,
            confidence=request.confidence,
            link_method=request.link_method,
            evidence=request.evidence,
        )

    _repo().insert_merge_history_event(
        "merge",
        request.actor,
        {
            "golden_id": request.golden_id,
            "source_record_id": request.source_record_id,
            "confidence": request.confidence,
            "link_method": request.link_method,
            "sims": request.evidence,
        },
    )

    return {
        "status": "merged",
        "golden_id": request.golden_id,
        "golden_record": merged.model_dump(),
        "persistence_mode": "oracle" if _ORACLE_MODE else "demo",
    }


@app.get("/golden/{golden_id}")
def get_golden(golden_id: str) -> Dict[str, object]:
    golden = _repo().get_golden_record(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail=f"Golden record '{golden_id}' not found")
    return {"golden_id": golden_id, "record": {k: v for k, v in golden.items() if k != "golden_id"}}


@app.get("/golden")
def list_golden() -> Dict[str, object]:
    records = _repo().list_golden_records()
    formatted = [{k: v for k, v in row.items() if k != "golden_id"} for row in records]
    return {"count": len(formatted), "records": formatted}


@app.get("/review/tasks")
def list_review_tasks() -> Dict[str, object]:
    tasks = _repo().list_open_manual_review_tasks()
    return {"count": len(tasks), "tasks": tasks}


@app.post("/review/{task_id}/decision")
def submit_review_decision(task_id: int, request: ReviewDecisionRequest) -> Dict[str, object]:
    valid_decisions = {"accept", "merge", "reject", "new", "escalate"}
    if request.decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Unsupported decision '{request.decision}'")

    task = _repo().get_manual_review_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    resolved_status = "assigned" if request.decision == "escalate" else "resolved"
    link_created = False

    if request.decision in {"accept", "merge"}:
        golden_id = request.golden_id or (task.get("candidate_goldens") or [None])[0]
        if not golden_id:
            raise HTTPException(status_code=400, detail="Decision requires a candidate golden_id")
        _repo().insert_record_link(
            source_record_id=int(task["source_record_id"]),
            golden_id=str(golden_id),
            confidence=float(task.get("best_confidence") or 1.0),
            link_method="manual",
            evidence={"review_task_id": task_id, "decision": request.decision},
        )
        link_created = True

    _repo().resolve_manual_review_task(
        task_id=task_id,
        decision=request.decision,
        reviewer_id=request.reviewer_id,
        notes=request.notes,
        status=resolved_status,
    )

    _repo().insert_merge_history_event(
        "merge" if link_created else "review",
        request.reviewer_id,
        {
            "task_id": task_id,
            "decision": request.decision,
            "status": resolved_status,
            "notes": request.notes,
        },
    )

    return {
        "status": "recorded",
        "task_id": task_id,
        "decision": request.decision,
        "task_status": resolved_status,
        "link_created": link_created,
    }
