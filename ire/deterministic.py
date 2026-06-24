from __future__ import annotations

"""Deterministic rules for Tier 1 identity attributes."""

from typing import Optional

from ire.models import GoldenRecord, NormalizedIdentity, SourceSystem
from ire.normalizer import normalize_email, normalize_hkid, normalize_id, normalize_name


TIER1_FIELDS = (
    ('norm_hkid', 'canonical_hkid', normalize_hkid),
    ('norm_emplid', 'canonical_emplid', normalize_id),
    ('norm_studentid', 'canonical_studentid', normalize_id),
    ('norm_alumniid', 'canonical_alumniid', normalize_id),
)



def has_tier1_conflict(norm: NormalizedIdentity, golden: GoldenRecord) -> bool:
    for norm_attr, golden_attr, normalizer in TIER1_FIELDS:
        norm_value = getattr(norm, norm_attr)
        golden_value = normalizer(getattr(golden, golden_attr))
        if norm_value and golden_value and norm_value != golden_value:
            return True
    return False



def deterministic_check(
    norm: NormalizedIdentity,
    golden: GoldenRecord,
    source_system: SourceSystem,
) -> Optional[str]:
    if has_tier1_conflict(norm, golden):
        return 'conflict'

    any_tier1_match = any(
        getattr(norm, norm_attr) and getattr(norm, norm_attr) == normalizer(getattr(golden, golden_attr))
        for norm_attr, golden_attr, normalizer in TIER1_FIELDS
    )
    if not any_tier1_match:
        return None

    if source_system.is_internal:
        return 'match'

    name_match = norm.norm_name and norm.norm_name == normalize_name(golden.canonical_name)
    email_match = norm.norm_email and norm.norm_email == normalize_email(golden.canonical_email)
    if name_match and email_match:
        return 'match'
    return None
