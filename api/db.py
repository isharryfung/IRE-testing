from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

try:
    import oracledb
except Exception:  # pragma: no cover - optional dependency at runtime
    oracledb = None


@dataclass(frozen=True)
class OracleSettings:
    user: str
    password: str
    dsn: str
    auto_merge_threshold: float
    manual_review_threshold: float


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_settings() -> OracleSettings:
    oracle_password = os.getenv("ORACLE_PASSWORD", "").strip()
    return OracleSettings(
        os.getenv("ORACLE_USER", "").strip(),
        oracle_password,
        os.getenv("ORACLE_DSN", "").strip(),
        _float_env("IRE_AUTO_MERGE_THRESHOLD", 0.85),
        _float_env("IRE_MANUAL_REVIEW_THRESHOLD", 0.50),
    )


SETTINGS = load_settings()


def oracle_enabled(settings: Optional[OracleSettings] = None) -> bool:
    cfg = settings or SETTINGS
    return bool(cfg.user and cfg.password and cfg.dsn and oracledb is not None)


@contextmanager
def get_connection() -> Iterator[Optional["oracledb.Connection"]]:
    if not oracle_enabled():
        yield None
        return

    connect_kwargs = {
        "user": SETTINGS.user,
        "password": SETTINGS.password,
        "dsn": SETTINGS.dsn,
    }
    conn = oracledb.connect(**connect_kwargs)
    try:
        yield conn
    finally:
        conn.close()
