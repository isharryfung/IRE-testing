from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Identity Resolution Engine API", version="1.0.0")

AUTO_MERGE_THRESHOLD = 0.85
MANUAL_REVIEW_THRESHOLD = 0.50
FIELD_PRIORITIES = {"id": 100, "email": 80, "phone": 60, "name": 40, "address": 20}
ID_FIELDS = ("hkid", "emplid", "studentid", "alumniid")
INTERNAL_SOURCES = {"internal", "hr", "sis", "student", "alumni"}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

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


class MergeRequest(BaseModel):
    golden_id: str
    incoming: PersonRecord


@dataclass(frozen=True)
class MatchResult:
    decision: str
    confidence: float
    best_match_index: Optional[int]
    best_match_record_id: Optional[str]
    similarities: Dict[str, float]
    explanation: str


# ---------------------------------------------------------------------------
# Sample golden records loaded from CSV at startup (prototype only)
# ---------------------------------------------------------------------------
_GOLDEN_RECORDS: Dict[str, PersonRecord] = {}


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


# Locate sample CSV relative to this file or from GOLDEN_CSV env var.
_CSV_PATH = Path(
    os.environ.get(
        "GOLDEN_CSV",
        str(Path(__file__).parent.parent / "prototype" / "golden_records.csv"),
    )
)


@app.on_event("startup")
def startup_event() -> None:
    _load_golden_records_csv(_CSV_PATH)


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

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


def _survivorship_merge(incoming: PersonRecord, golden: PersonRecord) -> PersonRecord:
    """Apply simple survivorship rules: fill gaps and prefer internal sources for IDs."""
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
    candidates = request.golden_records if request.golden_records else list(_GOLDEN_RECORDS.values())
    return asdict(match_records(request.incoming, candidates))


@app.post("/merge")
def merge(request: MergeRequest) -> Dict[str, object]:
    golden = _GOLDEN_RECORDS.get(request.golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail=f"Golden record '{request.golden_id}' not found")
    merged = _survivorship_merge(request.incoming, golden)
    _GOLDEN_RECORDS[request.golden_id] = merged
    return {"status": "merged", "golden_id": request.golden_id, "golden_record": merged.model_dump()}


@app.get("/golden/{golden_id}")
def get_golden(golden_id: str) -> Dict[str, object]:
    golden = _GOLDEN_RECORDS.get(golden_id)
    if golden is None:
        raise HTTPException(status_code=404, detail=f"Golden record '{golden_id}' not found")
    return {"golden_id": golden_id, "record": golden.model_dump()}


@app.get("/golden")
def list_golden() -> Dict[str, object]:
    return {"count": len(_GOLDEN_RECORDS), "records": [r.model_dump() for r in _GOLDEN_RECORDS.values()]}
