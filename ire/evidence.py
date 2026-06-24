from __future__ import annotations

"""Evidence serialization utilities."""

from dataclasses import asdict
import json
from typing import List

from ire.models import MatchCandidateFeature


def build_evidence_json(features: List[MatchCandidateFeature]) -> str:
    return json.dumps([asdict(feature) for feature in features], default=str, sort_keys=True)



def parse_evidence_json(evidence_json: str) -> List[dict]:
    if not evidence_json:
        return []
    return json.loads(evidence_json)
