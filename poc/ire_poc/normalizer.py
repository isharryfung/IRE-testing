from __future__ import annotations

import re
from typing import Dict

from .models import IdentityRecord


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def normalize_name(value: str) -> str:
    return normalize_text(value)


def normalize_email(value: str) -> str:
    return normalize_text(value)


def normalize_phone(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def normalize_address(value: str) -> str:
    return normalize_text(value)


def normalize_hkid(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", value or "").upper()


def normalize_id(value: str) -> str:
    return normalize_text(value)


def normalize_record(record: IdentityRecord) -> IdentityRecord:
    return IdentityRecord(
        source_system=normalize_text(record.source_system).upper(),
        source_pk=record.source_pk,
        name=normalize_name(record.name),
        email=normalize_email(record.email),
        phone=normalize_phone(record.phone),
        address=normalize_address(record.address),
        hkid=normalize_hkid(record.hkid),
        emplid=normalize_id(record.emplid),
        student_id=normalize_id(record.student_id),
        alumni_id=normalize_id(record.alumni_id),
        raw_payload=record.raw_payload or {},
    )
