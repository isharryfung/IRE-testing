from __future__ import annotations

import unittest

from poc.ire_poc.decision import decide
from poc.ire_poc.matcher import rank_candidates
from poc.ire_poc.models import IdentityRecord
from poc.ire_poc.normalizer import normalize_record


class TestPOC(unittest.TestCase):
    def test_normalization(self) -> None:
        record = IdentityRecord(source_system=" hr ", source_pk="1", name="  Alex  Chan ", email=" A@B.com ", phone="+852-9000-1111", address="  X  ", hkid="A123456(7)")
        normalized = normalize_record(record)
        self.assertEqual(normalized.source_system, "HR")
        self.assertEqual(normalized.name, "alex chan")
        self.assertEqual(normalized.email, "a@b.com")
        self.assertEqual(normalized.phone, "85290001111")
        self.assertEqual(normalized.hkid, "A1234567")

    def test_deterministic_internal_tier1_auto_merge(self) -> None:
        incoming = normalize_record(IdentityRecord(source_system="HR", source_pk="in", hkid="A123456(7)", name="Alex Chan"))
        golden = normalize_record(IdentityRecord(source_system="HR", source_pk="1001", hkid="A1234567", name="Alex Chan"))
        candidates = rank_candidates(incoming, [golden])
        self.assertEqual(candidates[0].confidence, 1.0)

    def test_tier1_conflict_blocks(self) -> None:
        incoming = normalize_record(IdentityRecord(source_system="CRM", source_pk="in", hkid="B1111111", email="same@x.com"))
        golden = normalize_record(IdentityRecord(source_system="HR", source_pk="1001", hkid="A1234567", email="same@x.com"))
        outcome = decide(rank_candidates(incoming, [golden]), 0.85, 0.5)
        self.assertEqual(outcome.decision, "manual-review")

    def test_dynamic_scoring(self) -> None:
        incoming = normalize_record(IdentityRecord(source_system="CRM", source_pk="in", name="john smith", email="john@x.com", phone="85212345678"))
        golden = normalize_record(IdentityRecord(source_system="CRM", source_pk="1002", name="john smith", email="john@x.com", phone="85212345678"))
        candidate = rank_candidates(incoming, [golden])[0]
        self.assertAlmostEqual(candidate.confidence, 1.0, places=6)

    def test_threshold_decision(self) -> None:
        candidate = rank_candidates(
            normalize_record(IdentityRecord(source_system="CRM", source_pk="in", email="x@y.com")),
            [normalize_record(IdentityRecord(source_system="CRM", source_pk="g1", email="x@y.com"))],
        )
        outcome = decide(candidate, 0.85, 0.5)
        self.assertEqual(outcome.decision, "auto-merge")

    def test_multiple_high_candidates_manual_review(self) -> None:
        incoming = normalize_record(IdentityRecord(source_system="CRM", source_pk="in", email="same@x.com", phone="85290001111", name="alex chan"))
        golden_one = normalize_record(IdentityRecord(source_system="CRM", source_pk="g1", email="same@x.com", phone="85290001111", name="alex chan"))
        golden_two = normalize_record(IdentityRecord(source_system="CRM", source_pk="g2", email="same@x.com", phone="85290001111", name="alex chan"))
        outcome = decide(rank_candidates(incoming, [golden_one, golden_two]), 0.85, 0.5)
        self.assertEqual(outcome.decision, "manual-review")
        self.assertEqual(outcome.reason, "multiple-high-candidates")


if __name__ == "__main__":
    unittest.main()
