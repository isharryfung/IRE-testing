from __future__ import annotations

import json
from typing import Dict, List, Optional

from .db import get_connection


class DemoRepository:
    def __init__(self, golden_records: Dict[str, object]) -> None:
        self._golden_records = golden_records
        self._source_records: Dict[int, Dict[str, object]] = {}
        self._manual_tasks: Dict[int, Dict[str, object]] = {}
        self._history: List[Dict[str, object]] = []
        self._next_source_id = 1
        self._next_task_id = 1

    def insert_source_record(self, **data: object) -> int:
        source_record_id = self._next_source_id
        self._next_source_id += 1
        self._source_records[source_record_id] = {"source_record_id": source_record_id, **data}
        return source_record_id

    def list_golden_records(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for golden_id, rec in self._golden_records.items():
            model_dump = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)
            rows.append({"golden_id": str(golden_id), **model_dump})
        return rows

    def get_golden_record(self, golden_id: str) -> Optional[Dict[str, object]]:
        rec = self._golden_records.get(str(golden_id))
        if rec is None:
            return None
        model_dump = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)
        return {"golden_id": str(golden_id), **model_dump}

    def update_golden_record(self, golden_id: str, data: Dict[str, object]) -> None:
        self._golden_records[str(golden_id)] = data["record"]

    def insert_record_link(
        self,
        source_record_id: int,
        golden_id: str,
        confidence: float,
        link_method: str,
        evidence: Dict[str, object],
    ) -> None:
        self._history.append(
            {
                "event_type": "link",
                "source_record_id": source_record_id,
                "golden_id": golden_id,
                "confidence": confidence,
                "link_method": link_method,
                "evidence": evidence,
            }
        )

    def insert_manual_review_task(self, source_record_id: int, candidate_goldens: List[str], best_confidence: float) -> int:
        task_id = self._next_task_id
        self._next_task_id += 1
        self._manual_tasks[task_id] = {
            "task_id": task_id,
            "source_record_id": source_record_id,
            "candidate_goldens": list(candidate_goldens),
            "best_confidence": best_confidence,
            "status": "open",
            "assigned_to": None,
            "reviewer_decision": None,
            "notes": None,
        }
        return task_id

    def list_open_manual_review_tasks(self) -> List[Dict[str, object]]:
        return [task for task in self._manual_tasks.values() if task.get("status") == "open"]

    def get_manual_review_task(self, task_id: int) -> Optional[Dict[str, object]]:
        return self._manual_tasks.get(task_id)

    def resolve_manual_review_task(
        self,
        task_id: int,
        decision: str,
        reviewer_id: str,
        notes: Optional[str],
        status: str,
    ) -> None:
        task = self._manual_tasks.get(task_id)
        if task is None:
            return
        task["reviewer_decision"] = decision
        task["assigned_to"] = reviewer_id
        task["notes"] = notes
        task["status"] = status

    def insert_merge_history_event(self, event_type: str, actor: str, details: Dict[str, object]) -> None:
        self._history.append({"event_type": event_type, "actor": actor, "details": details})


