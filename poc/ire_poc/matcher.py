from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .models import IdentityRecord, MatchCandidate, MatchCandidateFeature, TIER1_FIELDS

FIELD_PRIORITIES: Dict[str, int] = {
    "hkid": 100,
    "emplid": 100,
    "student_id": 100,
    "alumni_id": 100,
    "email": 80,
    "phone": 60,
    "name": 40,
    "address": 20,
}

INTERNAL_SOURCES = {"INTERNAL", "HR", "SIS", "STUDENT", "ALUMNI"}
THIRD_PARTY_SOURCES = {"THIRDPARTY", "THIRD_PARTY", "CRM"}


def _present(value: str) -> bool:
    return bool((value or "").strip())


def _text_similarity(left: str, right: str) -> Optional[float]:
    if not _present(left) or not _present(right):
        return None
    return SequenceMatcher(None, left, right).ratio()


def _exact_similarity(left: str, right: str) -> Optional[float]:
    if not _present(left) or not _present(right):
        return None
    return 1.0 if left == right else 0.0


def _phone_similarity(left: str, right: str) -> Optional[float]:
    if not _present(left) or not _present(right):
        return None
    if left == right:
        return 1.0
    if len(left) >= 7 and len(right) >= 7 and left[-7:] == right[-7:]:
        return 0.85
    return 0.0


def _name_block_key(name: str) -> str:
    return (name or "")[:4]


def _tier1_match_fields(incoming: IdentityRecord, golden: IdentityRecord) -> List[str]:
    matches: List[str] = []
    for field in TIER1_FIELDS:
        left = getattr(incoming, field)
        right = getattr(golden, field)
        if _present(left) and _present(right) and left == right:
            matches.append(field)
    return matches


def tier1_conflicts(incoming: IdentityRecord, golden: IdentityRecord) -> List[str]:
    conflicts: List[str] = []
    for field in TIER1_FIELDS:
        left = getattr(incoming, field)
        right = getattr(golden, field)
        if _present(left) and _present(right) and left != right:
            conflicts.append(field)
    return conflicts


def generate_candidates(incoming: IdentityRecord, golden_records: Iterable[IdentityRecord]) -> List[IdentityRecord]:
    id_hits: List[IdentityRecord] = []
    email_hits: List[IdentityRecord] = []
    phone_hits: List[IdentityRecord] = []
    name_hits: List[IdentityRecord] = []

    for golden in golden_records:
        if _tier1_match_fields(incoming, golden):
            id_hits.append(golden)
            continue
        if _present(incoming.email) and incoming.email == golden.email:
            email_hits.append(golden)
            continue
        phone_sim = _phone_similarity(incoming.phone, golden.phone)
        if _present(incoming.phone) and phone_sim is not None and phone_sim > 0:
            phone_hits.append(golden)
            continue
        if _present(incoming.name) and _name_block_key(incoming.name) == _name_block_key(golden.name):
            name_hits.append(golden)

    merged: List[IdentityRecord] = []
    seen: Set[str] = set()
    for bucket in (id_hits, email_hits, phone_hits, name_hits):
        for record in bucket:
            if record.source_pk not in seen:
                seen.add(record.source_pk)
                merged.append(record)
    return merged


