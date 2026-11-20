import unicodedata

import pytest

from common.normalization import clean_text, has_keyword, raw_text, week_number
from helpers import CONFIG, NORMALIZER

PATTERN = CONFIG.profile["week_sheet_pattern"]


def test_clean_text_collapses_whitespace_and_nfc():
    decomposed = unicodedata.normalize("NFD", "  Tiếng   Việt ")
    assert clean_text(decomposed) == "Tiếng Việt"
    assert clean_text(None) == ""


def test_raw_text_keeps_inner_text_but_clears_blank():
    assert raw_text(" Sử dụng năng lượng (Tiết 1)") == " Sử dụng năng lượng (Tiết 1)"
    assert raw_text("   ") is None
    assert raw_text(None) is None
    assert raw_text(5) == "5"


@pytest.mark.parametrize("raw, key", [
    ("Tin học ", "Tin học"),            # trailing space in the real file
    ("toán", "Toán"),                   # case-insensitive
    ("Mĩ thuật", "Mỹ thuật"),           # alias
    ("LS&ĐL", "Lịch sử & Địa lí"),
    ("HĐTV", "HĐTV/HĐTT"),              # interchangeable group
    ("HĐTT", "HĐTV/HĐTT"),
    ("HĐTV/HĐTT", "HĐTV/HĐTT"),
    ("GDTC chung", "GDTC chung"),       # must not merge with GDTC
    ("HĐTN (SHL)", "HĐTN (SHL)"),       # must not merge with HĐTN
    ("Môn lạ", "Môn lạ"),
    (None, ""),
])
def test_subject_key(raw, key):
    assert NORMALIZER.key(raw) == key


@pytest.mark.parametrize("name, number", [
    ("TUẦN 1", 1), ("TUẦN 09", 9), (unicodedata.normalize("NFD", "TUẦN 12"), 12),
    ("tuần 3", 3), ("MẪU", None), ("Ghi chú", None),
])
def test_week_number(name, number):
    assert week_number(name, PATTERN) == number


def test_has_keyword():
    assert has_keyword("Nghỉ lễ Quốc khánh", ["nghỉ"])
    assert not has_keyword("Ôn tập", ["nghỉ"])
