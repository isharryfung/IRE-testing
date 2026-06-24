from __future__ import annotations

from ire.config import Config
from ire.models import GoldenRecord, NormalizedIdentity, SourceSystem
from ire.safety import check_safety


CONFIG = Config()
INTERNAL = SourceSystem('SYS-001', 'HR', 'trusted', True)



def test_tier1_conflict_flag_when_conflict_present() -> None:
    norm = NormalizedIdentity(source_record_id='1', norm_hkid='A1234567')
    candidates = [GoldenRecord(golden_id='GR-1', canonical_hkid='B7654321')]
    flags = check_safety(norm, candidates, [(0.2, candidates[0])], INTERNAL, CONFIG)
    assert 'tier1_conflict' in flags



def test_multiple_high_candidates_flag() -> None:
    norm = NormalizedIdentity(source_record_id='1')
    candidates = [GoldenRecord(golden_id='GR-1'), GoldenRecord(golden_id='GR-2')]
    flags = check_safety(norm, candidates, [(0.91, candidates[0]), (0.88, candidates[1])], INTERNAL, CONFIG)
    assert 'multiple_high_candidates' in flags



def test_low_score_gap_flag() -> None:
    norm = NormalizedIdentity(source_record_id='1')
    candidates = [GoldenRecord(golden_id='GR-1'), GoldenRecord(golden_id='GR-2')]
    flags = check_safety(norm, candidates, [(0.70, candidates[0]), (0.66, candidates[1])], INTERNAL, CONFIG)
    assert 'low_score_gap' in flags
