from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .models import IdentityRecord, MatchDecision


class Repository(ABC):
    @abstractmethod
    def add_source_record(self, record: IdentityRecord) -> int:
        raise NotImplementedError

    @abstractmethod
    def list_golden_records(self) -> List[IdentityRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_golden_record(self, golden_id: str) -> Optional[IdentityRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_match_result(self, source_record_id: int, decision: MatchDecision) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_or_update_link(self, source_record_id: int, golden_id: str, confidence: float, method: str, reason: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_golden_record(self, from_record: IdentityRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    def upsert_golden_merge(self, golden_id: str, incoming: IdentityRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_review_task(self, source_record_id: int, decision: MatchDecision) -> int:
        raise NotImplementedError

    @abstractmethod
    def list_review_tasks(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def add_review_decision(self, task_id: int, decision: str, reviewer: str, selected_golden_id: Optional[str], rationale: str) -> Dict:
        raise NotImplementedError
