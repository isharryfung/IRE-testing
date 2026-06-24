from __future__ import annotations

"""Repository abstraction for IRE persistence operations."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ire.models import (
    GoldenRecord,
    ManualReviewDecision,
    ManualReviewTask,
    MatchCandidate,
    MatchCandidateFeature,
    MergeHistoryEvent,
    NormalizedIdentity,
    RecordLink,
    SourceRecord,
    SourceSystem,
)


class IRERepository(ABC):
    @abstractmethod
    def load_source_systems(self) -> List[SourceSystem]: ...

    @abstractmethod
    def ingest_source_record(self, record: SourceRecord) -> SourceRecord: ...

    @abstractmethod
    def save_normalized_identity(self, norm: NormalizedIdentity) -> NormalizedIdentity: ...

    @abstractmethod
    def load_golden_records(self) -> List[GoldenRecord]: ...

    @abstractmethod
    def get_golden_record(self, golden_id: str) -> Optional[GoldenRecord]: ...

    @abstractmethod
    def create_golden_record(self, golden: GoldenRecord) -> GoldenRecord: ...

    @abstractmethod
    def update_golden_record(self, golden: GoldenRecord) -> GoldenRecord: ...

    @abstractmethod
    def create_record_link(self, link: RecordLink) -> RecordLink: ...

    @abstractmethod
    def save_match_candidate(self, candidate: MatchCandidate) -> MatchCandidate: ...

    @abstractmethod
    def save_match_candidate_features(self, features: List[MatchCandidateFeature]) -> None: ...

    @abstractmethod
    def create_manual_review_task(self, task: ManualReviewTask) -> ManualReviewTask: ...

    @abstractmethod
    def list_manual_review_tasks(self, status: Optional[str] = None) -> List[ManualReviewTask]: ...

    @abstractmethod
    def resolve_manual_review_task(self, decision: ManualReviewDecision) -> ManualReviewTask: ...

    @abstractmethod
    def write_merge_history_event(self, event: MergeHistoryEvent) -> MergeHistoryEvent: ...

    @abstractmethod
    def get_source_record(self, source_record_id: str) -> Optional[SourceRecord]: ...
