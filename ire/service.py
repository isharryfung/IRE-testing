from __future__ import annotations

"""Service orchestration for the IRE MVP package."""

from dataclasses import replace
from typing import Dict, Optional
from uuid import uuid4

from ire.candidate_generation import generate_candidates
from ire.config import Config
from ire.decision import make_decision
from ire.deterministic import deterministic_check
from ire.evidence import build_evidence_json
from ire.models import (
    GoldenRecord,
    ManualReviewDecision,
    ManualReviewTask,
    MatchCandidate,
    MatchDecision,
    MergeHistoryEvent,
    RecordLink,
    SourceRecord,
    utc_now,
)
from ire.normalizer import normalize_hkid, normalize_id, normalize_record
from ire.repository import IRERepository
from ire.safety import check_safety
from ire.scoring import score_candidate
from ire.survivorship import apply_survivorship, build_provenance


class IREService:
    def __init__(self, repository: IRERepository, config: Config):
        self.repo = repository
        self.config = config

    def _find_source_system(self, source_system_name: str):
        for source_system in self.repo.load_source_systems():
            if source_system.name.lower() == source_system_name.lower():
                return source_system
        raise ValueError(f'Unknown source system: {source_system_name}')

    def _build_source_record(self, source_system_name: str, source_pk: str, raw_data: dict) -> SourceRecord:
        source_system = self._find_source_system(source_system_name)
        return SourceRecord(
            source_record_id=str(uuid4()),
            system_id=source_system.system_id,
            source_pk=source_pk,
            raw_name=raw_data.get('name'),
            raw_email=raw_data.get('email'),
            raw_phone=raw_data.get('phone'),
            raw_address=raw_data.get('address'),
            raw_hkid=raw_data.get('hkid'),
            raw_emplid=raw_data.get('emplid'),
            raw_studentid=raw_data.get('studentid'),
            raw_alumniid=raw_data.get('alumniid'),
            raw_payload=dict(raw_data),
        )

    def _new_golden_from_source(self, source_record: SourceRecord):
        return GoldenRecord(
            golden_id=str(uuid4()),
            canonical_name=(source_record.raw_name or '').strip() or None,
            canonical_email=(source_record.raw_email or '').strip().lower() or None,
            canonical_phone=''.join(ch for ch in (source_record.raw_phone or '') if ch.isdigit()) or None,
            canonical_hkid=normalize_hkid(source_record.raw_hkid) or None,
            canonical_emplid=normalize_id(source_record.raw_emplid) or None,
            canonical_studentid=normalize_id(source_record.raw_studentid) or None,
            canonical_alumniid=normalize_id(source_record.raw_alumniid) or None,
            canonical_address=' '.join((source_record.raw_address or '').strip().split()) or None,
            person_type='person',
            status='active',
        )

    def process_record(
        self,
        source_system_name: str,
        source_pk: str,
        raw_data: dict,
    ) -> MatchDecision:
        source_system = self._find_source_system(source_system_name)
        source_record = self._build_source_record(source_system_name, source_pk, raw_data)
        source_record = self.repo.ingest_source_record(source_record)

        norm = normalize_record(source_record)
        self.repo.save_normalized_identity(norm)

        golden_records = self.repo.load_golden_records()
        candidates = generate_candidates(norm, golden_records)

        deterministic_results: Dict[str, str] = {}
        scored = []
        feature_map = {}
        for candidate in candidates:
            deterministic_result = deterministic_check(norm, candidate, source_system)
            if deterministic_result:
                deterministic_results[candidate.golden_id] = deterministic_result
            score, features = score_candidate(norm, candidate)
            scored.append((score, candidate))
            feature_map[candidate.golden_id] = features

        scored.sort(key=lambda item: item[0], reverse=True)
        safety_flags = check_safety(norm, candidates, scored, source_system, self.config)
        decision = make_decision(norm, scored, deterministic_results, safety_flags, source_system, self.config)

        best_golden = scored[0][1] if scored else None
        best_features = feature_map.get(best_golden.golden_id if best_golden else '', [])
        decision.features = best_features

        match_candidate = MatchCandidate(
            candidate_id=str(uuid4()),
            source_record_id=source_record.source_record_id,
            golden_id=decision.best_golden_id,
            overall_score=decision.confidence,
            deterministic_result=deterministic_results.get(decision.best_golden_id or ''),
            safety_flags=list(safety_flags),
            decision=decision.decision,
        )
        self.repo.save_match_candidate(match_candidate)
        for feature in best_features:
            feature.candidate_id = match_candidate.candidate_id
        self.repo.save_match_candidate_features(best_features)

        evidence_json = build_evidence_json(best_features)

        if decision.decision == 'auto-merge' and best_golden is not None:
            updated = apply_survivorship(best_golden, norm, source_record, source_system)
            self.repo.update_golden_record(updated)
            self.repo.create_record_link(
                RecordLink(
                    link_id=str(uuid4()),
                    source_record_id=source_record.source_record_id,
                    golden_id=updated.golden_id,
                    confidence=decision.confidence,
                    method=deterministic_results.get(updated.golden_id, 'probabilistic'),
                    evidence_json=evidence_json,
                )
            )
            self.repo.write_merge_history_event(
                MergeHistoryEvent(
                    event_id=str(uuid4()),
                    event_type='merge',
                    actor='system',
                    source_record_id=source_record.source_record_id,
                    golden_id=updated.golden_id,
                    details={'decision': decision.decision, 'reason': decision.reason},
                )
            )
        elif decision.decision == 'manual-review':
            self.repo.create_manual_review_task(
                ManualReviewTask(
                    task_id=str(uuid4()),
                    source_record_id=source_record.source_record_id,
                    candidate_golden_ids=[candidate.golden_id for _, candidate in scored],
                    best_confidence=decision.confidence,
                    status='open',
                    reason=decision.reason,
                )
            )
        else:
            new_golden = self._new_golden_from_source(source_record)
            new_golden = replace(new_golden, provenance=build_provenance(new_golden, source_record, source_system))
            new_golden = self.repo.create_golden_record(new_golden)
            decision.best_golden_id = new_golden.golden_id
            self.repo.create_record_link(
                RecordLink(
                    link_id=str(uuid4()),
                    source_record_id=source_record.source_record_id,
                    golden_id=new_golden.golden_id,
                    confidence=decision.confidence,
                    method='new-golden-record',
                    evidence_json=evidence_json,
                )
            )
            self.repo.write_merge_history_event(
                MergeHistoryEvent(
                    event_id=str(uuid4()),
                    event_type='create',
                    actor='system',
                    source_record_id=source_record.source_record_id,
                    golden_id=new_golden.golden_id,
                    details={'decision': decision.decision, 'reason': decision.reason},
                )
            )

        self.repo.write_merge_history_event(
            MergeHistoryEvent(
                event_id=str(uuid4()),
                event_type='decision',
                actor='system',
                source_record_id=source_record.source_record_id,
                golden_id=decision.best_golden_id,
                details={
                    'decision': decision.decision,
                    'confidence': decision.confidence,
                    'candidate_count': decision.candidate_count,
                    'safety_flags': decision.safety_flags,
                    'timestamp': utc_now().isoformat(),
                },
            )
        )
        return decision

    def resolve_review_task(
        self,
        task_id: str,
        reviewer: str,
        decision: str,
        golden_id: Optional[str],
        notes: str,
    ) -> ManualReviewTask:
        review_decision = ManualReviewDecision(
            task_id=task_id,
            reviewer=reviewer,
            decision=decision,
            golden_id=golden_id,
            notes=notes,
        )
        task = self.repo.resolve_manual_review_task(review_decision)
        self.repo.write_merge_history_event(
            MergeHistoryEvent(
                event_id=str(uuid4()),
                event_type='manual-review-resolution',
                actor=reviewer,
                source_record_id=task.source_record_id,
                golden_id=golden_id,
                details={'decision': decision, 'notes': notes},
            )
        )
        return task
