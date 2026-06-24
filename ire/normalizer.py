from __future__ import annotations

"""Normalization helpers for incoming identity data."""

import re
from typing import Optional

from ire.models import NormalizedIdentity, SourceRecord


_WHITESPACE_RE = re.compile(r"\s+")
_NON_DIGIT_RE = re.compile(r"\D+")
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")


def _collapse_spaces(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value.strip())


def normalize_name(value: Optional[str]) -> str:
    return _collapse_spaces((value or "").lower())


def normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def normalize_phone(value: Optional[str]) -> str:
    return _NON_DIGIT_RE.sub("", value or "")


def normalize_address(value: Optional[str]) -> str:
    return _collapse_spaces((value or "").lower())


def normalize_hkid(value: Optional[str]) -> str:
    cleaned = (value or "").upper().replace(" ", "")
    return _NON_ALNUM_RE.sub("", cleaned)


def normalize_id(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def normalize_record(source_record: SourceRecord) -> NormalizedIdentity:
    return NormalizedIdentity(
        source_record_id=source_record.source_record_id,
        norm_name=normalize_name(source_record.raw_name),
        norm_email=normalize_email(source_record.raw_email),
        norm_phone=normalize_phone(source_record.raw_phone),
        norm_address=normalize_address(source_record.raw_address),
        norm_hkid=normalize_hkid(source_record.raw_hkid),
        norm_emplid=normalize_id(source_record.raw_emplid),
        norm_studentid=normalize_id(source_record.raw_studentid),
        norm_alumniid=normalize_id(source_record.raw_alumniid),
    )
