from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

from .evidence import evidence_json
from .models import IdentityRecord, MatchDecision
from .normalizer import normalize_record
from .repository import Repository


class DemoRepository(Repository):
    def __init__(self, initial_goldens: Optional[List[IdentityRecord]] = None) -> None:
        self._source_records: Dict[int, IdentityRecord] = {}
        self._goldens: Dict[str, IdentityRecord] = {
            record.source_pk: normalize_record(record) for record in (initial_goldens or [])
        }
        self._links: List[Dict] = []
        self._match_results: List[Dict] = []
        self._review_tasks: Dict[int, Dict] = {}
        self._review_decisions: List[Dict] = []
        self._source_seq = 1
        numeric_ids = [int(golden_id) for golden_id in self._goldens if str(golden_id).isdigit()]
        self._golden_seq = max(numeric_ids) if numeric_ids else 1000
        self._task_seq = 1

    def add_source_record(self, record: IdentityRecord) -> int:
        source_id = self._source_seq
        self._source_seq += 1
        self._source_records[source_id] = record
        return source_id

    def list_golden_records(self) -> List[IdentityRecord]:
        return list(self._goldens.values())

    def get_golden_record(self, golden_id: str) -> Optional[IdentityRecord]:
        return self._goldens.get(golden_id)

    def save_match_result(self, source_record_id: int, decision: MatchDecision) -> None:
        self._match_results.append(
            {
                "source_record_id": source_record_id,
                "decision": decision.decision,
                "confidence": decision.confidence,
                "best_golden_id": decision.best_golden_id,
                "reason": decision.reason,
                "evidence_json": evidence_json(decision.candidates),
            }
        )

    def create_or_update_link(self, source_record_id: int, golden_id: str, confidence: float, method: str, reason: str) -> None:
        self._links.append(
            {
                "source_record_id": source_record_id,
                "golden_id": golden_id,
                "confidence": confidence,
                "method": method,
                "reason": reason,
            }
        )

    def create_golden_record(self, from_record: IdentityRecord) -> str:
        self._golden_seq += 1
        golden_id = str(self._golden_seq)
        payload = asdict(from_record)
        payload["source_pk"] = golden_id
        self._goldens[golden_id] = IdentityRecord(**payload)
        return golden_id

    def upsert_golden_merge(self, golden_id: str, incoming: IdentityRecord) -> None:
        golden = self._goldens[golden_id]
        merged = asdict(golden)
        incoming_payload = asdict(incoming)
        for field in ("name", "email", "phone", "address", "hkid", "emplid", "student_id", "alumni_id"):
            if not merged.get(field) and incoming_payload.get(field):
                merged[field] = incoming_payload[field]
            elif field in {"name", "address"} and len(incoming_payload.get(field, "")) > len(merged.get(field, "")):
                merged[field] = incoming_payload[field]
        self._goldens[golden_id] = IdentityRecord(**merged)

    def create_review_task(self, source_record_id: int, decision: MatchDecision) -> int:
        task_id = self._task_seq
        self._task_seq += 1
        self._review_tasks[task_id] = {
            "task_id": task_id,
            "source_record_id": source_record_id,
            "status": "open",
            "reason": decision.reason,
            "recommended_action": "manual-review",
            "candidate_count": decision.candidate_count,
            "best_golden_id": decision.best_golden_id,
            "confidence": decision.confidence,
            "evidence_json": evidence_json(decision.candidates),
        }
        return task_id

    def list_review_tasks(self) -> List[Dict]:
        return list(self._review_tasks.values())

    def add_review_decision(self, task_id: int, decision: str, reviewer: str, selected_golden_id: Optional[str], rationale: str) -> Dict:
        task = self._review_tasks.get(task_id)
        if not task:
            raise KeyError(f"review task {task_id} not found")
        task["status"] = "resolved"
        payload = {
            "task_id": task_id,
            "decision": decision,
            "reviewer": reviewer,
            "selected_golden_id": selected_golden_id,
            "rationale": rationale,
        }
        self._review_decisions.append(payload)
        return payload
