from __future__ import annotations

"""Candidate generation via simple blocking rules."""

from typing import Dict, List

from ire.models import GoldenRecord, NormalizedIdentity
from ire.normalizer import normalize_email, normalize_hkid, normalize_id, normalize_name, normalize_phone


TIER1_FIELDS = {
    'hkid': ('norm_hkid', 'canonical_hkid', normalize_hkid),
    'emplid': ('norm_emplid', 'canonical_emplid', normalize_id),
    'studentid': ('norm_studentid', 'canonical_studentid', normalize_id),
    'alumniid': ('norm_alumniid', 'canonical_alumniid', normalize_id),
}



def _last8(phone: str) -> str:
    return phone[-8:] if len(phone) >= 8 else phone



def generate_candidates(norm: NormalizedIdentity, golden_records: List[GoldenRecord]) -> List[GoldenRecord]:
    candidates: Dict[str, GoldenRecord] = {}

    for golden in golden_records:
        matched = False

        for norm_attr, golden_attr, normalizer in TIER1_FIELDS.values():
            norm_value = getattr(norm, norm_attr)
            golden_value = normalizer(getattr(golden, golden_attr))
            if norm_value and golden_value and norm_value == golden_value:
                matched = True
                break

        if not matched:
            norm_email = norm.norm_email
            golden_email = normalize_email(golden.canonical_email)
            if norm_email and golden_email and norm_email == golden_email:
                matched = True

        if not matched:
            norm_phone = norm.norm_phone
            golden_phone = normalize_phone(golden.canonical_phone)
            if norm_phone and golden_phone:
                if norm_phone == golden_phone or _last8(norm_phone) == _last8(golden_phone):
                    matched = True

        if not matched and norm.norm_name:
            golden_name = normalize_name(golden.canonical_name)
            tokens = [token for token in norm.norm_name.split() if token]
            if golden_name and any(token in golden_name for token in tokens):
                matched = True

        if matched:
            candidates[golden.golden_id] = golden

    return list(candidates.values()) if candidates else list(golden_records)