class OracleRepository:
    def insert_source_record(self, **data: object) -> int:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            source_record_id_var = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO source_records (
                    source_name, source_pk, raw_payload,
                    normalized_name, normalized_email, normalized_phone,
                    hkid, emplid, studentid, alumniid, address, ingest_user
                ) VALUES (
                    :source_name, :source_pk, :raw_payload,
                    :normalized_name, :normalized_email, :normalized_phone,
                    :hkid, :emplid, :studentid, :alumniid, :address, :ingest_user
                ) RETURNING source_record_id INTO :source_record_id
                """,
                {
                    **data,
                    "source_record_id": source_record_id_var,
                },
            )
            conn.commit()
            return int(source_record_id_var.getvalue()[0])

    def list_golden_records(self) -> List[Dict[str, object]]:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT golden_id, canonical_name, canonical_email, canonical_phone,
                       canonical_hkid, canonical_emplid, canonical_studentid,
                       canonical_alumniid, canonical_address
                FROM golden_records
                WHERE status = 'active'
                ORDER BY golden_id
                """
            )
            rows = []
            for row in cursor.fetchall():
                rows.append(
                    {
                        "golden_id": str(row[0]),
                        "name": row[1],
                        "email": row[2],
                        "phone": row[3],
                        "hkid": row[4],
                        "emplid": row[5],
                        "studentid": row[6],
                        "alumniid": row[7],
                        "address": row[8],
                    }
                )
            return rows

    def get_golden_record(self, golden_id: str) -> Optional[Dict[str, object]]:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT golden_id, canonical_name, canonical_email, canonical_phone,
                       canonical_hkid, canonical_emplid, canonical_studentid,
                       canonical_alumniid, canonical_address
                FROM golden_records
                WHERE golden_id = :golden_id
                """,
                {"golden_id": golden_id},
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "golden_id": str(row[0]),
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "hkid": row[4],
                "emplid": row[5],
                "studentid": row[6],
                "alumniid": row[7],
                "address": row[8],
            }

    def update_golden_record(self, golden_id: str, data: Dict[str, object]) -> None:
        record = data["record"]
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE golden_records
                SET canonical_name = :name,
                    canonical_email = :email,
                    canonical_phone = :phone,
                    canonical_hkid = :hkid,
                    canonical_emplid = :emplid,
                    canonical_studentid = :studentid,
                    canonical_alumniid = :alumniid,
                    canonical_address = :address,
                    last_updated = SYSTIMESTAMP
                WHERE golden_id = :golden_id
                """,
                {
                    "golden_id": golden_id,
                    "name": record.name,
                    "email": record.email,
                    "phone": record.phone,
                    "hkid": record.hkid,
                    "emplid": record.emplid,
                    "studentid": record.studentid,
                    "alumniid": record.alumniid,
                    "address": record.address,
                },
            )
            conn.commit()

    def insert_record_link(
        self,
        source_record_id: int,
        golden_id: str,
        confidence: float,
        link_method: str,
        evidence: Dict[str, object],
    ) -> None:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO record_links (source_record_id, golden_id, link_confidence, link_method, evidence)
                VALUES (:source_record_id, :golden_id, :link_confidence, :link_method, :evidence)
                """,
                {
                    "source_record_id": source_record_id,
                    "golden_id": golden_id,
                    "link_confidence": confidence,
                    "link_method": link_method,
                    "evidence": json.dumps(evidence),
                },
            )
            conn.commit()

    def insert_manual_review_task(self, source_record_id: int, candidate_goldens: List[str], best_confidence: float) -> int:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            task_id_var = cursor.var(int)
            cursor.execute(
                """
                INSERT INTO manual_review_queue (
                    source_record_id, candidate_goldens, best_confidence, status
                ) VALUES (
                    :source_record_id, :candidate_goldens, :best_confidence, 'open'
                ) RETURNING task_id INTO :task_id
                """,
                {
                    "source_record_id": source_record_id,
                    "candidate_goldens": ",".join(candidate_goldens),
                    "best_confidence": best_confidence,
                    "task_id": task_id_var,
                },
            )
            conn.commit()
            return int(task_id_var.getvalue()[0])

    def list_open_manual_review_tasks(self) -> List[Dict[str, object]]:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT task_id, source_record_id, candidate_goldens, best_confidence,
                       status, assigned_to, reviewer_decision, notes
                FROM manual_review_queue
                WHERE status = 'open'
                ORDER BY created_ts
                """
            )
            rows = []
            for row in cursor.fetchall():
                rows.append(
                    {
                        "task_id": int(row[0]),
                        "source_record_id": int(row[1]),
                        "candidate_goldens": (row[2] or "").split(",") if row[2] else [],
                        "best_confidence": float(row[3]) if row[3] is not None else None,
                        "status": row[4],
                        "assigned_to": row[5],
                        "reviewer_decision": row[6],
                        "notes": row[7],
                    }
                )
            return rows

    def get_manual_review_task(self, task_id: int) -> Optional[Dict[str, object]]:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT task_id, source_record_id, candidate_goldens, best_confidence,
                       status, assigned_to, reviewer_decision, notes
                FROM manual_review_queue
                WHERE task_id = :task_id
                """,
                {"task_id": task_id},
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "task_id": int(row[0]),
                "source_record_id": int(row[1]),
                "candidate_goldens": (row[2] or "").split(",") if row[2] else [],
                "best_confidence": float(row[3]) if row[3] is not None else None,
                "status": row[4],
                "assigned_to": row[5],
                "reviewer_decision": row[6],
                "notes": row[7],
            }

    def resolve_manual_review_task(
        self,
        task_id: int,
        decision: str,
        reviewer_id: str,
        notes: Optional[str],
        status: str,
    ) -> None:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE manual_review_queue
                SET reviewer_decision = :decision,
                    assigned_to = :reviewer_id,
                    notes = :notes,
                    status = :status,
                    resolved_ts = CASE WHEN :status = 'resolved' THEN SYSTIMESTAMP ELSE NULL END
                WHERE task_id = :task_id
                """,
                {
                    "task_id": task_id,
                    "decision": decision,
                    "reviewer_id": reviewer_id,
                    "notes": notes,
                    "status": status,
                },
            )
            conn.commit()

    def insert_merge_history_event(self, event_type: str, actor: str, details: Dict[str, object]) -> None:
        with get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO merge_history (event_type, actor, details)
                VALUES (:event_type, :actor, :details)
                """,
                {
                    "event_type": event_type,
                    "actor": actor,
                    "details": json.dumps(details),
                },
            )
            conn.commit()
