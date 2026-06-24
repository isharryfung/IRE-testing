from __future__ import annotations

import os
from dataclasses import asdict
from typing import Dict, List, Optional

from .decision import decide
from .matcher import rank_candidates
from .models import IdentityRecord
from .normalizer import normalize_record
from .repository import Repository


class IREService:
    def __init__(self, repository: Repository, auto_merge_threshold: Optional[float] = None, manual_review_threshold: Optional[float] = None) -> None:
        self.repository = repository
        self.auto_merge_threshold = auto_merge_threshold if auto_merge_threshold is not None else float(os.getenv("IRE_AUTO_MERGE_THRESHOLD", "0.85"))
        self.manual_review_threshold = manual_review_threshold if manual_review_threshold is not None else float(os.getenv("IRE_MANUAL_REVIEW_THRESHOLD", "0.50"))

    def ingest(self, record: IdentityRecord) -> Dict:
        normalized = normalize_record(record)
        source_record_id = self.repository.add_source_record(normalized)
        return {"source_record_id": source_record_id, "normalized_record": asdict(normalized)}

    def match(self, record: IdentityRecord) -> Dict:
        normalized = normalize_record(record)
        source_record_id = self.repository.add_source_record(normalized)

        goldens = self.repository.list_golden_records()
        candidates = rank_candidates(normalized, goldens)
        decision = decide(candidates, self.auto_merge_threshold, self.manual_review_threshold)
        self.repository.save_match_result(source_record_id, decision)

        task_id: Optional[int] = None
        if decision.decision == "auto-merge" and decision.best_golden_id:
            method = "deterministic" if decision.confidence == 1.0 else "probabilistic"
            self.repository.create_or_update_link(source_record_id, decision.best_golden_id, decision.confidence, method, decision.reason)
            self.repository.upsert_golden_merge(decision.best_golden_id, normalized)
        elif decision.decision == "manual-review":
            task_id = self.repository.create_review_task(source_record_id, decision)
        else:
            golden_id = self.repository.create_golden_record(normalized)
            self.repository.create_or_update_link(source_record_id, golden_id, decision.confidence, "probabilistic", decision.reason)
            decision.best_golden_id = golden_id

        return {
            "source_record_id": source_record_id,
            "source_pk": normalized.source_pk,
            "source_system": normalized.source_system,
            "decision": decision.decision,
            "best_golden_id": decision.best_golden_id,
            "confidence": round(decision.confidence, 6),
            "reason": decision.reason,
            "candidate_count": decision.candidate_count,
            "review_task_id": task_id,
            "evidence": [asdict(candidate) for candidate in decision.candidates],
        }

    def get_golden(self, golden_id: str) -> Optional[Dict]:
        record = self.repository.get_golden_record(golden_id)
        return asdict(record) if record else None

    def list_review_tasks(self) -> List[Dict]:
        return self.repository.list_review_tasks()

    def submit_review_decision(self, task_id: int, decision: str, reviewer: str, selected_golden_id: Optional[str], rationale: str) -> Dict:
        return self.repository.add_review_decision(task_id, decision, reviewer, selected_golden_id, rationale)
