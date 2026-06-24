from __future__ import annotations

"""In-memory demo repository for the IRE MVP package."""

import csv
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

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
    utc_now,
)
from ire.repository import IRERepository


_DEFAULT_SOURCE_SYSTEMS = [
    SourceSystem('SYS-001', 'HR', 'trusted', True),
    SourceSystem('SYS-002', 'SIS', 'trusted', True),
    SourceSystem('SYS-003', 'Alumni', 'trusted', True),
    SourceSystem('SYS-004', 'CRM', 'standard', False),
    SourceSystem('SYS-005', 'ThirdParty', 'untrusted', False),
]



def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


class DemoRepository(IRERepository):
    def __init__(self, golden_csv: Optional[Path] = None, source_systems_csv: Optional[Path] = None):
        self._source_systems: Dict[str, SourceSystem] = {}
        self._source_records: Dict[str, SourceRecord] = {}
        self._normalized_identities: Dict[str, NormalizedIdentity] = {}
        self._golden_records: Dict[str, GoldenRecord] = {}
        self._record_links: Dict[str, RecordLink] = {}
        self._match_candidates: Dict[str, MatchCandidate] = {}
        self._match_candidate_features: Dict[str, MatchCandidateFeature] = {}
        self._manual_review_tasks: Dict[str, ManualReviewTask] = {}
        self._merge_history_events: Dict[str, MergeHistoryEvent] = {}

        if source_systems_csv:
            self._load_source_systems_csv(Path(source_systems_csv))
        else:
            for system in _DEFAULT_SOURCE_SYSTEMS:
                self._source_systems[system.system_id] = system

        if golden_csv:
            self._load_golden_records_csv(Path(golden_csv))

    def _load_source_systems_csv(self, path: Path) -> None:
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                system = SourceSystem(
                    system_id=(row.get('system_id') or str(uuid4())).strip(),
                    name=(row.get('name') or '').strip(),
                    trust_level=(row.get('trust_level') or '').strip(),
                    is_internal=_to_bool(row.get('is_internal', 'false')),
                )
                self._source_systems[system.system_id] = system

    def _load_golden_records_csv(self, path: Path) -> None:
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                golden = GoldenRecord(
                    golden_id=(row.get('golden_id') or str(uuid4())).strip(),
                    canonical_name=(row.get('canonical_name') or '').strip() or None,
                    canonical_email=(row.get('canonical_email') or '').strip() or None,
                    canonical_phone=(row.get('canonical_phone') or '').strip() or None,
                    canonical_hkid=(row.get('canonical_hkid') or '').strip() or None,
                    canonical_emplid=(row.get('canonical_emplid') or '').strip() or None,
                    canonical_studentid=(row.get('canonical_studentid') or '').strip() or None,
                    canonical_alumniid=(row.get('canonical_alumniid') or '').strip() or None,
                    canonical_address=(row.get('canonical_address') or '').strip() or None,
                    person_type=(row.get('person_type') or 'person').strip(),
                    status=(row.get('status') or 'active').strip(),
                )
                self._golden_records[golden.golden_id] = golden

    def load_source_systems(self) -> List[SourceSystem]:
        return list(self._source_systems.values())

    def ingest_source_record(self, record: SourceRecord) -> SourceRecord:
        if not record.source_record_id:
            record.source_record_id = str(uuid4())
        if not record.ingest_ts:
            record.ingest_ts = utc_now()
        self._source_records[record.source_record_id] = record
        return record

    def save_normalized_identity(self, norm: NormalizedIdentity) -> NormalizedIdentity:
        self._normalized_identities[norm.source_record_id] = norm
        return norm

    def load_golden_records(self) -> List[GoldenRecord]:
        return list(self._golden_records.values())

    def get_golden_record(self, golden_id: str) -> Optional[GoldenRecord]:
        return self._golden_records.get(golden_id)

    def create_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        if not golden.golden_id:
            golden.golden_id = str(uuid4())
        self._golden_records[golden.golden_id] = golden
        return golden

    def update_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        self._golden_records[golden.golden_id] = golden
        return golden

    def create_record_link(self, link: RecordLink) -> RecordLink:
        if not link.link_id:
            link.link_id = str(uuid4())
        self._record_links[link.link_id] = link
        return link

    def save_match_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        if not candidate.candidate_id:
            candidate.candidate_id = str(uuid4())
        self._match_candidates[candidate.candidate_id] = candidate
        return candidate

    def save_match_candidate_features(self, features: List[MatchCandidateFeature]) -> None:
        for feature in features:
            if not feature.feature_id:
                feature.feature_id = str(uuid4())
            self._match_candidate_features[feature.feature_id] = feature

    def create_manual_review_task(self, task: ManualReviewTask) -> ManualReviewTask:
        if not task.task_id:
            task.task_id = str(uuid4())
        self._manual_review_tasks[task.task_id] = task
        return task

    def list_manual_review_tasks(self, status: Optional[str] = None) -> List[ManualReviewTask]:
        tasks = list(self._manual_review_tasks.values())
        if status is None:
            return tasks
        return [task for task in tasks if task.status == status]

    def resolve_manual_review_task(self, decision: ManualReviewDecision) -> ManualReviewTask:
        task = self._manual_review_tasks.get(decision.task_id)
        if task is None:
            raise KeyError(f'Manual review task not found: {decision.task_id}')
        task.status = 'resolved'
        task.assigned_to = decision.reviewer
        task.resolved_ts = decision.decided_ts
        task.reason = decision.notes or task.reason
        self._manual_review_tasks[task.task_id] = task
        return task

    def write_merge_history_event(self, event: MergeHistoryEvent) -> MergeHistoryEvent:
        if not event.event_id:
            event.event_id = str(uuid4())
        self._merge_history_events[event.event_id] = event
        return event

    def get_source_record(self, source_record_id: str) -> Optional[SourceRecord]:
        return self._source_records.get(source_record_id)
