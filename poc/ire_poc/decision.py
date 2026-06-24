from __future__ import annotations

from typing import List

from .models import MatchCandidate, MatchDecision


def decide(candidates: List[MatchCandidate], auto_threshold: float, manual_threshold: float) -> MatchDecision:
    if not candidates:
        return MatchDecision(
            decision="new-golden-record",
            reason="no-candidates",
            confidence=0.0,
            best_golden_id=None,
            candidate_count=0,
            candidates=[],
        )

    best = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    multiple_high = len([candidate for candidate in candidates if candidate.confidence >= auto_threshold]) > 1

    if best.blocked_reason:
        return MatchDecision(
            decision="manual-review",
            reason=best.blocked_reason,
            confidence=best.confidence,
            best_golden_id=best.golden_id,
            candidate_count=len(candidates),
            candidates=candidates,
        )

    if multiple_high:
        return MatchDecision(
            decision="manual-review",
            reason="multiple-high-candidates",
            confidence=best.confidence,
            best_golden_id=best.golden_id,
            candidate_count=len(candidates),
            candidates=candidates,
        )

    if second and best.confidence >= manual_threshold and (best.confidence - second.confidence) < 0.10:
        return MatchDecision(
            decision="manual-review",
            reason="low-top2-score-gap",
            confidence=best.confidence,
            best_golden_id=best.golden_id,
            candidate_count=len(candidates),
            candidates=candidates,
        )

    if best.confidence >= auto_threshold:
        return MatchDecision(
            decision="auto-merge",
            reason="score-above-auto-threshold",
            confidence=best.confidence,
            best_golden_id=best.golden_id,
            candidate_count=len(candidates),
            candidates=candidates,
        )

    if best.confidence >= manual_threshold:
        return MatchDecision(
            decision="manual-review",
            reason="score-in-manual-range",
            confidence=best.confidence,
            best_golden_id=best.golden_id,
            candidate_count=len(candidates),
            candidates=candidates,
        )

    return MatchDecision(
        decision="new-golden-record",
        reason="score-below-manual-threshold",
        confidence=best.confidence,
        best_golden_id=None,
        candidate_count=len(candidates),
        candidates=candidates,
    )
