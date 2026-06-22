"""Prototype Identity Resolution Engine library.

Implements deterministic matching, probabilistic scoring with dynamic field
priorities, basic survivorship merging, and CSV-friendly record handling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, Optional
import re

AUTO_MERGE_THRESHOLD = 0.85
MANUAL_REVIEW_THRESHOLD = 0.50

FIELD_PRIORITIES: Dict[str, int] = {
    "id": 100,
    "email": 80,
    "phone": 60,
    "name": 40,
    "address": 20,
}

ID_FIELDS = ("hkid", "emplid", "studentid", "alumniid")
INTERNAL_SOURCES = {"internal", "hr", "sis", "student", "alumni"}


@dataclass(frozen=True)
class MatchResult:
    decision: str
    confidence: float
    best_match_index: Optional[int]
    best_match_record_id: Optional[str]
    similarities: Dict[str, float]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_text(value: Optional[str]) -> str:
    return " ".join((value or "").strip().lower().split())


def normalize_email(value: Optional[str]) -> str:
    return normalize_text(value)


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


def id_values(record: Dict[str, Any]) -> list[str]:
    return [normalize_text(record.get(field)) for field in ID_FIELDS if normalize_text(record.get(field))]


def id_similarity(incoming: Dict[str, Any], golden: Dict[str, Any]) -> Optional[float]:
    incoming_ids = id_values(incoming)
    golden_ids = id_values(golden)
    if not incoming_ids or not golden_ids:
        return None
    return 1.0 if set(incoming_ids).intersection(golden_ids) else 0.0


def source_type(record: Dict[str, Any]) -> str:
    return normalize_text(record.get("source_type") or record.get("source_name"))


def deterministic_match(incoming: Dict[str, Any], golden: Dict[str, Any]) -> bool:
    """Apply rigid exact-match rules before probabilistic scoring."""
    if id_similarity(incoming, golden) != 1.0:
        return False

    if source_type(incoming) in INTERNAL_SOURCES:
        return True

    name_match = exact_similarity(incoming.get("name"), golden.get("name")) == 1.0
    email_match = exact_similarity(incoming.get("email"), golden.get("email")) == 1.0
    return name_match and email_match


def field_similarities(incoming: Dict[str, Any], golden: Dict[str, Any]) -> Dict[str, float]:
    similarities: Dict[str, Optional[float]] = {
        "id": id_similarity(incoming, golden),
        "email": exact_similarity(incoming.get("email"), golden.get("email")),
        "phone": phone_similarity(incoming.get("phone"), golden.get("phone")),
        "name": text_similarity(incoming.get("name"), golden.get("name")),
        "address": text_similarity(incoming.get("address"), golden.get("address")),
    }
    return {field: score for field, score in similarities.items() if score is not None}


def weighted_confidence(similarities: Dict[str, float]) -> float:
    if not similarities:
        return 0.0
    priority_sum = sum(FIELD_PRIORITIES[field] for field in similarities)
    return sum((FIELD_PRIORITIES[field] / priority_sum) * score for field, score in similarities.items())


def decision_for_confidence(confidence: float) -> str:
    if confidence >= AUTO_MERGE_THRESHOLD:
        return "auto_merge"
    if confidence >= MANUAL_REVIEW_THRESHOLD:
        return "manual_review"
    return "create_new_golden_record"


def match_record(incoming: Dict[str, Any], golden_records: Iterable[Dict[str, Any]]) -> MatchResult:
    best_index: Optional[int] = None
    best_record_id: Optional[str] = None
    best_confidence = -1.0
    best_similarities: Dict[str, float] = {}

    for index, golden in enumerate(golden_records):
        if deterministic_match(incoming, golden):
            return MatchResult(
                decision="auto_merge",
                confidence=1.0,
                best_match_index=index,
                best_match_record_id=golden.get("record_id") or golden.get("golden_id"),
                similarities={"deterministic_id_rule": 1.0},
                explanation="Deterministic identity rule matched",
            )

        similarities = field_similarities(incoming, golden)
        confidence = weighted_confidence(similarities)
        if confidence > best_confidence:
            best_index = index
            best_record_id = golden.get("record_id") or golden.get("golden_id")
            best_confidence = confidence
            best_similarities = similarities

    if best_confidence < 0:
        best_confidence = 0.0

    decision = decision_for_confidence(best_confidence)
    return MatchResult(
        decision=decision,
        confidence=round(best_confidence, 6),
        best_match_index=best_index,
        best_match_record_id=best_record_id,
        similarities={k: round(v, 6) for k, v in best_similarities.items()},
        explanation=f"Weighted dynamic-priority score produced {decision}",
    )


def merge_record(incoming: Dict[str, Any], golden: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simple golden record using trust/most-complete survivorship."""
    merged = dict(golden)
    for field in ("name", "email", "phone", "hkid", "emplid", "studentid", "alumniid", "address"):
        incoming_value = incoming.get(field)
        golden_value = merged.get(field)
        if not present(golden_value) and present(incoming_value):
            merged[field] = incoming_value
        elif field in ID_FIELDS and source_type(incoming) in INTERNAL_SOURCES and present(incoming_value):
            merged[field] = incoming_value
        elif field in {"name", "address"} and len(str(incoming_value or "")) > len(str(golden_value or "")):
            merged[field] = incoming_value
    merged["last_merge_decision"] = "prototype_survivorship"
    return merged
