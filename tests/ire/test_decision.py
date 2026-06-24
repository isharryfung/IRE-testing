from __future__ import annotations

from ire.config import Config
from ire.decision import make_decision
from ire.models import GoldenRecord, NormalizedIdentity, SourceSystem


CONFIG = Config()
SOURCE = SourceSystem('SYS-001', 'HR', 'trusted', True)
NORM = NormalizedIdentity(source_record_id='1')



def test_auto_merge_when_deterministic_match() -> None:
    golden = GoldenRecord(golden_id='GR-1')
    decision = make_decision(NORM, [(0.6, golden)], {'GR-1': 'match'}, [], SOURCE, CONFIG)
    assert decision.decision == 'auto-merge'



def test_manual_review_when_tier1_conflict() -> None:
    golden = GoldenRecord(golden_id='GR-1')
    decision = make_decision(NORM, [(0.9, golden)], {'GR-1': 'conflict'}, ['tier1_conflict'], SOURCE, CONFIG)
    assert decision.decision == 'manual-review'



def test_new_golden_record_when_low_score() -> None:
    golden = GoldenRecord(golden_id='GR-1')
    decision = make_decision(NORM, [(0.2, golden)], {}, [], SOURCE, CONFIG)
    assert decision.decision == 'new-golden-record'



def test_manual_review_when_multiple_high_candidates() -> None:
    golden = GoldenRecord(golden_id='GR-1')
    decision = make_decision(NORM, [(0.9, golden)], {}, ['multiple_high_candidates'], SOURCE, CONFIG)
    assert decision.decision == 'manual-review'
