from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, List

from .models import MatchCandidate, MatchCandidateFeature


def feature_to_dict(feature: MatchCandidateFeature) -> Dict[str, Any]:
    return asdict(feature)


def candidate_to_dict(candidate: MatchCandidate) -> Dict[str, Any]:
    payload = asdict(candidate)
    payload["features"] = [feature_to_dict(feature) for feature in candidate.features]
    return payload


def evidence_json(candidates: List[MatchCandidate]) -> str:
    return json.dumps([candidate_to_dict(candidate) for candidate in candidates], ensure_ascii=False)
