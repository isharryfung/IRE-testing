from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


TIER1_FIELDS = ("hkid", "emplid", "student_id", "alumni_id")


@dataclass
class IdentityRecord:
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
    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchCandidateFeature:
    feature_type: str
    field_name: str
    rule_code: str
    similarity: float
    weight: float
    weighted_score: float
    passed: bool
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchCandidate:
    golden_id: str
    confidence: float
    rank: int
    blocked_reason: Optional[str]
    summary: Dict[str, Any] = field(default_factory=dict)
    features: List[MatchCandidateFeature] = field(default_factory=list)


@dataclass
class MatchDecision:
    decision: str
    reason: str
    confidence: float
    best_golden_id: Optional[str]
    candidate_count: int
    candidates: List[MatchCandidate] = field(default_factory=list)
