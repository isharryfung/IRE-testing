from __future__ import annotations

"""Survivorship logic for updating golden records."""

from copy import deepcopy
from dataclasses import replace
from typing import Any, Dict

from ire.models import GoldenRecord, SourceRecord, SourceSystem, utc_now
from ire.normalizer import normalize_email, normalize_hkid, normalize_id, normalize_phone


SURVIVORSHIP_STRATEGIES = {
    'hkid': 'trust_best_source',
    'emplid': 'trust_best_source',
    'studentid': 'trust_best_source',
    'alumniid': 'trust_best_source',
    'email': 'most_recent',
    'phone': 'most_recent',
    'name': 'trust_best_source',
    'address': 'most_recent',
}

_FIELD_MAP = {
    'hkid': 'canonical_hkid',
    'emplid': 'canonical_emplid',
    'studentid': 'canonical_studentid',
    'alumniid': 'canonical_alumniid',
    'email': 'canonical_email',
    'phone': 'canonical_phone',
    'name': 'canonical_name',
    'address': 'canonical_address',
}



def build_provenance(golden: GoldenRecord, source_record: SourceRecord, source_system: SourceSystem) -> dict:
    provenance: Dict[str, Any] = deepcopy(golden.provenance)
    for field_name, attr_name in _FIELD_MAP.items():
        raw_value = getattr(source_record, f'raw_{field_name}', None)
        if raw_value in (None, ''):
            continue
        provenance[field_name] = {
            'source_system_id': source_system.system_id,
            'source_system_name': source_system.name,
            'source_pk': source_record.source_pk,
            'source_record_id': source_record.source_record_id,
            'golden_field': attr_name,
        }
    return provenance



def _incoming_values(source_record: SourceRecord) -> Dict[str, str]:
    return {
        'hkid': normalize_hkid(source_record.raw_hkid),
        'emplid': normalize_id(source_record.raw_emplid),
        'studentid': normalize_id(source_record.raw_studentid),
        'alumniid': normalize_id(source_record.raw_alumniid),
        'email': normalize_email(source_record.raw_email),
        'phone': normalize_phone(source_record.raw_phone),
        'name': (source_record.raw_name or '').strip(),
        'address': ' '.join((source_record.raw_address or '').strip().split()),
    }



def apply_survivorship(
    golden: GoldenRecord,
    norm,  # kept for API contract; source values come from source_record
    source_record: SourceRecord,
    source_system: SourceSystem,
) -> GoldenRecord:
    updates = {}
    incoming = _incoming_values(source_record)

    for field_name, strategy in SURVIVORSHIP_STRATEGIES.items():
        attr_name = _FIELD_MAP[field_name]
        current_value = getattr(golden, attr_name) or ''
        incoming_value = incoming[field_name]
        if not incoming_value:
            updates[attr_name] = getattr(golden, attr_name)
            continue
        if not current_value:
            updates[attr_name] = incoming_value
            continue
        if strategy == 'trust_best_source':
            updates[attr_name] = incoming_value if source_system.is_internal else getattr(golden, attr_name)
            continue
        if strategy == 'most_recent':
            updates[attr_name] = incoming_value
            continue
        updates[attr_name] = getattr(golden, attr_name)

    return replace(
        golden,
        provenance=build_provenance(golden, source_record, source_system),
        last_updated=utc_now(),
        **updates,
    )
