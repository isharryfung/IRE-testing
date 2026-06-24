from __future__ import annotations

from ire.deterministic import deterministic_check, has_tier1_conflict
from ire.models import GoldenRecord, NormalizedIdentity, SourceSystem


INTERNAL = SourceSystem('SYS-001', 'HR', 'trusted', True)
THIRD_PARTY = SourceSystem('SYS-005', 'ThirdParty', 'untrusted', False)



def test_internal_id_exact_match_returns_match() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_emplid='E1001')
    golden = GoldenRecord(golden_id='GR-1', canonical_emplid='E1001')
    assert deterministic_check(norm, golden, INTERNAL) == 'match'



def test_third_party_id_match_without_name_email_support_returns_none() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_hkid='A1234567', norm_name='john different', norm_email='other@example.com')
    golden = GoldenRecord(golden_id='GR-1', canonical_hkid='A1234567', canonical_name='John Smith', canonical_email='john@example.com')
    assert deterministic_check(norm, golden, THIRD_PARTY) is None



def test_tier1_conflict_returns_conflict() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_hkid='A1234567')
    golden = GoldenRecord(golden_id='GR-1', canonical_hkid='B7654321')
    assert deterministic_check(norm, golden, INTERNAL) == 'conflict'



def test_has_tier1_conflict_detects_hkid_mismatch() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_hkid='A1234567')
    golden = GoldenRecord(golden_id='GR-1', canonical_hkid='B7654321')
    assert has_tier1_conflict(norm, golden) is True
