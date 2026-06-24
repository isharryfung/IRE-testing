from __future__ import annotations

"""Dataclasses used by the IRE MVP package."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SourceSystem:
    system_id: str
    name: str
    trust_level: str
    is_internal: bool


@dataclass
class SourceRecord:
    source_record_id: str
    system_id: str
    source_pk: str
    raw_name: Optional[str] = None
    raw_email: Optional[str] = None
    raw_phone: Optional[str] = None
    raw_address: Optional[str] = None
    raw_hkid: Optional[str] = None
    raw_emplid: Optional[str] = None
    raw_studentid: Optional[str] = None
    raw_alumniid: Optional[str] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    ingest_ts: datetime = field(default_factory=utc_now)


@dataclass
class NormalizedIdentity:
    source_record_id: str
    norm_name: str = ""
    norm_email: str = ""
    norm_phone: str = ""
    norm_address: str = ""
    norm_hkid: str = ""
    norm_emplid: str = ""
    norm_studentid: str = ""
    norm_alumniid: str = ""


@dataclass
class GoldenRecord:
    golden_id: str
    canonical_name: Optional[str] = None
    canonical_email: Optional[str] = None
    canonical_phone: Optional[str] = None
    canonical_hkid: Optional[str] = None
    canonical_emplid: Optional[str] = None
    canonical_studentid: Optional[str] = None
    canonical_alumniid: Optional[str] = None
    canonical_address: Optional[str] = None
    person_type: str = "person"
    status: str = "active"
    provenance: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=utc_now)


@dataclass
class RecordLink:
    link_id: str
    source_record_id: str
    golden_id: str
    confidence: float
    method: str
    evidence_json: str = "[]"
    link_ts: datetime = field(default_factory=utc_now)


@dataclass
class MatchCandidate:
    candidate_id: str
    source_record_id: str
    golden_id: Optional[str]
    overall_score: float
    deterministic_result: Optional[str]
    safety_flags: List[str] = field(default_factory=list)
    decision: str = ""
    created_ts: datetime = field(default_factory=utc_now)


@dataclass
class MatchCandidateFeature:
    feature_id: str
    candidate_id: str
    feature_name: str
    feature_type: str
    source_value: str
    golden_value: str
    normalized_source_value: str
    normalized_golden_value: str
    similarity_algorithm: str
    similarity_score: float
    priority: int
    weight: float
    weighted_score: float
    is_match: bool
    is_conflict: bool
    is_blocking_feature: bool
    evidence_json: str = "{}"


@dataclass
class ManualReviewTask:
    task_id: str
    source_record_id: str
    candidate_golden_ids: List[str] = field(default_factory=list)
    best_confidence: float = 0.0
    status: str = "open"
    assigned_to: Optional[str] = None
    created_ts: datetime = field(default_factory=utc_now)
    resolved_ts: Optional[datetime] = None
    reason: str = ""


@dataclass
class ManualReviewDecision:
    task_id: str
    reviewer: str
    decision: str
    golden_id: Optional[str]
    notes: str = ""
    decided_ts: datetime = field(default_factory=utc_now)


@dataclass
class MergeHistoryEvent:
    event_id: str
    event_type: str
    actor: str
    source_record_id: Optional[str] = None
    golden_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    event_ts: datetime = field(default_factory=utc_now)


@dataclass
class MatchDecision:
    decision: str
    confidence: float
    best_golden_id: Optional[str] = None
    reason: str = ""
    candidate_count: int = 0
    safety_flags: List[str] = field(default_factory=list)
    features: List[MatchCandidateFeature] = field(default_factory=list)
