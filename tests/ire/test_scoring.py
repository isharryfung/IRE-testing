from __future__ import annotations

import pytest

from ire.models import GoldenRecord, NormalizedIdentity
from ire.scoring import score_candidate



def test_dynamic_scoring_with_only_name_and_email_present() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_name='jane chan', norm_email='jchan@example.com')
    golden = GoldenRecord(golden_id='GR-1', canonical_name='Jane Chan', canonical_email='jchan@example.com')
    total, features = score_candidate(norm, golden)

    weights = {feature.feature_name: feature.weight for feature in features}
    assert weights['email'] == pytest.approx(80 / 120)
    assert weights['name'] == pytest.approx(40 / 120)
    assert total == pytest.approx(1.0)



def test_perfect_score_all_fields_match() -> None:
    norm = NormalizedIdentity(
        source_record_id='1',
        norm_name='john smith',
        norm_email='john@example.com',
        norm_phone='85255512345',
        norm_address='clear water bay',
        norm_hkid='A1234567',
        norm_emplid='E1001',
        norm_studentid='S3003',
        norm_alumniid='A4004',
    )
    golden = GoldenRecord(
        golden_id='GR-1',
        canonical_name='John Smith',
        canonical_email='john@example.com',
        canonical_phone='85255512345',
        canonical_address='Clear Water Bay',
        canonical_hkid='A1234567',
        canonical_emplid='E1001',
        canonical_studentid='S3003',
        canonical_alumniid='A4004',
    )
    total, _ = score_candidate(norm, golden)
    assert total == pytest.approx(1.0)



def test_zero_score_when_nothing_matches() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_name='alice', norm_email='alice@example.com')
    golden = GoldenRecord(golden_id='GR-1', canonical_name='bob', canonical_email='bob@example.com')
    total, _ = score_candidate(norm, golden)
    assert total == pytest.approx(0.0)



def test_feature_evidence_contains_correct_fields_and_weights() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_name='jane chan', norm_email='jchan@example.com', norm_phone='85291234567')
    golden = GoldenRecord(golden_id='GR-1', canonical_name='Jane Chan', canonical_email='jchan@example.com', canonical_phone='85291234567')
    _, features = score_candidate(norm, golden)

    assert {feature.feature_name for feature in features} == {'name', 'email', 'phone'}
    for feature in features:
        assert feature.weight > 0
        assert feature.normalized_source_value
        assert feature.normalized_golden_value
