from __future__ import annotations

"""Safety checks applied before final IRE decisions."""

from typing import List, Tuple

from ire.config import Config
from ire.deterministic import has_tier1_conflict
from ire.models import GoldenRecord, NormalizedIdentity, SourceSystem



def check_safety(
    norm: NormalizedIdentity,
    candidates: List[GoldenRecord],
    scores: List[Tuple[float, GoldenRecord]],
    source_system: SourceSystem,
    config: Config,
) -> List[str]:
    flags: List[str] = []

    if any(has_tier1_conflict(norm, candidate) for candidate in candidates):
        flags.append('tier1_conflict')

    high_count = sum(1 for score, _ in scores if score >= config.IRE_AUTO_MERGE_THRESHOLD)
    if high_count >= 2:
        flags.append('multiple_high_candidates')

    if len(scores) >= 2 and (scores[0][0] - scores[1][0]) < config.IRE_MULTI_MATCH_GAP_THRESHOLD:
        flags.append('low_score_gap')

    if (not source_system.is_internal) or source_system.trust_level.lower() != 'trusted':
        flags.append('untrusted_source')

    return flags
