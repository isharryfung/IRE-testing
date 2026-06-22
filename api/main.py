from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional
import re

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Identity Resolution Engine API", version="1.0.0")

AUTO_MERGE_THRESHOLD = 0.85
MANUAL_REVIEW_THRESHOLD = 0.50
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


@dataclass(frozen=True)
class MatchResult:
    decision: str
    confidence: float
    best_match_index: Optional[int]
    best_match_record_id: Optional[str]
    similarities: Dict[str, float]
    explanation: str


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
    incoming_ids = [normalize_text(getattr(incoming, field)) for field in ID_FIELDS if normalize_text(getattr(incoming, field))]
    golden_ids = [normalize_text(getattr(golden, field)) for field in ID_FIELDS if normalize_text(getattr(golden, field))]
    if not incoming_ids or not golden_ids:
        return None
    return 1.0 if set(incoming_ids).intersection(golden_ids) else 0.0


def deterministic_match(incoming: PersonRecord, golden: PersonRecord) -> bool:
    if id_similarity(incoming, golden) != 1.0:
        return False
    if normalize_text(incoming.source_type) in INTERNAL_SOURCES:
        return True
    return exact_similarity(incoming.name, golden.name) == 1.0 and exact_similarity(incoming.email, golden.email) == 1.0


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
    return sum((FIELD_PRIORITIES[field] / priority_sum) * score for field, score in similarities.items())


def match_records(incoming: PersonRecord, golden_records: List[PersonRecord]) -> MatchResult:
    best_index: Optional[int] = None
    best_record_id: Optional[str] = None
    best_confidence = -1.0
    best_similarities: Dict[str, float] = {}

    for index, golden in enumerate(golden_records):
        if deterministic_match(incoming, golden):
            return MatchResult("auto_merge", 1.0, index, golden.record_id, {"deterministic_id_rule": 1.0}, "Deterministic identity rule matched")
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


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "ire-api"}


@app.post("/ingest")
def ingest(request: IngestRequest) -> Dict[str, object]:
    return {
        "status": "accepted",
        "source_name": request.source_name,
        "source_pk": request.source_pk,
        "normalized": {
            "name": normalize_text(request.payload.name),
            "email": normalize_text(request.payload.email),
            "phone": normalize_phone(request.payload.phone),
        },
    }


@app.post("/match")
def match(request: MatchRequest) -> Dict[str, object]:
    return asdict(match_records(request.incoming, request.golden_records))
