from __future__ import annotations

"""Oracle repository contract for the IRE MVP package."""

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
from ire.repository import IRERepository


class OracleRepository(IRERepository):
    def __init__(self, user: str, password: str, dsn: str):
        self._user = user
        self._password = password
        self._dsn = dsn
        self._connection = None

    def _get_connection(self):
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError('OracleRepository requires the optional oracledb package to be installed.') from exc
        if self._connection is None:
            self._connection = oracledb.connect(self._user, self._password, self._dsn)
        return self._connection

    def load_source_systems(self) -> List[SourceSystem]:
        """Load source systems.

        SQL:
            SELECT system_id, name, trust_level, is_internal
            FROM source_systems
        """
        raise NotImplementedError('OracleRepository.load_source_systems is documented but not executable in this environment.')

    def ingest_source_record(self, record: SourceRecord) -> SourceRecord:
        """Insert a source record.

        SQL:
            INSERT INTO source_records (
                source_name, source_pk, raw_payload, normalized_name, normalized_email,
                normalized_phone, hkid, emplid, studentid, alumniid, address
            ) VALUES (
                :source_name, :source_pk, :raw_payload, :normalized_name, :normalized_email,
                :normalized_phone, :hkid, :emplid, :studentid, :alumniid, :address
            )
        """
        raise NotImplementedError('OracleRepository.ingest_source_record is documented but not executable in this environment.')

    def save_normalized_identity(self, norm: NormalizedIdentity) -> NormalizedIdentity:
        """Persist normalized values.

        SQL:
            UPDATE source_records
            SET normalized_name = :normalized_name,
                normalized_email = :normalized_email,
                normalized_phone = :normalized_phone,
                hkid = :hkid,
                emplid = :emplid,
                studentid = :studentid,
                alumniid = :alumniid,
                address = :address
            WHERE source_record_id = :source_record_id
        """
        raise NotImplementedError('OracleRepository.save_normalized_identity is documented but not executable in this environment.')

    def load_golden_records(self) -> List[GoldenRecord]:
        """Load all golden records.

        SQL:
            SELECT golden_id, canonical_name, canonical_email, canonical_phone,
                   canonical_hkid, canonical_emplid, canonical_studentid,
                   canonical_alumniid, canonical_address, provenance,
                   last_updated, status
            FROM golden_records
        """
        raise NotImplementedError('OracleRepository.load_golden_records is documented but not executable in this environment.')

    def get_golden_record(self, golden_id: str) -> Optional[GoldenRecord]:
        """Load a single golden record.

        SQL:
            SELECT golden_id, canonical_name, canonical_email, canonical_phone,
                   canonical_hkid, canonical_emplid, canonical_studentid,
                   canonical_alumniid, canonical_address, provenance,
                   last_updated, status
            FROM golden_records
            WHERE golden_id = :golden_id
        """
        raise NotImplementedError('OracleRepository.get_golden_record is documented but not executable in this environment.')

    def create_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        """Insert a golden record.

        SQL:
            INSERT INTO golden_records (
                canonical_name, canonical_email, canonical_phone, canonical_hkid,
                canonical_emplid, canonical_studentid, canonical_alumniid,
                canonical_address, provenance, status
            ) VALUES (
                :canonical_name, :canonical_email, :canonical_phone, :canonical_hkid,
                :canonical_emplid, :canonical_studentid, :canonical_alumniid,
                :canonical_address, :provenance, :status
            )
        """
        raise NotImplementedError('OracleRepository.create_golden_record is documented but not executable in this environment.')

    def update_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        """Update a golden record.

        SQL:
            UPDATE golden_records
            SET canonical_name = :canonical_name,
                canonical_email = :canonical_email,
                canonical_phone = :canonical_phone,
                canonical_hkid = :canonical_hkid,
                canonical_emplid = :canonical_emplid,
                canonical_studentid = :canonical_studentid,
                canonical_alumniid = :canonical_alumniid,
                canonical_address = :canonical_address,
                provenance = :provenance,
                last_updated = SYSTIMESTAMP,
                status = :status
            WHERE golden_id = :golden_id
        """
        raise NotImplementedError('OracleRepository.update_golden_record is documented but not executable in this environment.')

    def create_record_link(self, link: RecordLink) -> RecordLink:
        """Insert a record link.

        SQL:
            INSERT INTO record_links (
                source_record_id, golden_id, link_confidence, link_method, evidence
            ) VALUES (
                :source_record_id, :golden_id, :link_confidence, :link_method, :evidence
            )
        """
        raise NotImplementedError('OracleRepository.create_record_link is documented but not executable in this environment.')

    def save_match_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        """Persist a match candidate.

        SQL:
            -- Intended target: a future match_candidates table aligned to the MVP model.
            INSERT INTO match_candidates (
                candidate_id, source_record_id, golden_id, overall_score,
                deterministic_result, safety_flags, decision, created_ts
            ) VALUES (
                :candidate_id, :source_record_id, :golden_id, :overall_score,
                :deterministic_result, :safety_flags, :decision, :created_ts
            )
        """
        raise NotImplementedError('OracleRepository.save_match_candidate is documented but not executable in this environment.')

    def save_match_candidate_features(self, features: List[MatchCandidateFeature]) -> None:
        """Persist candidate feature evidence.

        SQL:
            -- Intended target: a future match_candidate_features table aligned to the MVP model.
            INSERT INTO match_candidate_features (
                feature_id, candidate_id, feature_name, feature_type, source_value,
                golden_value, normalized_source_value, normalized_golden_value,
                similarity_algorithm, similarity_score, priority, weight,
                weighted_score, is_match, is_conflict, is_blocking_feature, evidence_json
            ) VALUES (
                :feature_id, :candidate_id, :feature_name, :feature_type, :source_value,
                :golden_value, :normalized_source_value, :normalized_golden_value,
                :similarity_algorithm, :similarity_score, :priority, :weight,
                :weighted_score, :is_match, :is_conflict, :is_blocking_feature, :evidence_json
            )
        """
        raise NotImplementedError('OracleRepository.save_match_candidate_features is documented but not executable in this environment.')

    def create_manual_review_task(self, task: ManualReviewTask) -> ManualReviewTask:
        """Insert a manual review task.

        SQL:
            INSERT INTO manual_review_queue (
                source_record_id, candidate_goldens, best_confidence, status,
                assigned_to, reviewer_decision, notes
            ) VALUES (
                :source_record_id, :candidate_goldens, :best_confidence, :status,
                :assigned_to, :reviewer_decision, :notes
            )
        """
        raise NotImplementedError('OracleRepository.create_manual_review_task is documented but not executable in this environment.')

    def list_manual_review_tasks(self, status: Optional[str] = None) -> List[ManualReviewTask]:
        """List manual review tasks.

        SQL:
            SELECT task_id, source_record_id, candidate_goldens, best_confidence,
                   status, assigned_to, created_ts, resolved_ts, notes
            FROM manual_review_queue
            WHERE (:status IS NULL OR status = :status)
        """
        raise NotImplementedError('OracleRepository.list_manual_review_tasks is documented but not executable in this environment.')

    def resolve_manual_review_task(self, decision: ManualReviewDecision) -> ManualReviewTask:
        """Resolve a manual review task.

        SQL:
            UPDATE manual_review_queue
            SET status = 'resolved',
                assigned_to = :reviewer,
                reviewer_decision = :decision,
                notes = :notes,
                resolved_ts = SYSTIMESTAMP
            WHERE task_id = :task_id
        """
        raise NotImplementedError('OracleRepository.resolve_manual_review_task is documented but not executable in this environment.')

    def write_merge_history_event(self, event: MergeHistoryEvent) -> MergeHistoryEvent:
        """Insert a merge history event.

        SQL:
            INSERT INTO merge_history (event_type, actor, details)
            VALUES (:event_type, :actor, :details)
        """
        raise NotImplementedError('OracleRepository.write_merge_history_event is documented but not executable in this environment.')

    def get_source_record(self, source_record_id: str) -> Optional[SourceRecord]:
        """Load a source record.

        SQL:
            SELECT source_record_id, source_name, source_pk, raw_payload,
                   normalized_name, normalized_email, normalized_phone,
                   hkid, emplid, studentid, alumniid, address, ingest_ts
            FROM source_records
            WHERE source_record_id = :source_record_id
        """
        raise NotImplementedError('OracleRepository.get_source_record is documented but not executable in this environment.')
