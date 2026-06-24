from __future__ import annotations

"""Decision policy for the IRE MVP package."""

from typing import Dict, List, Tuple

from ire.config import Config
from ire.models import GoldenRecord, MatchDecision, NormalizedIdentity, SourceSystem


_BLOCKING_FLAGS = {'multiple_high_candidates', 'low_score_gap', 'tier1_conflict'}



def make_decision(
    norm: NormalizedIdentity,
    scored_candidates: List[Tuple[float, GoldenRecord]],
    deterministic_results: Dict[str, str],
    safety_flags: List[str],
    source_system: SourceSystem,
    config: Config,
) -> MatchDecision:
    del norm, source_system

    top_score = scored_candidates[0][0] if scored_candidates else 0.0
    top_golden_id = scored_candidates[0][1].golden_id if scored_candidates else None
    candidate_count = len(scored_candidates)

    if any(result == 'conflict' for result in deterministic_results.values()):
        return MatchDecision(
            decision='manual-review',
            confidence=top_score,
            best_golden_id=top_golden_id,
            reason='tier1_conflict',
            candidate_count=candidate_count,
            safety_flags=list(safety_flags),
        )

    if any(result == 'match' for result in deterministic_results.values()) and 'tier1_conflict' not in safety_flags:
        return MatchDecision(
            decision='auto-merge',
            confidence=max(top_score, 1.0),
            best_golden_id=top_golden_id,
            reason='deterministic_match',
            candidate_count=candidate_count,
            safety_flags=list(safety_flags),
        )

    if not scored_candidates or top_score < config.IRE_MANUAL_REVIEW_THRESHOLD:
        return MatchDecision(
            decision='new-golden-record',
            confidence=top_score,
            best_golden_id=top_golden_id,
            reason='low_confidence' if scored_candidates else 'no_candidates',
            candidate_count=candidate_count,
            safety_flags=list(safety_flags),
        )

    for flag in ('multiple_high_candidates', 'low_score_gap', 'tier1_conflict'):
        if flag in safety_flags:
            return MatchDecision(
                decision='manual-review',
                confidence=top_score,
                best_golden_id=top_golden_id,
                reason=flag,
                candidate_count=candidate_count,
                safety_flags=list(safety_flags),
            )

    if top_score >= config.IRE_AUTO_MERGE_THRESHOLD and not safety_flags:
        return MatchDecision(
            decision='auto-merge',
            confidence=top_score,
            best_golden_id=top_golden_id,
            reason='high_confidence',
            candidate_count=candidate_count,
            safety_flags=list(safety_flags),
        )

    if top_score >= config.IRE_MANUAL_REVIEW_THRESHOLD:
        reason = 'untrusted_source' if 'untrusted_source' in safety_flags else 'needs_review'
        return MatchDecision(
            decision='manual-review',
            confidence=top_score,
            best_golden_id=top_golden_id,
            reason=reason,
            candidate_count=candidate_count,
            safety_flags=list(safety_flags),
        )

    return MatchDecision(
        decision='new-golden-record',
        confidence=top_score,
        best_golden_id=top_golden_id,
        reason='low_confidence',
        candidate_count=candidate_count,
        safety_flags=list(safety_flags),
    )
