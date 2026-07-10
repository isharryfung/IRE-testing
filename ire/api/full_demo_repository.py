from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from ire.candidate_generation import generate_candidates
from ire.config import Config
from ire.decision import make_decision
from ire.demo_repository import DemoRepository
from ire.deterministic import deterministic_check
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
from ire.normalizer import normalize_record
from ire.safety import check_safety
from ire.scoring import score_candidate
from ire.survivorship import apply_survivorship, build_provenance


_GOLDEN_FIELDS = {
    'name': 'canonical_name',
    'email': 'canonical_email',
    'phone': 'canonical_phone',
    'hkid': 'canonical_hkid',
    'emplid': 'canonical_emplid',
    'studentid': 'canonical_studentid',
    'alumniid': 'canonical_alumniid',
    'address': 'canonical_address',
}


def _now_iso() -> str:
    return utc_now().isoformat()


def _copy_json(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


class FullDemoRepository(DemoRepository):
    def __init__(self, data_dir: Optional[Path] = None, config: Optional[Config] = None):
        super().__init__()
        self._source_systems.clear()
        self._source_records.clear()
        self._normalized_identities.clear()
        self._golden_records.clear()
        self._record_links.clear()
        self._match_candidates.clear()
        self._match_candidate_features.clear()
        self._manual_review_tasks.clear()
        self._merge_history_events.clear()

        self.config = config or Config()
        self.data_dir = Path(data_dir or Path(__file__).resolve().parent.parent / 'sample_data' / 'full_poc')

        self._source_system_details: Dict[str, Dict[str, Any]] = {}
        self._source_record_details: Dict[str, Dict[str, Any]] = {}
        self._normalized_identity_details: Dict[str, Dict[str, Any]] = {}
        self._golden_record_details: Dict[str, Dict[str, Any]] = {}
        self._record_link_details: Dict[str, Dict[str, Any]] = {}
        self._match_candidate_details: Dict[str, Dict[str, Any]] = {}
        self._match_candidate_feature_details: Dict[str, Dict[str, Any]] = {}
        self._manual_review_task_details: Dict[str, Dict[str, Any]] = {}
        self._manual_review_decisions: List[Dict[str, Any]] = []
        self._duplicate_candidates: Dict[str, Dict[str, Any]] = {}
        self._matching_features: Dict[str, Dict[str, Any]] = {}
        self._matching_rules: Dict[str, Dict[str, Any]] = {}
        self._matching_rule_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._threshold_settings: Dict[str, Dict[str, Any]] = {}
        self._rule_simulations: Dict[str, Dict[str, Any]] = {}
        self._rule_simulation_results: Dict[str, List[Dict[str, Any]]] = {}
        self._survivorship_rules: Dict[str, Dict[str, Any]] = {}
        self._survivorship_rule_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._survivorship_previews: List[Dict[str, Any]] = []
        self._audit_events: Dict[str, Dict[str, Any]] = {}
        self._merge_history_details: Dict[str, Dict[str, Any]] = {}
        self._golden_field_values: Dict[str, Dict[str, Any]] = {}
        self._ingestion_batches: Dict[str, Dict[str, Any]] = {}
        self._app_users: Dict[str, Dict[str, Any]] = {}
        self._app_roles: Dict[str, Dict[str, Any]] = {}
        self._app_user_roles: Dict[str, Dict[str, Any]] = {}
        self._rebatch_jobs: Dict[str, Dict[str, Any]] = {}

        self._load_seed_data()

    def _fixture(self, name: str) -> list[dict[str, Any]]:
        path = self.data_dir / name
        with path.open(encoding='utf-8') as handle:
            return json.load(handle)

    def _load_seed_data(self) -> None:
        self._load_source_systems()
        self._load_ingestion_batches()
        self._load_golden_records()
        self._load_source_records()
        self._load_record_links()
        self._load_match_candidates()
        self._load_match_candidate_features()
        self._load_manual_review_tasks()
        self._load_manual_review_decisions()
        self._load_duplicate_candidates()
        self._load_matching_features()
        self._load_matching_rules()
        self._load_survivorship_rules()
        self._load_audit_events()
        self._seed_thresholds()
        self._seed_app_security()
        self._seed_merge_history()
        self._build_initial_golden_field_values()

    def _load_source_systems(self) -> None:
        for row in self._fixture('source_systems.json'):
            detail = {
                'system_id': row['system_id'],
                'name': row['name'],
                'description': row.get('description', ''),
                'trust_level': row.get('trust_level', 'standard'),
                'is_internal': _bool(row.get('is_internal', False)),
                'auto_merge_allowed': _bool(row.get('auto_merge_allowed', True)),
                'is_active': _bool(row.get('is_active', True)),
                'created_at': row.get('created_at', _now_iso()),
            }
            self._source_system_details[detail['system_id']] = detail
            self._source_systems[detail['system_id']] = SourceSystem(
                system_id=detail['system_id'],
                name=detail['name'],
                trust_level=detail['trust_level'],
                is_internal=detail['is_internal'],
            )

    def _load_ingestion_batches(self) -> None:
        for row in self._fixture('ingestion_batches.json'):
            self._ingestion_batches[row['batch_id']] = dict(row)

    def _load_golden_records(self) -> None:
        for row in self._fixture('golden_records.json'):
            golden = GoldenRecord(
                golden_id=row['golden_id'],
                canonical_name=row.get('canonical_name'),
                canonical_email=row.get('canonical_email'),
                canonical_phone=row.get('canonical_phone'),
                canonical_hkid=row.get('canonical_hkid'),
                canonical_emplid=row.get('canonical_emplid'),
                canonical_studentid=row.get('canonical_studentid'),
                canonical_alumniid=row.get('canonical_alumniid'),
                canonical_address=row.get('canonical_address'),
                person_type=row.get('person_type', 'person'),
                status=row.get('status', 'active'),
                provenance=_copy_json(row.get('provenance', {})),
            )
            self._golden_records[golden.golden_id] = golden
            self._golden_record_details[golden.golden_id] = {
                **_copy_json(row),
                'updated_at': row.get('updated_at', row.get('created_at', _now_iso())),
            }

    def _load_source_records(self) -> None:
        for row in self._fixture('source_records.json'):
            record = SourceRecord(
                source_record_id=row['source_record_id'],
                system_id=row['source_system_id'],
                source_pk=row['source_pk'],
                raw_name=row.get('raw_name'),
                raw_email=row.get('raw_email'),
                raw_phone=row.get('raw_phone'),
                raw_address=row.get('raw_address'),
                raw_hkid=row.get('raw_hkid'),
                raw_emplid=row.get('raw_emplid'),
                raw_studentid=row.get('raw_studentid'),
                raw_alumniid=row.get('raw_alumniid'),
                raw_payload=_copy_json(row.get('raw_payload', {})),
            )
            self._source_records[record.source_record_id] = record
            detail = {
                **_copy_json(row),
                'ingestion_status': row.get('ingestion_status', 'processed'),
                'validation_warnings': row.get('validation_warnings', []),
                'ingest_ts': row.get('ingest_ts', _now_iso()),
                'ingest_user': row.get('ingest_user', 'demo-loader'),
            }
            self._source_record_details[record.source_record_id] = detail
            norm = normalize_record(record)
            self._normalized_identities[norm.source_record_id] = norm
            self._normalized_identity_details[norm.source_record_id] = asdict(norm)
            self._normalized_identity_details[norm.source_record_id]['normalized_at'] = detail['ingest_ts']

    def _load_record_links(self) -> None:
        for row in self._fixture('record_links.json'):
            link = RecordLink(
                link_id=row['link_id'],
                source_record_id=row['source_record_id'],
                golden_id=row['golden_id'],
                confidence=float(row.get('confidence', 0.0)),
                method=row.get('link_method', 'unknown'),
                evidence_json=json.dumps(row.get('evidence_json', []), default=str),
            )
            self._record_links[link.link_id] = link
            self._record_link_details[link.link_id] = {
                **_copy_json(row),
                'link_status': row.get('link_status', 'linked'),
                'link_method': row.get('link_method', link.method),
                'created_at': row.get('created_at', _now_iso()),
                'updated_at': row.get('updated_at', row.get('created_at', _now_iso())),
                'created_by': row.get('created_by', 'demo-loader'),
                'is_active': _bool(row.get('is_active', True)),
            }

    def _load_match_candidates(self) -> None:
        for row in self._fixture('match_candidates.json'):
            candidate = MatchCandidate(
                candidate_id=row['candidate_id'],
                source_record_id=row['source_record_id'],
                golden_id=row.get('golden_id'),
                overall_score=float(row.get('total_score', 0.0)),
                deterministic_result=row.get('deterministic_result'),
                safety_flags=list(row.get('safety_flags', [])),
                decision=row.get('decision_hint', ''),
            )
            self._match_candidates[candidate.candidate_id] = candidate
            self._match_candidate_details[candidate.candidate_id] = {
                **_copy_json(row),
                'source_record': self._source_record_details.get(candidate.source_record_id),
                'golden_record': self._golden_record_details.get(candidate.golden_id) if candidate.golden_id else None,
            }

    def _load_match_candidate_features(self) -> None:
        for row in self._fixture('match_candidate_features.json'):
            feature = MatchCandidateFeature(
                feature_id=row['feature_id'],
                candidate_id=row['candidate_id'],
                feature_name=row['feature_name'],
                feature_type=row.get('feature_type', 'profile'),
                source_value=row.get('source_value', ''),
                golden_value=row.get('golden_value', ''),
                normalized_source_value=row.get('normalized_source_value', ''),
                normalized_golden_value=row.get('normalized_golden_value', ''),
                similarity_algorithm=row.get('similarity_algorithm', 'sequence_matcher'),
                similarity_score=float(row.get('similarity_score', 0.0)),
                priority=int(row.get('priority', 0)),
                weight=float(row.get('calculated_weight', row.get('weight', 0.0))),
                weighted_score=float(row.get('weighted_score', 0.0)),
                is_match=_bool(row.get('is_match', False)),
                is_conflict=_bool(row.get('is_conflict', False)),
                is_blocking_feature=_bool(row.get('is_blocking_feature', False)),
                evidence_json=json.dumps(row.get('evidence_json', {}), default=str),
            )
            self._match_candidate_features[feature.feature_id] = feature
            self._match_candidate_feature_details[feature.feature_id] = {
                **_copy_json(row),
                'calculated_weight': float(row.get('calculated_weight', row.get('weight', 0.0))),
            }

    def _load_manual_review_tasks(self) -> None:
        for row in self._fixture('manual_review_tasks.json'):
            task = ManualReviewTask(
                task_id=row['task_id'],
                source_record_id=row['source_record_id'],
                candidate_golden_ids=list(row.get('candidate_golden_ids', [])),
                best_confidence=float(row.get('best_confidence', 0.0)),
                status=row.get('status', 'open'),
                assigned_to=row.get('assigned_to'),
                reason=row.get('reason_code', ''),
            )
            self._manual_review_tasks[task.task_id] = task
            self._manual_review_task_details[task.task_id] = {
                **_copy_json(row),
                'created_at': row.get('created_at', _now_iso()),
                'resolved_at': row.get('resolved_at'),
                'notes': row.get('notes', ''),
                'safety_flags': row.get('safety_flags', []),
            }

    def _load_manual_review_decisions(self) -> None:
        self._manual_review_decisions = [_copy_json(item) for item in self._fixture('manual_review_decisions.json')]

    def _load_duplicate_candidates(self) -> None:
        for row in self._fixture('golden_duplicate_candidates.json'):
            self._duplicate_candidates[row['duplicate_id']] = _copy_json(row)

    def _load_matching_features(self) -> None:
        for row in self._fixture('matching_features.json'):
            self._matching_features[row['feature_id']] = _copy_json(row)

    def _load_matching_rules(self) -> None:
        for row in self._fixture('matching_rules.json'):
            self._matching_rules[row['rule_id']] = _copy_json(row)
            self._matching_rule_versions[row['rule_id']] = [
                {
                    'version_id': f"{row['rule_id']}-V{row.get('version', 1)}",
                    'rule_id': row['rule_id'],
                    'version_number': row.get('version', 1),
                    'rule_snapshot': _copy_json(row),
                    'changed_by': row.get('created_by', 'demo-loader'),
                    'changed_at': row.get('updated_at', row.get('created_at', _now_iso())),
                    'change_reason': 'Initial demo rule load',
                }
            ]

    def _load_survivorship_rules(self) -> None:
        for row in self._fixture('survivorship_rules.json'):
            self._survivorship_rules[row['rule_id']] = _copy_json(row)
            self._survivorship_rule_versions[row['rule_id']] = [
                {
                    'version_id': f"{row['rule_id']}-V{row.get('version', 1)}",
                    'rule_id': row['rule_id'],
                    'version_number': row.get('version', 1),
                    'rule_snapshot': _copy_json(row),
                    'changed_by': 'demo-loader',
                    'changed_at': row.get('updated_at', row.get('created_at', _now_iso())),
                }
            ]

    def _load_audit_events(self) -> None:
        for row in self._fixture('audit_events.json'):
            self._audit_events[row['event_id']] = _copy_json(row)

    def _seed_thresholds(self) -> None:
        seeded = [
            ('TH-001', 'auto_merge', 0.85, 'Auto merge threshold'),
            ('TH-002', 'manual_review', 0.50, 'Manual review threshold'),
            ('TH-003', 'new_golden', 0.50, 'Below this threshold create new golden record'),
            ('TH-004', 'multi_match_gap', 0.10, 'Minimum score gap between top two candidates'),
        ]
        for setting_id, name, value, description in seeded:
            self._threshold_settings[setting_id] = {
                'setting_id': setting_id,
                'setting_name': name,
                'setting_value': value,
                'description': description,
                'updated_at': _now_iso(),
                'updated_by': 'demo-loader',
            }

    def _seed_app_security(self) -> None:
        self._app_users = {
            'USR-001': {'user_id': 'USR-001', 'username': 'viewer.demo', 'display_name': 'Demo Viewer', 'email': 'viewer@example.org', 'is_active': True, 'created_at': _now_iso()},
            'USR-002': {'user_id': 'USR-002', 'username': 'reviewer.demo', 'display_name': 'Demo Reviewer', 'email': 'reviewer@example.org', 'is_active': True, 'created_at': _now_iso()},
            'USR-003': {'user_id': 'USR-003', 'username': 'steward.demo', 'display_name': 'Data Steward', 'email': 'steward@example.org', 'is_active': True, 'created_at': _now_iso()},
        }
        for role_id, role_name, description in [
            ('ROLE-001', 'Viewer', 'Read-only access to operational dashboards.'),
            ('ROLE-002', 'Reviewer', 'Can work manual review tasks and duplicate queues.'),
            ('ROLE-003', 'Data Steward', 'Can override records and merge/split goldens.'),
            ('ROLE-004', 'Rule Admin', 'Can change matching and survivorship rules.'),
            ('ROLE-005', 'System Admin', 'Full administrative access.'),
        ]:
            self._app_roles[role_id] = {
                'role_id': role_id,
                'role_name': role_name,
                'description': description,
                'permissions': ['read'],
            }
        self._app_user_roles = {
            'UR-001': {'user_role_id': 'UR-001', 'user_id': 'USR-001', 'role_id': 'ROLE-001', 'assigned_at': _now_iso(), 'assigned_by': 'system'},
            'UR-002': {'user_role_id': 'UR-002', 'user_id': 'USR-002', 'role_id': 'ROLE-002', 'assigned_at': _now_iso(), 'assigned_by': 'system'},
            'UR-003': {'user_role_id': 'UR-003', 'user_id': 'USR-003', 'role_id': 'ROLE-003', 'assigned_at': _now_iso(), 'assigned_by': 'system'},
        }

    def _seed_merge_history(self) -> None:
        seeded = [
            {'event_id': 'MH-001', 'event_type': 'merge', 'actor': 'system', 'source_record_id': 'SRC-HR-001', 'golden_id': 'GR-001', 'details': {'story': 'John Michael Smith auto-merged from HR exact EmplId'}, 'event_ts': '2024-09-01T09:05:00Z'},
            {'event_id': 'MH-002', 'event_type': 'merge', 'actor': 'system', 'source_record_id': 'SRC-SIS-001', 'golden_id': 'GR-001', 'details': {'story': 'SIS enrichment linked to same golden'}, 'event_ts': '2024-09-01T10:10:00Z'},
            {'event_id': 'MH-003', 'event_type': 'manual-review-resolution', 'actor': 'reviewer.demo', 'source_record_id': 'SRC-TP-003', 'golden_id': 'GR-003', 'details': {'decision': 'accept_merge', 'notes': 'Phone and department evidence confirm the HR person despite conflicting HKID in source.'}, 'event_ts': '2024-09-03T11:00:00Z'},
            {'event_id': 'MH-004', 'event_type': 'create', 'actor': 'system', 'source_record_id': 'SRC-CRM-004', 'golden_id': 'GR-010', 'details': {'story': 'Unique CRM contact created as new golden'}, 'event_ts': '2024-09-04T08:45:00Z'},
            {'event_id': 'MH-005', 'event_type': 'unlink', 'actor': 'data.steward', 'source_record_id': 'SRC-CRM-007', 'golden_id': 'GR-004', 'details': {'reason': 'Legacy marketing record linked to wrong alumni'}, 'event_ts': '2024-09-05T14:20:00Z'},
        ]
        for row in seeded:
            event = MergeHistoryEvent(
                event_id=row['event_id'],
                event_type=row['event_type'],
                actor=row['actor'],
                source_record_id=row.get('source_record_id'),
                golden_id=row.get('golden_id'),
                details=_copy_json(row.get('details', {})),
            )
            self._merge_history_events[event.event_id] = event
            self._merge_history_details[event.event_id] = _copy_json(row)

    def _add_field_values_for_link(self, link: Dict[str, Any]) -> None:
        record = self._source_record_details.get(link['source_record_id'])
        if record is None:
            return
        for field_name, golden_attr in _GOLDEN_FIELDS.items():
            raw_value = record.get(f'raw_{field_name}')
            if raw_value in (None, ''):
                continue
            field_value_id = f"GFV-{len(self._golden_field_values) + 1:03d}"
            self._golden_field_values[field_value_id] = {
                'field_value_id': field_value_id,
                'golden_id': link['golden_id'],
                'field_name': field_name,
                'field_value': raw_value,
                'source_record_id': record['source_record_id'],
                'source_system_id': record['source_system_id'],
                'applied_rule_id': 'SVR-DEFAULT',
                'applied_at': link['created_at'],
                'golden_field': golden_attr,
            }

    def _build_initial_golden_field_values(self) -> None:
        for link in self._record_link_details.values():
            if not link.get('is_active'):
                continue
            self._add_field_values_for_link(link)

    def _source_system_name(self, source_system_id: str) -> str:
        detail = self._source_system_details.get(source_system_id)
        return detail['name'] if detail else source_system_id

    def _append_audit(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor: str,
        action: str,
        old_value: Any = None,
        new_value: Any = None,
        notes: str = '',
    ) -> Dict[str, Any]:
        event_id = f"AE-{len(self._audit_events) + 1:03d}"
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'actor': actor,
            'action': action,
            'old_value': _copy_json(old_value),
            'new_value': _copy_json(new_value),
            'event_ts': _now_iso(),
            'ip_address': '127.0.0.1',
            'notes': notes,
        }
        self._audit_events[event_id] = event
        return event

    def _append_merge_history(
        self,
        *,
        event_type: str,
        actor: str,
        source_record_id: Optional[str],
        golden_id: Optional[str],
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        event_id = f"MH-{len(self._merge_history_details) + 1:03d}"
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'actor': actor,
            'source_record_id': source_record_id,
            'golden_id': golden_id,
            'details': _copy_json(details),
            'event_ts': _now_iso(),
        }
        self._merge_history_details[event_id] = event
        self._merge_history_events[event_id] = MergeHistoryEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            source_record_id=source_record_id,
            golden_id=golden_id,
            details=_copy_json(details),
        )
        return event

    def _get_source_system_by_name(self, source_system_name: str) -> SourceSystem:
        for system in self._source_systems.values():
            if system.name.lower() == source_system_name.lower():
                return system
        raise KeyError(f'Unknown source system: {source_system_name}')

    def _source_system_filters(self, filters: Dict[str, Any], detail: Dict[str, Any]) -> bool:
        name = str(filters.get('name') or '').strip().lower()
        if name and name not in detail['name'].lower():
            return False
        return True

    def _source_matches(self, source: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        def contains(field: str, value: str) -> bool:
            return value in str(source.get(field, '') or '').lower()

        for key in ('source_pk', 'name', 'email', 'phone', 'address', 'hkid', 'emplid', 'studentid', 'alumniid'):
            needle = str(filters.get(key) or '').strip().lower()
            if needle and not contains(f'raw_{key}' if key not in {'source_pk'} else key, needle):
                return False
        source_system = str(filters.get('source_system') or '').strip().lower()
        if source_system and source_system not in self._source_system_name(source['source_system_id']).lower():
            return False
        batch_id = str(filters.get('batch_id') or '').strip()
        if batch_id and source.get('ingestion_batch_id') != batch_id:
            return False
        ingestion_status = str(filters.get('ingestion_status') or '').strip().lower()
        if ingestion_status and str(source.get('ingestion_status', '')).lower() != ingestion_status:
            return False
        return True

    def _golden_matches(self, golden: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for field in ('name', 'email', 'hkid', 'emplid', 'studentid', 'alumniid', 'status', 'person_type'):
            value = str(filters.get(field) or '').strip().lower()
            if not value:
                continue
            lookup_field = f'canonical_{field}' if field in {'name', 'email', 'hkid', 'emplid', 'studentid', 'alumniid'} else field
            if value not in str(golden.get(lookup_field, '') or '').lower():
                return False
        possible_duplicate = filters.get('possible_duplicate')
        if possible_duplicate is not None and _bool(possible_duplicate) != _bool(golden.get('is_possible_duplicate', False)):
            return False
        return True

    def _candidate_features_for(self, candidate_id: str) -> List[Dict[str, Any]]:
        features = [item for item in self._match_candidate_feature_details.values() if item['candidate_id'] == candidate_id]
        return sorted(features, key=lambda item: (-int(item.get('priority', 0)), item['feature_name']))

    def _active_link_for_source(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        for link in self._record_link_details.values():
            if link['source_record_id'] == source_record_id and link.get('is_active'):
                return _copy_json(link)
        return None

    def _build_golden_from_source(self, source: Dict[str, Any], actor: str) -> Dict[str, Any]:
        golden_id = f"GR-{len(self._golden_record_details) + 1:03d}"
        detail = {
            'golden_id': golden_id,
            'canonical_name': source.get('raw_name'),
            'canonical_email': source.get('raw_email'),
            'canonical_phone': source.get('raw_phone'),
            'canonical_hkid': source.get('raw_hkid'),
            'canonical_emplid': source.get('raw_emplid'),
            'canonical_studentid': source.get('raw_studentid'),
            'canonical_alumniid': source.get('raw_alumniid'),
            'canonical_address': source.get('raw_address'),
            'person_type': 'person',
            'status': 'active',
            'is_possible_duplicate': False,
            'confidence_level': 'medium',
            'provenance': {},
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
            'created_by': actor,
        }
        created = self.create_golden_record_full(detail, actor=actor)
        self.link_source_to_golden(source['source_record_id'], created['golden_id'], actor=actor, method='new-golden-record', confidence=0.5)
        return created

    def load_source_systems(self) -> List[SourceSystem]:
        return list(self._source_systems.values())

    def ingest_source_record(self, record: SourceRecord) -> SourceRecord:
        super().ingest_source_record(record)
        detail = {
            'source_record_id': record.source_record_id,
            'source_system_id': record.system_id,
            'ingestion_batch_id': None,
            'source_pk': record.source_pk,
            'raw_name': record.raw_name,
            'raw_email': record.raw_email,
            'raw_phone': record.raw_phone,
            'raw_address': record.raw_address,
            'raw_hkid': record.raw_hkid,
            'raw_emplid': record.raw_emplid,
            'raw_studentid': record.raw_studentid,
            'raw_alumniid': record.raw_alumniid,
            'raw_payload': _copy_json(record.raw_payload),
            'ingestion_status': 'processed',
            'validation_warnings': [],
            'ingest_ts': _now_iso(),
            'ingest_user': 'system',
        }
        self._source_record_details[record.source_record_id] = detail
        self._append_audit(event_type='source_record', entity_type='source_record', entity_id=record.source_record_id, actor='system', action='ingest', new_value=detail)
        return record

    def save_normalized_identity(self, norm: NormalizedIdentity) -> NormalizedIdentity:
        super().save_normalized_identity(norm)
        self._normalized_identity_details[norm.source_record_id] = {**asdict(norm), 'normalized_at': _now_iso()}
        return norm

    def load_golden_records(self) -> List[GoldenRecord]:
        return list(self._golden_records.values())

    def get_golden_record(self, golden_id: str) -> Optional[GoldenRecord]:
        return self._golden_records.get(golden_id)

    def create_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        super().create_golden_record(golden)
        detail = self._golden_record_details.get(golden.golden_id, {})
        detail.update(
            {
                'golden_id': golden.golden_id,
                'canonical_name': golden.canonical_name,
                'canonical_email': golden.canonical_email,
                'canonical_phone': golden.canonical_phone,
                'canonical_hkid': golden.canonical_hkid,
                'canonical_emplid': golden.canonical_emplid,
                'canonical_studentid': golden.canonical_studentid,
                'canonical_alumniid': golden.canonical_alumniid,
                'canonical_address': golden.canonical_address,
                'person_type': golden.person_type,
                'status': golden.status,
                'provenance': _copy_json(golden.provenance),
                'updated_at': _now_iso(),
            }
        )
        detail.setdefault('created_at', _now_iso())
        detail.setdefault('created_by', 'system')
        detail.setdefault('is_possible_duplicate', False)
        detail.setdefault('confidence_level', 'medium')
        self._golden_record_details[golden.golden_id] = detail
        return golden

    def update_golden_record(self, golden: GoldenRecord) -> GoldenRecord:
        super().update_golden_record(golden)
        current = self._golden_record_details.get(golden.golden_id, {})
        current.update(
            {
                'golden_id': golden.golden_id,
                'canonical_name': golden.canonical_name,
                'canonical_email': golden.canonical_email,
                'canonical_phone': golden.canonical_phone,
                'canonical_hkid': golden.canonical_hkid,
                'canonical_emplid': golden.canonical_emplid,
                'canonical_studentid': golden.canonical_studentid,
                'canonical_alumniid': golden.canonical_alumniid,
                'canonical_address': golden.canonical_address,
                'person_type': golden.person_type,
                'status': golden.status,
                'provenance': _copy_json(golden.provenance),
                'updated_at': _now_iso(),
            }
        )
        self._golden_record_details[golden.golden_id] = current
        return golden

    def create_record_link(self, link: RecordLink) -> RecordLink:
        super().create_record_link(link)
        self._record_link_details[link.link_id] = {
            'link_id': link.link_id,
            'source_record_id': link.source_record_id,
            'golden_id': link.golden_id,
            'link_status': 'linked',
            'link_method': link.method,
            'confidence': link.confidence,
            'candidate_id': None,
            'review_task_id': None,
            'evidence_json': json.loads(link.evidence_json or '[]'),
            'unlink_reason': None,
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
            'created_by': 'system',
            'is_active': True,
        }
        return link

    def save_match_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        super().save_match_candidate(candidate)
        self._match_candidate_details[candidate.candidate_id] = {
            'candidate_id': candidate.candidate_id,
            'source_record_id': candidate.source_record_id,
            'golden_id': candidate.golden_id,
            'total_score': candidate.overall_score,
            'decision_hint': candidate.decision,
            'rank_order': 1,
            'has_tier1_conflict': 'tier1_conflict' in candidate.safety_flags,
            'has_multi_match': 'multiple_high_candidates' in candidate.safety_flags,
            'has_low_gap': 'low_score_gap' in candidate.safety_flags,
            'source_trust': self._source_system_name(self._source_record_details[candidate.source_record_id]['source_system_id']),
            'evidence_summary': {'safety_flags': list(candidate.safety_flags)},
            'scoring_version': 'demo-v1',
            'rule_version': 'rules-v1',
            'scored_by': 'system',
            'scored_at': _now_iso(),
            'source_record': self._source_record_details.get(candidate.source_record_id),
            'golden_record': self._golden_record_details.get(candidate.golden_id) if candidate.golden_id else None,
        }
        return candidate

    def save_match_candidate_features(self, features: List[MatchCandidateFeature]) -> None:
        super().save_match_candidate_features(features)
        for feature in features:
            self._match_candidate_feature_details[feature.feature_id] = {
                'feature_id': feature.feature_id,
                'candidate_id': feature.candidate_id,
                'feature_name': feature.feature_name,
                'display_label': feature.feature_name.title(),
                'feature_type': feature.feature_type,
                'source_value': feature.source_value,
                'golden_value': feature.golden_value,
                'normalized_source_value': feature.normalized_source_value,
                'normalized_golden_value': feature.normalized_golden_value,
                'similarity_algorithm': feature.similarity_algorithm,
                'similarity_score': feature.similarity_score,
                'priority': feature.priority,
                'calculated_weight': feature.weight,
                'weighted_score': feature.weighted_score,
                'is_match': feature.is_match,
                'is_conflict': feature.is_conflict,
                'is_blocking_feature': feature.is_blocking_feature,
                'is_visible_in_review': True,
                'evidence_json': json.loads(feature.evidence_json or '{}'),
            }

    def create_manual_review_task(self, task: ManualReviewTask) -> ManualReviewTask:
        super().create_manual_review_task(task)
        candidates_for_source = sorted(
            [item for item in self._match_candidate_details.values() if item.get('source_record_id') == task.source_record_id],
            key=lambda c: (c.get('rank_order', 999), -(c.get('total_score') or 0)),
        )
        best_candidate = candidates_for_source[0] if candidates_for_source else {}
        safety_flags = best_candidate.get('evidence_summary', {}).get('safety_flags', [])
        self._manual_review_task_details[task.task_id] = {
            'task_id': task.task_id,
            'source_record_id': task.source_record_id,
            'candidate_golden_ids': list(task.candidate_golden_ids),
            'best_confidence': task.best_confidence,
            'priority': 'medium',
            'status': task.status,
            'reason_code': task.reason,
            'assigned_to': task.assigned_to,
            'created_at': _now_iso(),
            'resolved_at': None,
            'notes': '',
            'safety_flags': safety_flags,
        }
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
        detail = self._manual_review_task_details[task.task_id]
        detail['status'] = 'resolved'
        detail['assigned_to'] = decision.reviewer
        detail['resolved_at'] = decision.decided_ts.isoformat()
        detail['notes'] = decision.notes or detail.get('notes', '')
        self._manual_review_decisions.append(
            {
                'decision_id': f"MRD-{len(self._manual_review_decisions) + 1:03d}",
                'task_id': task.task_id,
                'reviewer': decision.reviewer,
                'decision': decision.decision,
                'selected_golden_id': decision.golden_id,
                'notes': decision.notes,
                'decided_at': decision.decided_ts.isoformat(),
            }
        )
        return task

    def write_merge_history_event(self, event: MergeHistoryEvent) -> MergeHistoryEvent:
        super().write_merge_history_event(event)
        self._merge_history_details[event.event_id] = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'actor': event.actor,
            'source_record_id': event.source_record_id,
            'golden_id': event.golden_id,
            'details': _copy_json(event.details),
            'event_ts': _now_iso(),
        }
        return event

    def get_source_record(self, source_record_id: str) -> Optional[SourceRecord]:
        return self._source_records.get(source_record_id)

    def list_source_systems_data(self) -> List[Dict[str, Any]]:
        return sorted([_copy_json(item) for item in self._source_system_details.values()], key=lambda item: item['name'])

    def create_source_system(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        system_id = payload.get('system_id') or f"SYS-{len(self._source_system_details) + 1:03d}"
        detail = {
            'system_id': system_id,
            'name': payload['name'],
            'description': payload.get('description', ''),
            'trust_level': payload.get('trust_level', 'standard'),
            'is_internal': _bool(payload.get('is_internal', False)),
            'auto_merge_allowed': _bool(payload.get('auto_merge_allowed', True)),
            'is_active': _bool(payload.get('is_active', True)),
            'created_at': _now_iso(),
        }
        self._source_system_details[system_id] = detail
        self._source_systems[system_id] = SourceSystem(system_id, detail['name'], detail['trust_level'], detail['is_internal'])
        self._append_audit(event_type='source_system', entity_type='source_system', entity_id=system_id, actor=actor, action='create', new_value=detail)
        return _copy_json(detail)

    def get_source_system_detail(self, source_system_id: str) -> Optional[Dict[str, Any]]:
        detail = self._source_system_details.get(source_system_id)
        return _copy_json(detail) if detail else None

    def update_source_system(self, source_system_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        detail = self._source_system_details.get(source_system_id)
        if detail is None:
            raise KeyError(source_system_id)
        old = _copy_json(detail)
        detail.update({key: value for key, value in payload.items() if value is not None})
        self._source_systems[source_system_id] = SourceSystem(source_system_id, detail['name'], detail['trust_level'], _bool(detail['is_internal']))
        self._append_audit(event_type='source_system', entity_type='source_system', entity_id=source_system_id, actor=actor, action='update', old_value=old, new_value=detail)
        return _copy_json(detail)

    def deactivate_source_system(self, source_system_id: str, actor: str = 'api') -> Dict[str, Any]:
        return self.update_source_system(source_system_id, {'is_active': False}, actor=actor)

    def list_ingestion_batches(self) -> List[Dict[str, Any]]:
        return sorted([_copy_json(item) for item in self._ingestion_batches.values()], key=lambda item: item['created_at'], reverse=True)

    def get_ingestion_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        batch = self._ingestion_batches.get(batch_id)
        return _copy_json(batch) if batch else None

    def list_batch_records(self, batch_id: str) -> List[Dict[str, Any]]:
        return [self.get_source_record_detail(item['source_record_id']) for item in self._source_record_details.values() if item.get('ingestion_batch_id') == batch_id]

    def create_ingestion_batch(self, source_system_id: str, total_records: int, created_by: str = 'api') -> Dict[str, Any]:
        batch_id = f"BATCH-{len(self._ingestion_batches) + 1:03d}"
        batch = {
            'batch_id': batch_id,
            'source_system_id': source_system_id,
            'batch_status': 'processing',
            'total_records': total_records,
            'processed_records': 0,
            'failed_records': 0,
            'auto_merged': 0,
            'manual_review_count': 0,
            'new_golden_count': 0,
            'created_at': _now_iso(),
            'completed_at': None,
            'created_by': created_by,
        }
        self._ingestion_batches[batch_id] = batch
        return _copy_json(batch)

    def finalize_ingestion_batch(self, batch_id: str, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        batch = self._ingestion_batches[batch_id]
        batch['processed_records'] = len(decisions)
        batch['failed_records'] = sum(1 for item in decisions if item.get('decision') == 'failed')
        batch['auto_merged'] = sum(1 for item in decisions if item.get('decision') == 'auto-merge')
        batch['manual_review_count'] = sum(1 for item in decisions if item.get('decision') == 'manual-review')
        batch['new_golden_count'] = sum(1 for item in decisions if item.get('decision') == 'new-golden-record')
        batch['batch_status'] = 'completed'
        batch['completed_at'] = _now_iso()
        return _copy_json(batch)

    def attach_record_to_batch(self, source_record_id: str, batch_id: str, ingest_user: str) -> None:
        detail = self._source_record_details[source_record_id]
        detail['ingestion_batch_id'] = batch_id
        detail['ingest_user'] = ingest_user

    def find_latest_source_record(self, source_system_name: str, source_pk: str) -> Optional[Dict[str, Any]]:
        matches = [
            item for item in self._source_record_details.values()
            if item['source_pk'] == source_pk and self._source_system_name(item['source_system_id']).lower() == source_system_name.lower()
        ]
        if not matches:
            return None
        return _copy_json(matches[-1])

    def list_golden_record_details(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        items = [_copy_json(item) for item in self._golden_record_details.values() if self._golden_matches(item, filters)]
        return sorted(items, key=lambda item: item['golden_id'])

    def get_golden_record_detail(self, golden_id: str) -> Optional[Dict[str, Any]]:
        detail = self._golden_record_details.get(golden_id)
        if detail is None:
            return None
        payload = _copy_json(detail)
        payload['source_links'] = self.get_golden_source_links(golden_id)
        payload['field_provenance'] = self.get_golden_field_provenance(golden_id)
        return payload

    def create_golden_record_full(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        golden = GoldenRecord(
            golden_id=payload.get('golden_id') or f"GR-{len(self._golden_record_details) + 1:03d}",
            canonical_name=payload.get('canonical_name'),
            canonical_email=payload.get('canonical_email'),
            canonical_phone=payload.get('canonical_phone'),
            canonical_hkid=payload.get('canonical_hkid'),
            canonical_emplid=payload.get('canonical_emplid'),
            canonical_studentid=payload.get('canonical_studentid'),
            canonical_alumniid=payload.get('canonical_alumniid'),
            canonical_address=payload.get('canonical_address'),
            person_type=payload.get('person_type', 'person'),
            status=payload.get('status', 'active'),
            provenance=_copy_json(payload.get('provenance', {})),
        )
        self.create_golden_record(golden)
        detail = self._golden_record_details[golden.golden_id]
        detail.update({
            'confidence_level': payload.get('confidence_level', 'medium'),
            'is_possible_duplicate': _bool(payload.get('is_possible_duplicate', False)),
            'created_by': actor,
            'created_at': payload.get('created_at', _now_iso()),
            'updated_at': payload.get('updated_at', _now_iso()),
        })
        self._append_audit(event_type='golden_record', entity_type='golden_record', entity_id=golden.golden_id, actor=actor, action='create', new_value=detail)
        return _copy_json(detail)

    def update_golden_record_detail(self, golden_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        current = self._golden_record_details.get(golden_id)
        if current is None:
            raise KeyError(golden_id)
        old = _copy_json(current)
        current.update({key: value for key, value in payload.items() if value is not None})
        current['updated_at'] = _now_iso()
        golden = self._golden_records[golden_id]
        updated = replace(
            golden,
            canonical_name=current.get('canonical_name'),
            canonical_email=current.get('canonical_email'),
            canonical_phone=current.get('canonical_phone'),
            canonical_hkid=current.get('canonical_hkid'),
            canonical_emplid=current.get('canonical_emplid'),
            canonical_studentid=current.get('canonical_studentid'),
            canonical_alumniid=current.get('canonical_alumniid'),
            canonical_address=current.get('canonical_address'),
            person_type=current.get('person_type', golden.person_type),
            status=current.get('status', golden.status),
            provenance=_copy_json(current.get('provenance', {})),
        )
        self.update_golden_record(updated)
        self._append_audit(event_type='golden_record', entity_type='golden_record', entity_id=golden_id, actor=actor, action='update', old_value=old, new_value=current)
        return _copy_json(current)

    def get_golden_source_links(self, golden_id: str) -> List[Dict[str, Any]]:
        links = [
            {
                **_copy_json(link),
                'source_record': self.get_source_record_detail(link['source_record_id']),
            }
            for link in self._record_link_details.values()
            if link['golden_id'] == golden_id
        ]
        return sorted(links, key=lambda item: item['created_at'], reverse=True)

    def get_golden_history(self, golden_id: str) -> List[Dict[str, Any]]:
        events = [item for item in self._audit_events.values() if item['entity_id'] == golden_id]
        events.extend(item for item in self._merge_history_details.values() if item.get('golden_id') == golden_id)
        return sorted((_copy_json(item) for item in events), key=lambda item: item.get('event_ts', ''), reverse=True)

    def get_golden_field_provenance(self, golden_id: str) -> Dict[str, Any]:
        return {
            'golden_id': golden_id,
            'provenance': _copy_json(self._golden_record_details[golden_id].get('provenance', {})),
            'field_values': [
                _copy_json(item)
                for item in self._golden_field_values.values()
                if item['golden_id'] == golden_id
            ],
        }

    def override_golden_field(self, golden_id: str, field_name: str, value: Any, actor: str = 'api') -> Dict[str, Any]:
        if field_name not in _GOLDEN_FIELDS:
            raise KeyError(field_name)
        attr = _GOLDEN_FIELDS[field_name]
        golden = self._golden_record_details.get(golden_id)
        if golden is None:
            raise KeyError(golden_id)
        old = _copy_json(golden)
        golden[attr] = value
        golden.setdefault('provenance', {})[field_name] = {'source_system_name': 'Manual Override', 'source_record_id': None, 'updated_by': actor}
        golden['updated_at'] = _now_iso()
        updated = replace(self._golden_records[golden_id], **{attr: value}, provenance=_copy_json(golden['provenance']))
        self.update_golden_record(updated)
        field_value_id = f"GFV-{len(self._golden_field_values) + 1:03d}"
        self._golden_field_values[field_value_id] = {
            'field_value_id': field_value_id,
            'golden_id': golden_id,
            'field_name': field_name,
            'field_value': value,
            'source_record_id': None,
            'source_system_id': 'MANUAL',
            'applied_rule_id': 'MANUAL-OVERRIDE',
            'applied_at': _now_iso(),
            'golden_field': attr,
        }
        self._append_audit(event_type='golden_record', entity_type='golden_record', entity_id=golden_id, actor=actor, action='field_override', old_value=old, new_value=golden, notes=field_name)
        return self.get_golden_record_detail(golden_id)

    def link_source_to_golden(
        self,
        source_record_id: str,
        golden_id: str,
        *,
        actor: str = 'api',
        method: str = 'manual-link',
        confidence: float = 1.0,
        review_task_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        evidence: Optional[Any] = None,
    ) -> Dict[str, Any]:
        if golden_id not in self._golden_record_details:
            raise KeyError(golden_id)
        if source_record_id not in self._source_record_details:
            raise KeyError(source_record_id)
        for link in self._record_link_details.values():
            if link['source_record_id'] == source_record_id and link.get('is_active') and link['golden_id'] != golden_id:
                link['is_active'] = False
                link['link_status'] = 'unlinked'
                link['unlink_reason'] = 'Relinked to a different golden record'
                link['updated_at'] = _now_iso()
        link_id = f"LINK-{len(self._record_link_details) + 1:03d}"
        detail = {
            'link_id': link_id,
            'source_record_id': source_record_id,
            'golden_id': golden_id,
            'link_status': 'linked',
            'link_method': method,
            'confidence': confidence,
            'candidate_id': candidate_id,
            'review_task_id': review_task_id,
            'evidence_json': _copy_json(evidence or {}),
            'unlink_reason': None,
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
            'created_by': actor,
            'is_active': True,
        }
        self._record_link_details[link_id] = detail
        self._record_links[link_id] = RecordLink(link_id=link_id, source_record_id=source_record_id, golden_id=golden_id, confidence=confidence, method=method, evidence_json=json.dumps(detail['evidence_json']))
        self._add_field_values_for_link(detail)
        source_record = self._source_records[source_record_id]
        source_system = self._source_systems[source_record.system_id]
        updated = apply_survivorship(self._golden_records[golden_id], self._normalized_identities[source_record_id], source_record, source_system)
        updated = replace(updated, provenance=build_provenance(updated, source_record, source_system))
        self.update_golden_record(updated)
        self._append_merge_history(event_type='link', actor=actor, source_record_id=source_record_id, golden_id=golden_id, details={'method': method, 'confidence': confidence})
        self._append_audit(event_type='record_link', entity_type='record_link', entity_id=link_id, actor=actor, action='create', new_value=detail)
        return _copy_json(detail)

    def unlink_source_from_golden(self, source_record_id: str, golden_id: Optional[str], reason: str, actor: str = 'api') -> List[Dict[str, Any]]:
        updated_links: List[Dict[str, Any]] = []
        for link in self._record_link_details.values():
            if link['source_record_id'] != source_record_id:
                continue
            if golden_id and link['golden_id'] != golden_id:
                continue
            if not link.get('is_active'):
                continue
            link['is_active'] = False
            link['link_status'] = 'unlinked'
            link['unlink_reason'] = reason
            link['updated_at'] = _now_iso()
            updated_links.append(_copy_json(link))
            self._append_merge_history(event_type='unlink', actor=actor, source_record_id=source_record_id, golden_id=link['golden_id'], details={'reason': reason})
            self._append_audit(event_type='record_link', entity_type='record_link', entity_id=link['link_id'], actor=actor, action='unlink', new_value=link, notes=reason)
        if not updated_links:
            raise KeyError(source_record_id)
        return updated_links

    def merge_golden_records(self, source_golden_id: str, target_golden_id: str, merge_reason: str, actor: str = 'api') -> Dict[str, Any]:
        source = self._golden_record_details.get(source_golden_id)
        target = self._golden_record_details.get(target_golden_id)
        if source is None or target is None:
            raise KeyError('golden_record')
        old_target = _copy_json(target)
        for field in _GOLDEN_FIELDS.values():
            if not target.get(field) and source.get(field):
                target[field] = source[field]
        target['updated_at'] = _now_iso()
        source['status'] = 'merged'
        source['merged_into'] = target_golden_id
        self.update_golden_record_detail(target_golden_id, target, actor=actor)
        self.update_golden_record_detail(source_golden_id, source, actor=actor)
        for link in self._record_link_details.values():
            if link['golden_id'] == source_golden_id and link.get('is_active'):
                link['golden_id'] = target_golden_id
                link['updated_at'] = _now_iso()
        for duplicate in self._duplicate_candidates.values():
            if {duplicate['golden_id_a'], duplicate['golden_id_b']} == {source_golden_id, target_golden_id}:
                duplicate['status'] = 'merged'
                duplicate['resolved_at'] = _now_iso()
        self._append_merge_history(event_type='golden-merge', actor=actor, source_record_id=None, golden_id=target_golden_id, details={'source_golden_id': source_golden_id, 'target_golden_id': target_golden_id, 'merge_reason': merge_reason})
        self._append_audit(event_type='golden_record', entity_type='golden_record', entity_id=target_golden_id, actor=actor, action='merge', old_value=old_target, new_value=target, notes=merge_reason)
        return self.get_golden_record_detail(target_golden_id)

    def split_golden(self, golden_id: str, source_record_ids: Optional[List[str]], actor: str = 'api') -> Dict[str, Any]:
        source_record_ids = source_record_ids or []
        if not source_record_ids:
            active = [item['source_record_id'] for item in self.get_golden_source_links(golden_id) if item.get('is_active')]
            source_record_ids = active[:1]
        created = []
        for source_record_id in source_record_ids:
            source = self.get_source_record_detail(source_record_id)
            if source is None:
                continue
            self.unlink_source_from_golden(source_record_id, golden_id, 'Split from golden record', actor=actor)
            created.append(self._build_golden_from_source(source, actor))
        self._append_audit(event_type='golden_record', entity_type='golden_record', entity_id=golden_id, actor=actor, action='split', new_value={'source_record_ids': source_record_ids})
        return {'golden_id': golden_id, 'created_goldens': created}

    def list_source_records(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        items = []
        for detail in self._source_record_details.values():
            if not self._source_matches(detail, filters):
                continue
            payload = self.get_source_record_detail(detail['source_record_id'])
            if payload is not None:
                items.append(payload)
        return sorted(items, key=lambda item: item['source_record_id'])

    def get_source_record_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        detail = self._source_record_details.get(source_record_id)
        if detail is None:
            return None
        payload = _copy_json(detail)
        payload['source_system_name'] = self._source_system_name(detail['source_system_id'])
        payload['active_link'] = self._active_link_for_source(source_record_id)
        payload['links'] = [
            _copy_json(link) for link in self._record_link_details.values() if link['source_record_id'] == source_record_id
        ]
        return payload

    def get_normalized_identity_detail(self, source_record_id: str) -> Optional[Dict[str, Any]]:
        detail = self._normalized_identity_details.get(source_record_id)
        return _copy_json(detail) if detail else None

    def get_source_history(self, source_record_id: str) -> List[Dict[str, Any]]:
        events = [item for item in self._audit_events.values() if item['entity_id'] == source_record_id]
        events.extend(item for item in self._merge_history_details.values() if item.get('source_record_id') == source_record_id)
        return sorted((_copy_json(item) for item in events), key=lambda item: item.get('event_ts', ''), reverse=True)

    def preview_match(self, source_system_name: str, source_payload: Dict[str, Any], source_pk: str = 'preview') -> Dict[str, Any]:
        source_system = self._get_source_system_by_name(source_system_name)
        temp_source = SourceRecord(
            source_record_id='preview-record',
            system_id=source_system.system_id,
            source_pk=source_pk,
            raw_name=source_payload.get('name'),
            raw_email=source_payload.get('email'),
            raw_phone=source_payload.get('phone'),
            raw_address=source_payload.get('address'),
            raw_hkid=source_payload.get('hkid'),
            raw_emplid=source_payload.get('emplid'),
            raw_studentid=source_payload.get('studentid'),
            raw_alumniid=source_payload.get('alumniid'),
            raw_payload=_copy_json(source_payload),
        )
        norm = normalize_record(temp_source)
        candidates = generate_candidates(norm, self.load_golden_records())
        scored = []
        deterministic_results: Dict[str, str] = {}
        results = []
        for golden in candidates:
            deterministic = deterministic_check(norm, golden, source_system)
            if deterministic:
                deterministic_results[golden.golden_id] = deterministic
            score, features = score_candidate(norm, golden)
            scored.append((score, golden))
            results.append(
                {
                    'candidate_id': f"PREVIEW-{golden.golden_id}",
                    'golden_id': golden.golden_id,
                    'golden_record': _copy_json(self._golden_record_details[golden.golden_id]),
                    'total_score': score,
                    'deterministic_result': deterministic,
                    'feature_count': len(features),
                    'features': [
                        {
                            'feature_id': feature.feature_id,
                            'candidate_id': f"PREVIEW-{golden.golden_id}",
                            'feature_name': feature.feature_name,
                            'feature_type': feature.feature_type,
                            'source_value': feature.source_value,
                            'golden_value': feature.golden_value,
                            'normalized_source_value': feature.normalized_source_value,
                            'normalized_golden_value': feature.normalized_golden_value,
                            'similarity_algorithm': feature.similarity_algorithm,
                            'similarity_score': feature.similarity_score,
                            'priority': feature.priority,
                            'calculated_weight': feature.weight,
                            'weighted_score': feature.weighted_score,
                            'is_match': feature.is_match,
                            'is_conflict': feature.is_conflict,
                            'is_blocking_feature': feature.is_blocking_feature,
                            'is_visible_in_review': True,
                            'evidence_json': {},
                        }
                        for feature in features
                    ],
                }
            )
        scored.sort(key=lambda item: item[0], reverse=True)
        safety_flags = check_safety(norm, candidates, scored, source_system, self.config)
        decision = make_decision(norm, scored, deterministic_results, safety_flags, source_system, self.config)
        return {
            'normalized_identity': asdict(norm),
            'decision': asdict(decision),
            'candidates': sorted(results, key=lambda item: item['total_score'], reverse=True),
        }

    def list_match_candidates(self, source_record_id: Optional[str] = None) -> List[Dict[str, Any]]:
        items = [_copy_json(item) for item in self._match_candidate_details.values()]
        if source_record_id:
            items = [item for item in items if item['source_record_id'] == source_record_id]
        return sorted(items, key=lambda item: (item['source_record_id'], item.get('rank_order', 0), item['candidate_id']))

    def get_match_candidate_detail(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        detail = self._match_candidate_details.get(candidate_id)
        if detail is None:
            return None
        payload = _copy_json(detail)
        payload['features'] = self._candidate_features_for(candidate_id)
        return payload

    def get_match_candidate_features(self, candidate_id: str) -> List[Dict[str, Any]]:
        return self._candidate_features_for(candidate_id)

    def create_golden_from_source(self, source_record_id: str, actor: str = 'api') -> Dict[str, Any]:
        source = self.get_source_record_detail(source_record_id)
        if source is None:
            raise KeyError(source_record_id)
        return self._build_golden_from_source(source, actor)

    def rematch_source_record(self, source_record_id: str) -> Dict[str, Any]:
        source = self.get_source_record_detail(source_record_id)
        if source is None:
            raise KeyError(source_record_id)
        payload = {
            'name': source.get('raw_name'),
            'email': source.get('raw_email'),
            'phone': source.get('raw_phone'),
            'address': source.get('raw_address'),
            'hkid': source.get('raw_hkid'),
            'emplid': source.get('raw_emplid'),
            'studentid': source.get('raw_studentid'),
            'alumniid': source.get('raw_alumniid'),
        }
        return self.preview_match(self._source_system_name(source['source_system_id']), payload, source_pk=source['source_pk'])

    def list_review_tasks_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        items = []
        for task in self._manual_review_task_details.values():
            source = self._source_record_details.get(task['source_record_id'], {})
            if filters.get('status') and task.get('status') != filters['status']:
                continue
            if filters.get('priority') and task.get('priority') != filters['priority']:
                continue
            if filters.get('reason_code') and task.get('reason_code') != filters['reason_code']:
                continue
            if filters.get('assigned_to') and task.get('assigned_to') != filters['assigned_to']:
                continue
            if filters.get('source_system') and self._source_system_name(source.get('source_system_id', '')).lower() != str(filters['source_system']).lower():
                continue
            items.append(self.get_review_task_detail(task['task_id']))
        return sorted((item for item in items if item), key=lambda item: item['created_at'], reverse=True)

    def get_review_task_detail(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self._manual_review_task_details.get(task_id)
        if task is None:
            return None
        payload = _copy_json(task)
        payload['source_record'] = self.get_source_record_detail(task['source_record_id'])
        payload['candidates'] = [
            item for item in self.list_match_candidates(task['source_record_id']) if item.get('golden_id') in task.get('candidate_golden_ids', [])
        ]
        if not payload['candidates']:
            payload['candidates'] = [item for item in self.list_match_candidates(task['source_record_id'])]
        if not payload.get('recommended_decision') and payload['candidates']:
            payload['recommended_decision'] = payload['candidates'][0].get('decision_hint', '')
        return payload

    def assign_review_task(self, task_id: str, assigned_to: str, actor: str = 'api') -> Dict[str, Any]:
        task = self._manual_review_task_details.get(task_id)
        if task is None:
            raise KeyError(task_id)
        task['assigned_to'] = assigned_to
        if task['status'] == 'open':
            task['status'] = 'assigned'
        self._manual_review_tasks[task_id].assigned_to = assigned_to
        self._manual_review_tasks[task_id].status = task['status']
        self._append_audit(event_type='manual_review_task', entity_type='manual_review_task', entity_id=task_id, actor=actor, action='assign', new_value=task)
        return self.get_review_task_detail(task_id)

    def submit_review_decision(self, task_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        task = self._manual_review_task_details.get(task_id)
        if task is None:
            raise KeyError(task_id)
        decision = payload['decision']
        selected_golden_id = payload.get('selected_golden_id')
        notes = payload.get('notes', '')
        result: Dict[str, Any] = {'task_id': task_id, 'decision': decision}
        if decision in {'accept_merge', 'manual_override'} and selected_golden_id:
            result['link'] = self.link_source_to_golden(task['source_record_id'], selected_golden_id, actor=actor, method=decision, review_task_id=task_id)
            task['status'] = 'resolved'
        elif decision == 'create_new_golden':
            result['golden'] = self.create_golden_from_source(task['source_record_id'], actor=actor)
            task['status'] = 'resolved'
        elif decision == 'merge_goldens' and selected_golden_id:
            current = task.get('candidate_golden_ids', [])
            source_golden_id = next((item for item in current if item != selected_golden_id), selected_golden_id)
            result['merge'] = self.merge_golden_records(source_golden_id, selected_golden_id, notes or 'Manual review merge', actor=actor)
            task['status'] = 'resolved'
        elif decision == 'split_golden' and selected_golden_id:
            result['split'] = self.split_golden(selected_golden_id, [task['source_record_id']], actor=actor)
            task['status'] = 'resolved'
        elif decision == 'escalate':
            task['status'] = 'escalated'
        elif decision == 'request_more_info':
            task['status'] = 'waiting-info'
        elif decision == 'reject_candidate':
            task['status'] = 'resolved'
        else:
            task['status'] = 'resolved'
        task['assigned_to'] = payload.get('reviewer') or actor
        task['resolved_at'] = _now_iso() if task['status'] == 'resolved' else None
        task['notes'] = notes
        if task_id in self._manual_review_tasks:
            self._manual_review_tasks[task_id].status = task['status']
            self._manual_review_tasks[task_id].assigned_to = task['assigned_to']
        decision_row = {
            'decision_id': f"MRD-{len(self._manual_review_decisions) + 1:03d}",
            'task_id': task_id,
            'reviewer': task['assigned_to'],
            'decision': decision,
            'selected_golden_id': selected_golden_id,
            'notes': notes,
            'decided_at': _now_iso(),
        }
        self._manual_review_decisions.append(decision_row)
        self._append_audit(event_type='manual_review_task', entity_type='manual_review_task', entity_id=task_id, actor=actor, action='decision', new_value=decision_row)
        result['task'] = self.get_review_task_detail(task_id)
        result['decision_record'] = decision_row
        return result

    def list_review_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        return [item for item in self._manual_review_decisions if item['task_id'] == task_id]

    def list_review_decisions(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._manual_review_decisions), key=lambda item: item['decided_at'], reverse=True)

    def list_duplicate_candidates_data(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._duplicate_candidates.values()), key=lambda item: item['similarity_score'], reverse=True)

    def create_duplicate_candidate(self, golden_id_a: str, golden_id_b: str, detection_method: str = 'manual-flag', actor: str = 'api') -> Dict[str, Any]:
        if self._golden_record_details.get(golden_id_a) is None:
            raise KeyError(golden_id_a)
        if self._golden_record_details.get(golden_id_b) is None:
            raise KeyError(golden_id_b)
        # Return existing pair if already flagged
        for dup in self._duplicate_candidates.values():
            if {dup['golden_id_a'], dup['golden_id_b']} == {golden_id_a, golden_id_b}:
                return self.get_duplicate_candidate_detail(dup['duplicate_id'])
        dup_id = f"DUP-{len(self._duplicate_candidates) + 1:03d}"
        item: Dict[str, Any] = {
            'duplicate_id': dup_id,
            'golden_id_a': golden_id_a,
            'golden_id_b': golden_id_b,
            'similarity_score': 0.0,
            'status': 'open',
            'detection_method': detection_method,
            'created_at': _now_iso(),
            'resolved_at': None,
        }
        self._duplicate_candidates[dup_id] = item
        self._append_audit(
            event_type='duplicate_candidate', entity_type='duplicate_candidate',
            entity_id=dup_id, actor=actor, action='create', new_value=item,
        )
        return self.get_duplicate_candidate_detail(dup_id)

    def get_duplicate_candidate_detail(self, duplicate_id: str) -> Optional[Dict[str, Any]]:
        duplicate = self._duplicate_candidates.get(duplicate_id)
        if duplicate is None:
            return None
        payload = _copy_json(duplicate)
        payload['golden_a'] = self._golden_record_details.get(duplicate['golden_id_a'])
        payload['golden_b'] = self._golden_record_details.get(duplicate['golden_id_b'])
        comparisons = []
        if payload['golden_a'] and payload['golden_b']:
            for field_name, attr in _GOLDEN_FIELDS.items():
                comparisons.append({'field_name': field_name, 'value_a': payload['golden_a'].get(attr), 'value_b': payload['golden_b'].get(attr), 'same': payload['golden_a'].get(attr) == payload['golden_b'].get(attr)})
        payload['field_comparison'] = comparisons
        return payload

    def decide_duplicate_candidate(self, duplicate_id: str, decision: str, actor: str = 'api', target_golden_id: Optional[str] = None, notes: str = '') -> Dict[str, Any]:
        duplicate = self._duplicate_candidates.get(duplicate_id)
        if duplicate is None:
            raise KeyError(duplicate_id)
        duplicate['status'] = decision
        duplicate['resolved_at'] = _now_iso()
        if decision == 'merge':
            target = target_golden_id or duplicate['golden_id_a']
            source = duplicate['golden_id_b'] if target == duplicate['golden_id_a'] else duplicate['golden_id_a']
            duplicate['merge_result'] = self.merge_golden_records(source, target, notes or 'Duplicate golden merge', actor=actor)
        self._append_audit(event_type='duplicate_candidate', entity_type='duplicate_candidate', entity_id=duplicate_id, actor=actor, action='decision', new_value=duplicate, notes=notes)
        return self.get_duplicate_candidate_detail(duplicate_id)

    def list_matching_features(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._matching_features.values()), key=lambda item: (-int(item.get('priority', 0)), item['feature_name']))

    def get_matching_feature(self, feature_id: str) -> Optional[Dict[str, Any]]:
        item = self._matching_features.get(feature_id)
        return _copy_json(item) if item else None

    def create_matching_feature(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        feature_id = payload.get('feature_id') or f"MF-{len(self._matching_features) + 1:03d}"
        item = {
            'feature_id': feature_id,
            'feature_name': payload['feature_name'],
            'display_label': payload.get('display_label', payload['feature_name']),
            'feature_type': payload.get('feature_type', 'profile'),
            'is_enabled': _bool(payload.get('is_enabled', True)),
            'priority': int(payload.get('priority', 10)),
            'algorithm': payload.get('algorithm', 'sequence_matcher'),
            'is_auto_merge_eligible': _bool(payload.get('is_auto_merge_eligible', True)),
            'is_manual_review_only': _bool(payload.get('is_manual_review_only', False)),
            'is_blocking': _bool(payload.get('is_blocking', False)),
            'is_visible_in_review': _bool(payload.get('is_visible_in_review', True)),
            'is_active': _bool(payload.get('is_active', True)),
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
        }
        self._matching_features[feature_id] = item
        self._append_audit(event_type='matching_feature', entity_type='matching_feature', entity_id=feature_id, actor=actor, action='create', new_value=item)
        return _copy_json(item)

    def update_matching_feature(self, feature_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        item = self._matching_features.get(feature_id)
        if item is None:
            raise KeyError(feature_id)
        old = _copy_json(item)
        item.update({key: value for key, value in payload.items() if value is not None})
        item['updated_at'] = _now_iso()
        self._append_audit(event_type='matching_feature', entity_type='matching_feature', entity_id=feature_id, actor=actor, action='update', old_value=old, new_value=item)
        return _copy_json(item)

    def deactivate_matching_feature(self, feature_id: str, actor: str = 'api') -> Dict[str, Any]:
        return self.update_matching_feature(feature_id, {'is_active': False, 'is_enabled': False}, actor=actor)

    def list_matching_rules(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._matching_rules.values()), key=lambda item: item['rule_name'])

    def get_matching_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        item = self._matching_rules.get(rule_id)
        return _copy_json(item) if item else None

    def create_matching_rule(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        rule_id = payload.get('rule_id') or f"RULE-{len(self._matching_rules) + 1:03d}"
        item = {
            'rule_id': rule_id,
            'rule_name': payload['rule_name'],
            'description': payload.get('description', ''),
            'rule_type': payload.get('rule_type', 'probabilistic'),
            'conditions': _copy_json(payload.get('conditions', {})),
            'is_active': _bool(payload.get('is_active', True)),
            'version': 1,
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
            'created_by': actor,
        }
        self._matching_rules[rule_id] = item
        self._matching_rule_versions[rule_id] = [{
            'version_id': f'{rule_id}-V1',
            'rule_id': rule_id,
            'version_number': 1,
            'rule_snapshot': _copy_json(item),
            'changed_by': actor,
            'changed_at': _now_iso(),
            'change_reason': 'Initial creation',
        }]
        self._append_audit(event_type='matching_rule', entity_type='matching_rule', entity_id=rule_id, actor=actor, action='create', new_value=item)
        return _copy_json(item)

    def update_matching_rule(self, rule_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        item = self._matching_rules.get(rule_id)
        if item is None:
            raise KeyError(rule_id)
        old = _copy_json(item)
        item.update({key: value for key, value in payload.items() if value is not None})
        item['version'] = int(item.get('version', 1)) + 1
        item['updated_at'] = _now_iso()
        self._matching_rule_versions.setdefault(rule_id, []).append({
            'version_id': f"{rule_id}-V{item['version']}",
            'rule_id': rule_id,
            'version_number': item['version'],
            'rule_snapshot': _copy_json(item),
            'changed_by': actor,
            'changed_at': _now_iso(),
            'change_reason': payload.get('change_reason', 'Updated from API'),
        })
        self._append_audit(event_type='matching_rule', entity_type='matching_rule', entity_id=rule_id, actor=actor, action='update', old_value=old, new_value=item)
        return _copy_json(item)

    def deactivate_matching_rule(self, rule_id: str, actor: str = 'api') -> Dict[str, Any]:
        return self.update_matching_rule(rule_id, {'is_active': False, 'change_reason': 'Soft deactivated'}, actor=actor)

    def list_matching_rule_versions(self, rule_id: str) -> List[Dict[str, Any]]:
        return [_copy_json(item) for item in self._matching_rule_versions.get(rule_id, [])]

    def create_rule_simulation(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        simulation_id = f"SIM-{len(self._rule_simulations) + 1:03d}"
        simulation = {
            'simulation_id': simulation_id,
            'simulation_name': payload.get('simulation_name', f'Simulation {simulation_id}'),
            'rule_snapshot': _copy_json(payload.get('rule_snapshot', payload)),
            'status': 'completed',
            'created_at': _now_iso(),
            'completed_at': _now_iso(),
            'created_by': actor,
        }
        self._rule_simulations[simulation_id] = simulation
        results = []
        for index, candidate in enumerate(self.list_match_candidates()[:10], start=1):
            old_decision = candidate.get('decision_hint', 'manual-review')
            new_decision = old_decision
            if candidate.get('total_score', 0) >= 0.8 and payload.get('tighten_auto_merge'):
                new_decision = 'manual-review'
            results.append({
                'result_id': f'{simulation_id}-R{index:03d}',
                'simulation_id': simulation_id,
                'source_record_id': candidate['source_record_id'],
                'old_decision': old_decision,
                'new_decision': new_decision,
                'old_score': candidate.get('total_score', 0),
                'new_score': candidate.get('total_score', 0),
                'changed': old_decision != new_decision,
                'created_at': _now_iso(),
            })
        self._rule_simulation_results[simulation_id] = results
        return _copy_json(simulation)

    def get_rule_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        item = self._rule_simulations.get(simulation_id)
        return _copy_json(item) if item else None

    def get_rule_simulation_results(self, simulation_id: str) -> List[Dict[str, Any]]:
        return [_copy_json(item) for item in self._rule_simulation_results.get(simulation_id, [])]

    def get_thresholds(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._threshold_settings.values()), key=lambda item: item['setting_name'])

    def update_thresholds(self, payload: Dict[str, Any], actor: str = 'api') -> List[Dict[str, Any]]:
        for item in self._threshold_settings.values():
            name = item['setting_name']
            if name in payload:
                item['setting_value'] = float(payload[name])
                item['updated_at'] = _now_iso()
                item['updated_by'] = actor
        return self.get_thresholds()

    def list_survivorship_rules(self) -> List[Dict[str, Any]]:
        return sorted((_copy_json(item) for item in self._survivorship_rules.values()), key=lambda item: (item['field_name'], item['rule_name']))

    def get_survivorship_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        item = self._survivorship_rules.get(rule_id)
        return _copy_json(item) if item else None

    def create_survivorship_rule(self, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        rule_id = payload.get('rule_id') or f"SVR-{len(self._survivorship_rules) + 1:03d}"
        item = {
            'rule_id': rule_id,
            'field_name': payload['field_name'],
            'rule_name': payload['rule_name'],
            'strategy': payload.get('strategy', 'most_recent'),
            'priority_source_systems': payload.get('priority_source_systems', []),
            'is_active': _bool(payload.get('is_active', True)),
            'version': 1,
            'created_at': _now_iso(),
            'updated_at': _now_iso(),
        }
        self._survivorship_rules[rule_id] = item
        self._survivorship_rule_versions[rule_id] = [{
            'version_id': f'{rule_id}-V1',
            'rule_id': rule_id,
            'version_number': 1,
            'rule_snapshot': _copy_json(item),
            'changed_by': actor,
            'changed_at': _now_iso(),
        }]
        return _copy_json(item)

    def update_survivorship_rule(self, rule_id: str, payload: Dict[str, Any], actor: str = 'api') -> Dict[str, Any]:
        item = self._survivorship_rules.get(rule_id)
        if item is None:
            raise KeyError(rule_id)
        item.update({key: value for key, value in payload.items() if value is not None})
        item['version'] = int(item.get('version', 1)) + 1
        item['updated_at'] = _now_iso()
        self._survivorship_rule_versions.setdefault(rule_id, []).append({
            'version_id': f"{rule_id}-V{item['version']}",
            'rule_id': rule_id,
            'version_number': item['version'],
            'rule_snapshot': _copy_json(item),
            'changed_by': actor,
            'changed_at': _now_iso(),
        })
        return _copy_json(item)

    def deactivate_survivorship_rule(self, rule_id: str, actor: str = 'api') -> Dict[str, Any]:
        return self.update_survivorship_rule(rule_id, {'is_active': False}, actor=actor)

    def list_survivorship_rule_versions(self, rule_id: str) -> List[Dict[str, Any]]:
        return [_copy_json(item) for item in self._survivorship_rule_versions.get(rule_id, [])]

    def preview_survivorship(self, golden_id: str) -> Dict[str, Any]:
        golden = self._golden_records.get(golden_id)
        if golden is None:
            raise KeyError(golden_id)
        links = [item for item in self._record_link_details.values() if item['golden_id'] == golden_id and item.get('is_active')]
        previews = []
        for link in links:
            source_record = self._source_records.get(link['source_record_id'])
            if source_record is None:
                continue
            source_system = self._source_systems[source_record.system_id]
            updated = apply_survivorship(golden, self._normalized_identities[source_record.source_record_id], source_record, source_system)
            for field_name, attr in _GOLDEN_FIELDS.items():
                previews.append({
                    'preview_id': f"PRV-{len(self._survivorship_previews) + len(previews) + 1:03d}",
                    'golden_id': golden_id,
                    'field_name': field_name,
                    'current_value': getattr(golden, attr),
                    'preview_value': getattr(updated, attr),
                    'applied_rule_id': f'SVR-{field_name.upper()}',
                    'preview_ts': _now_iso(),
                })
        self._survivorship_previews.extend(previews)
        return {'golden_id': golden_id, 'previews': previews}

    def list_audit_events(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        events = []
        for event in self._audit_events.values():
            if filters.get('event_type') and event['event_type'] != filters['event_type']:
                continue
            if filters.get('entity_type') and event['entity_type'] != filters['entity_type']:
                continue
            if filters.get('entity_id') and event['entity_id'] != filters['entity_id']:
                continue
            if filters.get('actor') and event['actor'] != filters['actor']:
                continue
            events.append(_copy_json(event))
        return sorted(events, key=lambda item: item['event_ts'], reverse=True)

    def get_audit_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        event = self._audit_events.get(event_id)
        return _copy_json(event) if event else None

    def dashboard_summary(self) -> Dict[str, Any]:
        return {
            'total_source_records': len(self._source_record_details),
            'total_golden_records': len(self._golden_record_details),
            'auto_merged': sum(1 for item in self._record_link_details.values() if item.get('is_active') and item.get('link_method') in {'deterministic_match', 'high_confidence', 'strong-contact-match', 'accept_merge'}),
            'manual_review_pending': sum(1 for item in self._manual_review_task_details.values() if item.get('status') in {'open', 'assigned', 'escalated', 'waiting-info'}),
            'new_golden_created': sum(1 for item in self._record_link_details.values() if item.get('link_method') == 'new-golden-record'),
            'tier1_conflicts': sum(1 for item in self._manual_review_task_details.values() if item.get('reason_code') == 'tier1_conflict'),
            'duplicate_golden_alerts': sum(1 for item in self._duplicate_candidates.values() if item.get('status') in {'open', 'under_review'}),
            'failed_ingestion': sum(1 for item in self._source_record_details.values() if item.get('ingestion_status') == 'failed'),
        }

    def dashboard_process_counts(self) -> Dict[str, Any]:
        return {
            'ingested': len(self._source_record_details),
            'normalized': len(self._normalized_identity_details),
            'matched': len(self._match_candidate_details),
            'linked_active': sum(1 for item in self._record_link_details.values() if item.get('is_active')),
            'manual_review_open': sum(1 for item in self._manual_review_task_details.values() if item.get('status') in {'open', 'assigned'}),
            'duplicate_queue': sum(1 for item in self._duplicate_candidates.values() if item.get('status') in {'open', 'under_review'}),
            'rebatch_jobs': len(self._rebatch_jobs),
        }

    def dashboard_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        combined: List[Dict[str, Any]] = [_copy_json(item) for item in self._audit_events.values()]
        combined.extend(_copy_json(item) for item in self._merge_history_details.values())
        combined.sort(key=lambda item: item.get('event_ts', ''), reverse=True)
        return combined[:limit]
