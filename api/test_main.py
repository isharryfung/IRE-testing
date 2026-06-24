from __future__ import annotations

import unittest

from api import main


class ApiWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        main.startup_event()

    def test_ingest_manual_review_creates_task(self) -> None:
        response = main.ingest(
            main.IngestRequest(
                source_name="ExternalCRM",
                source_pk="CRM-101",
                run_match=True,
                payload=main.PersonRecord(
                    source_type="ExternalCRM",
                    name="John Smyth",
                    email="jsmith@ust.hk",
                    phone="+85299999999",
                ),
            )
        )

        self.assertEqual(response["status"], "accepted")
        self.assertEqual(response["match"]["decision"], "manual_review")
        self.assertIn("manual_review_task_id", response["match"])

    def test_review_decision_resolves_task(self) -> None:
        ingest_response = main.ingest(
            main.IngestRequest(
                source_name="ExternalCRM",
                source_pk="CRM-102",
                run_match=True,
                payload=main.PersonRecord(
                    source_type="ExternalCRM",
                    name="John Smyth",
                    email="jsmith@ust.hk",
                    phone="+85299999999",
                ),
            )
        )
        task_id = ingest_response["match"]["manual_review_task_id"]

        decision_response = main.submit_review_decision(
            task_id,
            main.ReviewDecisionRequest(
                decision="reject",
                reviewer_id="reviewer-1",
                notes="not the same person",
            ),
        )

        self.assertEqual(decision_response["status"], "recorded")
        self.assertEqual(decision_response["task_status"], "resolved")
        open_tasks = main.list_review_tasks()
        self.assertEqual(open_tasks["count"], 0)


if __name__ == "__main__":
    unittest.main()
