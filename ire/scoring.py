from __future__ import annotations

"""Weighted candidate scoring for the IRE MVP package."""

from difflib import SequenceMatcher
from typing import List, Tuple
from uuid import uuid4

from ire.models import GoldenRecord, MatchCandidateFeature, NormalizedIdentity
from ire.normalizer import normalize_address, normalize_email, normalize_hkid, normalize_id, normalize_name, normalize_phone


FIELD_PRIORITIES = {
    'hkid': 100,
    'emplid': 100,
    'studentid': 100,
    'alumniid': 100,
    'email': 80,
    'phone': 60,
    'name': 40,
    'address': 20,
}

_TIER1_FIELDS = {'hkid', 'emplid', 'studentid', 'alumniid'}



def _last8(phone: str) -> str:
    return phone[-8:] if len(phone) >= 8 else phone



def _field_values(norm: NormalizedIdentity, golden: GoldenRecord, field_name: str) -> Tuple[str, str, str, str, str, str]:
    if field_name == 'hkid':
        return norm.norm_hkid, (golden.canonical_hkid or ''), norm.norm_hkid, normalize_hkid(golden.canonical_hkid), 'identifier', 'exact_match'
    if field_name == 'emplid':
        return norm.norm_emplid, (golden.canonical_emplid or ''), norm.norm_emplid, normalize_id(golden.canonical_emplid), 'identifier', 'exact_match'
    if field_name == 'studentid':
        return norm.norm_studentid, (golden.canonical_studentid or ''), norm.norm_studentid, normalize_id(golden.canonical_studentid), 'identifier', 'exact_match'
    if field_name == 'alumniid':
        return norm.norm_alumniid, (golden.canonical_alumniid or ''), norm.norm_alumniid, normalize_id(golden.canonical_alumniid), 'identifier', 'exact_match'
    if field_name == 'email':
        return norm.norm_email, (golden.canonical_email or ''), norm.norm_email, normalize_email(golden.canonical_email), 'contact', 'exact_match'
    if field_name == 'phone':
        return norm.norm_phone, (golden.canonical_phone or ''), norm.norm_phone, normalize_phone(golden.canonical_phone), 'contact', 'phone_exact_or_last8'
    if field_name == 'name':
        return norm.norm_name, (golden.canonical_name or ''), norm.norm_name, normalize_name(golden.canonical_name), 'profile', 'sequence_matcher'
    if field_name == 'address':
        return norm.norm_address, (golden.canonical_address or ''), norm.norm_address, normalize_address(golden.canonical_address), 'profile', 'sequence_matcher'
    raise KeyError(f'Unknown field {field_name}')



def _similarity(field_name: str, source_value: str, golden_value: str) -> float:
    if field_name in _TIER1_FIELDS or field_name == 'email':
        return 1.0 if source_value == golden_value else 0.0
    if field_name == 'phone':
        if source_value == golden_value:
            return 1.0
        if source_value and golden_value and _last8(source_value) == _last8(golden_value):
            return 0.85
        return 0.0
    return SequenceMatcher(None, source_value, golden_value).ratio()



def score_candidate(
    norm: NormalizedIdentity,
    golden: GoldenRecord,
) -> Tuple[float, List[MatchCandidateFeature]]:
    present_fields = []
    materialized = {}
    for field_name, priority in FIELD_PRIORITIES.items():
        values = _field_values(norm, golden, field_name)
        normalized_source = values[2]
        normalized_golden = values[3]
        if normalized_source and normalized_golden:
            present_fields.append((field_name, priority))
            materialized[field_name] = values

    if not present_fields:
        return 0.0, []

    priority_sum = sum(priority for _, priority in present_fields)
    features: List[MatchCandidateFeature] = []
    total_score = 0.0

    for field_name, priority in present_fields:
        source_value, golden_value, normalized_source, normalized_golden, feature_type, algorithm = materialized[field_name]
        similarity_score = _similarity(field_name, normalized_source, normalized_golden)
        weight = priority / priority_sum
        weighted_score = similarity_score * weight
        is_conflict = field_name in _TIER1_FIELDS and similarity_score == 0.0 and bool(normalized_source and normalized_golden)
        feature = MatchCandidateFeature(
            feature_id=str(uuid4()),
            candidate_id='',
            feature_name=field_name,
            feature_type=feature_type,
            source_value=source_value,
            golden_value=golden_value,
            normalized_source_value=normalized_source,
            normalized_golden_value=normalized_golden,
            similarity_algorithm=algorithm,
            similarity_score=similarity_score,
            priority=priority,
            weight=weight,
            weighted_score=weighted_score,
            is_match=similarity_score >= 0.8,
            is_conflict=is_conflict,
            is_blocking_feature=is_conflict,
            evidence_json='{}',
        )
        features.append(feature)
        total_score += weighted_score

    return total_score, features
