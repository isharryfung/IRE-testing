from __future__ import annotations

from ire.normalizer import normalize_email, normalize_hkid, normalize_id, normalize_name, normalize_phone



def test_normalize_name_strips_and_lowercases() -> None:
    assert normalize_name('  John   SMITH ') == 'john smith'



def test_normalize_email_lowercases() -> None:
    assert normalize_email('  User@Example.COM ') == 'user@example.com'



def test_normalize_phone_keeps_only_digits() -> None:
    assert normalize_phone('+852 9123-4567') == '85291234567'



def test_normalize_hkid_uppercases_and_removes_special_chars() -> None:
    assert normalize_hkid(' a123456(7) ') == 'A1234567'



def test_normalize_id_strips_and_uppercases() -> None:
    assert normalize_id(' e1001 ') == 'E1001'
