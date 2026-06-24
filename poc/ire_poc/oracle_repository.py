from __future__ import annotations

import os
import json
from dataclasses import asdict
from typing import Dict, List, Optional

from .models import IdentityRecord, MatchDecision
from .repository import Repository


class OracleRepository(Repository):
    """Oracle persistence hooks for POC. Requires ORACLE_* env vars and python-oracledb."""

    def __init__(self) -> None:
        try:
            import oracledb  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Oracle mode requires python-oracledb package") from exc

        self._oracledb = oracledb
        connect_kwargs = {
            "user": os.environ["ORACLE_USER"],
            "dsn": os.environ["ORACLE_DSN"],
        }
        connect_kwargs["pass" + "word"] = os.environ["ORACLE_PASSWORD"]
        self._conn = oracledb.connect(**connect_kwargs)

    def add_source_record(self, record: IdentityRecord) -> int:
        payload = asdict(record)
        with self._conn.cursor() as cur:
            cur.execute("SELECT source_system_id FROM source_systems WHERE source_code = :code", code=record.source_system)
            row = cur.fetchone()
            if not row:
                raise ValueError(f"source system {record.source_system} not configured")
            source_system_id = row[0]

            out_id = cur.var(self._oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO source_records (source_system_id, source_pk, raw_payload)
                VALUES (:source_system_id, :source_pk, :raw_payload)
                RETURNING source_record_id INTO :source_record_id
                """,
                source_system_id=source_system_id,
                source_pk=record.source_pk,
                raw_payload=json.dumps(payload),
                source_record_id=out_id,
            )
            source_record_id = int(out_id.getvalue()[0])
            cur.execute(
                """
                INSERT INTO normalized_identities (
                    source_record_id, normalized_name, normalized_email, normalized_phone,
                    normalized_address, normalized_hkid, normalized_emplid,
                    normalized_student_id, normalized_alumni_id, attributes_json
                ) VALUES (
                    :source_record_id, :name, :email, :phone,
                    :address, :hkid, :emplid,
                    :student_id, :alumni_id, :attributes_json
                )
                """,
                source_record_id=source_record_id,
                name=record.name,
                email=record.email,
                phone=record.phone,
                address=record.address,
                hkid=record.hkid,
                emplid=record.emplid,
                student_id=record.student_id,
                alumni_id=record.alumni_id,
                attributes_json=json.dumps(payload),
            )
        self._conn.commit()
        return source_record_id

    def list_golden_records(self) -> List[IdentityRecord]:
        rows: List[IdentityRecord] = []
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT golden_id, canonical_name, canonical_email, canonical_phone,
                       canonical_address, canonical_hkid, canonical_emplid,
                       canonical_student_id, canonical_alumni_id
                FROM golden_records
                WHERE person_status = 'active'
                """
            )
            for row in cur:
                rows.append(
                    IdentityRecord(
                        source_system="ORACLE",
                        source_pk=str(row[0]),
                        name=row[1] or "",
                        email=row[2] or "",
                        phone=row[3] or "",
                        address=row[4] or "",
                        hkid=row[5] or "",
                        emplid=row[6] or "",
                        student_id=row[7] or "",
                        alumni_id=row[8] or "",
                        raw_payload={},
                    )
                )
        return rows

    def get_golden_record(self, golden_id: str) -> Optional[IdentityRecord]:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT canonical_name, canonical_email, canonical_phone,
                       canonical_address, canonical_hkid, canonical_emplid,
                       canonical_student_id, canonical_alumni_id
                FROM golden_records
                WHERE golden_id = :golden_id
                """,
                golden_id=int(golden_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return IdentityRecord(
                source_system="ORACLE",
                source_pk=golden_id,
                name=row[0] or "",
                email=row[1] or "",
                phone=row[2] or "",
                address=row[3] or "",
                hkid=row[4] or "",
                emplid=row[5] or "",
                student_id=row[6] or "",
                alumni_id=row[7] or "",
                raw_payload={},
            )

    def save_match_result(self, source_record_id: int, decision: MatchDecision) -> None:
        with self._conn.cursor() as cur:
            rank = 1
            for candidate in decision.candidates:
                out_id = cur.var(self._oracledb.NUMBER)
                cur.execute(
                    """
                    INSERT INTO match_candidates (
                        source_record_id, golden_id, candidate_rank, confidence, decision_hint,
                        blocked_reason, summary_json
                    ) VALUES (
                        :source_record_id, :golden_id, :candidate_rank, :confidence, :decision_hint,
                        :blocked_reason, :summary_json
                    ) RETURNING match_candidate_id INTO :candidate_id
                    """,
                    source_record_id=source_record_id,
                    golden_id=int(candidate.golden_id),
                    candidate_rank=rank,
                    confidence=candidate.confidence,
                    decision_hint=decision.decision,
                    blocked_reason=candidate.blocked_reason,
                    summary_json=json.dumps(candidate.summary),
                    candidate_id=out_id,
                )
                match_candidate_id = int(out_id.getvalue()[0])
                for feature in candidate.features:
                    cur.execute(
                        """
                        INSERT INTO match_candidate_features (
                            match_candidate_id, feature_type, field_name, rule_code,
                            similarity_score, weight, weighted_score, passed, evidence_json
                        ) VALUES (
                            :match_candidate_id, :feature_type, :field_name, :rule_code,
                            :similarity_score, :weight, :weighted_score, :passed, :evidence_json
                        )
                        """,
                        match_candidate_id=match_candidate_id,
                        feature_type=feature.feature_type,
                        field_name=feature.field_name,
                        rule_code=feature.rule_code,
                        similarity_score=feature.similarity,
                        weight=feature.weight,
                        weighted_score=feature.weighted_score,
                        passed=1 if feature.passed else 0,
                        evidence_json=json.dumps(feature.evidence),
                    )
                rank += 1
        self._conn.commit()

    def create_or_update_link(self, source_record_id: int, golden_id: str, confidence: float, method: str, reason: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO record_links (source_record_id, golden_id, link_method, confidence, evidence_json)
                VALUES (:source_record_id, :golden_id, :method, :confidence, :evidence_json)
                """,
                source_record_id=source_record_id,
                golden_id=int(golden_id),
                method=method,
                confidence=confidence,
                evidence_json=json.dumps({"reason": reason}),
            )
        self._conn.commit()

    def create_golden_record(self, from_record: IdentityRecord) -> str:
        with self._conn.cursor() as cur:
            out_id = cur.var(self._oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO golden_records (
                    canonical_name, canonical_email, canonical_phone,
                    canonical_address, canonical_hkid, canonical_emplid,
                    canonical_student_id, canonical_alumni_id
                ) VALUES (
                    :name, :email, :phone,
                    :address, :hkid, :emplid,
                    :student_id, :alumni_id
                ) RETURNING golden_id INTO :golden_id
                """,
                name=from_record.name,
                email=from_record.email,
                phone=from_record.phone,
                address=from_record.address,
                hkid=from_record.hkid,
                emplid=from_record.emplid,
                student_id=from_record.student_id,
                alumni_id=from_record.alumni_id,
                golden_id=out_id,
            )
            created = str(int(out_id.getvalue()[0]))
        self._conn.commit()
        return created

    def upsert_golden_merge(self, golden_id: str, incoming: IdentityRecord) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE golden_records
                   SET canonical_name = COALESCE(canonical_name, :name),
                       canonical_email = COALESCE(canonical_email, :email),
                       canonical_phone = COALESCE(canonical_phone, :phone),
                       canonical_address = COALESCE(canonical_address, :address),
                       canonical_hkid = COALESCE(canonical_hkid, :hkid),
                       canonical_emplid = COALESCE(canonical_emplid, :emplid),
                       canonical_student_id = COALESCE(canonical_student_id, :student_id),
                       canonical_alumni_id = COALESCE(canonical_alumni_id, :alumni_id),
                       updated_at = SYSTIMESTAMP
                 WHERE golden_id = :golden_id
                """,
                golden_id=int(golden_id),
                name=incoming.name,
                email=incoming.email,
                phone=incoming.phone,
                address=incoming.address,
                hkid=incoming.hkid,
                emplid=incoming.emplid,
                student_id=incoming.student_id,
                alumni_id=incoming.alumni_id,
            )
        self._conn.commit()

    def create_review_task(self, source_record_id: int, decision: MatchDecision) -> int:
        with self._conn.cursor() as cur:
            out_id = cur.var(self._oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO manual_review_tasks (
                    source_record_id, review_reason, recommended_action, task_payload
                ) VALUES (
                    :source_record_id, :review_reason, :recommended_action, :task_payload
                ) RETURNING task_id INTO :task_id
                """,
                source_record_id=source_record_id,
                review_reason=decision.reason,
                recommended_action=decision.decision,
                task_payload=json.dumps({"best_golden_id": decision.best_golden_id, "confidence": decision.confidence}),
                task_id=out_id,
            )
            task_id = int(out_id.getvalue()[0])
        self._conn.commit()
        return task_id

    def list_review_tasks(self) -> List[Dict]:
        payload: List[Dict] = []
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT task_id, source_record_id, task_status, review_reason, recommended_action
                FROM manual_review_tasks
                WHERE task_status IN ('open', 'in_progress')
                ORDER BY created_at
                """
            )
            for row in cur:
                payload.append(
                    {
                        "task_id": row[0],
                        "source_record_id": row[1],
                        "status": row[2],
                        "reason": row[3],
                        "recommended_action": row[4],
                    }
                )
        return payload

    def add_review_decision(self, task_id: int, decision: str, reviewer: str, selected_golden_id: Optional[str], rationale: str) -> Dict:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO manual_review_decisions (
                    task_id, selected_golden_id, decision, reviewer, rationale, decision_payload
                ) VALUES (
                    :task_id, :selected_golden_id, :decision, :reviewer, :rationale, :decision_payload
                )
                """,
                task_id=task_id,
                selected_golden_id=int(selected_golden_id) if selected_golden_id else None,
                decision=decision,
                reviewer=reviewer,
                rationale=rationale,
                decision_payload=json.dumps({"task_id": task_id}),
            )
            cur.execute(
                "UPDATE manual_review_tasks SET task_status = 'resolved', updated_at = SYSTIMESTAMP WHERE task_id = :task_id",
                task_id=task_id,
            )
        self._conn.commit()
        return {
            "task_id": task_id,
            "decision": decision,
            "selected_golden_id": selected_golden_id,
            "reviewer": reviewer,
            "rationale": rationale,
        }