def _probabilistic_features(incoming: IdentityRecord, golden: IdentityRecord) -> Tuple[float, List[MatchCandidateFeature]]:
    sims = {
        "hkid": _exact_similarity(incoming.hkid, golden.hkid),
        "emplid": _exact_similarity(incoming.emplid, golden.emplid),
        "student_id": _exact_similarity(incoming.student_id, golden.student_id),
        "alumni_id": _exact_similarity(incoming.alumni_id, golden.alumni_id),
        "email": _exact_similarity(incoming.email, golden.email),
        "phone": _phone_similarity(incoming.phone, golden.phone),
        "name": _text_similarity(incoming.name, golden.name),
        "address": _text_similarity(incoming.address, golden.address),
    }

    comparable = {field: score for field, score in sims.items() if score is not None and _present(getattr(incoming, field))}
    if not comparable:
        return 0.0, []

    priority_sum = sum(FIELD_PRIORITIES[field] for field in comparable)
    features: List[MatchCandidateFeature] = []
    confidence = 0.0
    for field, sim in comparable.items():
        weight = FIELD_PRIORITIES[field] / priority_sum
        weighted_score = weight * sim
        confidence += weighted_score
        features.append(
            MatchCandidateFeature(
                feature_type="field_similarity",
                field_name=field,
                rule_code="PROB_DYNAMIC_WEIGHT",
                similarity=round(sim, 6),
                weight=round(weight, 6),
                weighted_score=round(weighted_score, 6),
                passed=sim >= 0.5,
                evidence={"priority": FIELD_PRIORITIES[field]},
            )
        )

    return confidence, features


def score_candidate(incoming: IdentityRecord, golden: IdentityRecord, rank: int) -> MatchCandidate:
    conflicts = tier1_conflicts(incoming, golden)
    tier1_fields = _tier1_match_fields(incoming, golden)

    supporting_evidence = (
        _exact_similarity(incoming.email, golden.email) == 1.0
        or _phone_similarity(incoming.phone, golden.phone) in {1.0, 0.85}
        or (_text_similarity(incoming.name, golden.name) or 0.0) >= 0.9
    )

    deterministic_auto = False
    blocked_reason: Optional[str] = None
    deterministic_features: List[MatchCandidateFeature] = []

    if conflicts:
        blocked_reason = f"tier1_conflict:{','.join(conflicts)}"

    if tier1_fields:
        if incoming.source_system in INTERNAL_SOURCES and not conflicts:
            deterministic_auto = True
            deterministic_features.append(
                MatchCandidateFeature(
                    feature_type="rule",
                    field_name="tier1",
                    rule_code="TIER1_INTERNAL_EXACT",
                    similarity=1.0,
                    weight=1.0,
                    weighted_score=1.0,
                    passed=True,
                    evidence={"matched_fields": tier1_fields},
                )
            )
        elif incoming.source_system in THIRD_PARTY_SOURCES:
            passed = supporting_evidence and not conflicts
            deterministic_features.append(
                MatchCandidateFeature(
                    feature_type="rule",
                    field_name="tier1",
                    rule_code="TIER1_THIRDPARTY_SUPPORT",
                    similarity=1.0 if passed else 0.0,
                    weight=1.0,
                    weighted_score=1.0 if passed else 0.0,
                    passed=passed,
                    evidence={"matched_fields": tier1_fields, "supporting_evidence": supporting_evidence},
                )
            )
            deterministic_auto = passed

    if deterministic_auto:
        return MatchCandidate(
            golden_id=golden.source_pk,
            confidence=1.0,
            rank=rank,
            blocked_reason=blocked_reason,
            summary={"path": "deterministic", "tier1_fields": tier1_fields},
            features=deterministic_features,
        )

    confidence, probabilistic_features = _probabilistic_features(incoming, golden)
    features = deterministic_features + probabilistic_features
    return MatchCandidate(
        golden_id=golden.source_pk,
        confidence=round(confidence, 6),
        rank=rank,
        blocked_reason=blocked_reason,
        summary={"path": "probabilistic", "tier1_fields": tier1_fields, "supporting_evidence": supporting_evidence},
        features=features,
    )


def rank_candidates(incoming: IdentityRecord, golden_records: Iterable[IdentityRecord]) -> List[MatchCandidate]:
    candidates = generate_candidates(incoming, golden_records)
    scored = [score_candidate(incoming, golden, index + 1) for index, golden in enumerate(candidates)]
    scored.sort(key=lambda item: item.confidence, reverse=True)
    return [replace(candidate, rank=index + 1) for index, candidate in enumerate(scored)]
