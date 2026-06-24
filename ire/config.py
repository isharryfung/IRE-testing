from __future__ import annotations

"""Runtime configuration for the IRE MVP package."""

from dataclasses import dataclass
import os


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float, got {value!r}") from exc


@dataclass(frozen=True)
class Config:
    IRE_MODE: str = "demo"
    ORACLE_USER: str = ""
    ORACLE_PASSWORD: str = ""
    ORACLE_DSN: str = ""
    IRE_AUTO_MERGE_THRESHOLD: float = 0.85
    IRE_MANUAL_REVIEW_THRESHOLD: float = 0.50
    IRE_MULTI_MATCH_GAP_THRESHOLD: float = 0.10

    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            IRE_MODE=os.getenv('IRE_MODE', 'demo'),
            ORACLE_USER=os.getenv('ORACLE_USER', ''),
            ORACLE_PASSWORD=os.getenv('ORACLE_PASSWORD', ''),
            ORACLE_DSN=os.getenv('ORACLE_DSN', ''),
            IRE_AUTO_MERGE_THRESHOLD=_get_float('IRE_AUTO_MERGE_THRESHOLD', 0.85),
            IRE_MANUAL_REVIEW_THRESHOLD=_get_float('IRE_MANUAL_REVIEW_THRESHOLD', 0.50),
            IRE_MULTI_MATCH_GAP_THRESHOLD=_get_float('IRE_MULTI_MATCH_GAP_THRESHOLD', 0.10),
        )


config = Config.from_env()
