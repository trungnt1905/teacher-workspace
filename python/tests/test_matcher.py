from common.day_off_detector import detect_off_sessions
from common.timetable_matcher import match_week
from helpers import KEYWORDS, NORMALIZER, make_week

ALL = {"Toán", "Tiếng Việt", "Khoa học", "HĐTV/HĐTT", "HĐTN (SHDC)", "Đạo đức"}


def run(source, target, selected=ALL, manual=None):
    off = detect_off_sessions(source, KEYWORDS, manual)
    return match_week(source, target, week_no=1, selected_subjects=set(selected), off_sessions=off,
                      normalizer=NORMALIZER, keywords=KEYWORDS)


def status(result):
    return {s["subject"]: s["status"] for s in result.subjects}


def test_matches_by_subject_order_not_by_row():
    # Example from DETAIL_DESIGN §4.6
    source = make_week([("Hai", "SÁNG", "Tiếng Việt", "Bài A"), ("Hai", "SÁNG", "Toán", "Bài B", "Phấn"),
                        ("Hai", "SÁNG", "Khoa học", "Bài C"), ("Ba", "SÁNG", "Toán", "Bài D")])
    target = make_week([("Hai", "SÁNG", "Toán", None), ("Hai", "SÁNG", "Tiếng Việt", None),
                        ("Hai", "SÁNG", "Khoa học", None), ("Ba", "SÁNG", "Toán", None)])
    result = run(source, target)
    assert result.writes == {"E3": "Bài B", "F3": "Phấn", "E4": "Bài A", "F4": None,
                             "E5": "Bài C", "F5": None, "E6": "Bài D", "F6": None}
    assert set(status(result).values()) == {"matched"}


def test_count_mismatch_skips_only_that_subject():
    source = make_week([("Hai", "SÁNG", "Toán", "T1"), ("Hai", "SÁNG", "Toán", "T2"), ("Hai", "SÁNG", "Tiếng Việt", "V1")])
    target = make_week([("Hai", "SÁNG", "Toán", None), ("Hai", "SÁNG", "Tiếng Việt", None), ("Hai", "SÁNG", "Đạo đức", None)])
    result = run(source, target)
    assert status(result) == {"Toán": "skipped_count_mismatch", "Tiếng Việt": "matched",
                              "Đạo đức": "skipped_unknown_subject"}
    assert result.writes == {"E4": "V1", "F4": None}
    codes = {w["code"] for w in result.warnings}
    assert codes == {"SUBJECT_COUNT_MISMATCH", "UNKNOWN_SUBJECT"}


def test_empty_lesson_skips_subject_with_warning():
    source = make_week([("Hai", "SÁNG", "HĐTN (SHDC)", None), ("Hai", "SÁNG", "Toán", "T1")])
    target = make_week([("Hai", "SÁNG", "HĐTN (SHDC)", None), ("Hai", "SÁNG", "Toán", None)])
    result = run(source, target)
    assert status(result) == {"HĐTN (SHDC)": "skipped_empty_lesson", "Toán": "matched"}
    assert "E3" not in result.writes
    assert result.warnings[0]["code"] == "EMPTY_LESSON"
    assert result.warnings[0]["message"] == (
        "Tuần 1, môn HĐTN (SHDC): file nguồn chưa có tên bài ở thứ Hai tiết 1 — môn này không được điền.")


def test_keyword_nghi_marks_period_off():
    source = make_week([("Hai", "SÁNG", "Toán", "Nghỉ lễ"), ("Hai", "SÁNG", "Tiếng Việt", "V1")])
    target = make_week([("Hai", "SÁNG", "Toán", None), ("Hai", "SÁNG", "Tiếng Việt", None)])
    result = run(source, target)
    assert status(result)["Toán"] == "skipped_day_off"


def test_day_off_skips_subjects_with_target_slot_that_day_even_if_counts_match():
    # §4.8 example: Khoa học is on Tue/Thu in the source (unaffected) but on Mon/Wed in the target.
    source = make_week([
        ("Hai", "SÁNG", "Toán", None), ("Hai", "SÁNG", "Tiếng Việt", None),       # Monday off (all empty)
        ("Ba", "SÁNG", "Khoa học", "K1"), ("Năm", "SÁNG", "Khoa học", "K2"),
        ("Tư", "SÁNG", "Đạo đức", "D1"),
    ])
    target = make_week([
        ("Hai", "SÁNG", "Khoa học", None), ("Ba", "SÁNG", "Đạo đức", None),
        ("Tư", "SÁNG", "Khoa học", None), ("Năm", "SÁNG", "Toán", None), ("Năm", "SÁNG", "Tiếng Việt", None),
    ])
    result = run(source, target)
    assert status(result) == {"Khoa học": "skipped_day_off", "Đạo đức": "matched",
                              "Toán": "skipped_day_off", "Tiếng Việt": "skipped_day_off"}
    assert set(result.writes) == {"E4", "F4"}


def test_unselected_subjects_are_ignored_entirely():
    source = make_week([("Hai", "SÁNG", "Tiếng Anh", "E1"), ("Hai", "SÁNG", "Toán", "T1")])
    target = make_week([("Hai", "SÁNG", "Toán", None), ("Hai", "SÁNG", "Tiếng Anh", None)])
    result = run(source, target, selected={"Toán"})
    assert status(result) == {"Toán": "matched"}
    assert set(result.writes) == {"E3", "F3"}


def test_interchangeable_group_renames_subject_cell():
    source = make_week([("Sáu", "SÁNG", "HĐTT", "ATGT", "BGĐT")])
    target = make_week([("Sáu", "SÁNG", "HĐTV/HĐTT", None)])
    result = run(source, target)
    assert result.writes == {"E3": "ATGT", "F3": "BGĐT", "D3": "HĐTT"}
    assert result.subjects[0]["items"][0]["subject_rename"] == {"from": "HĐTV/HĐTT", "to": "HĐTT"}


def test_group_without_rename_when_names_equal():
    source = make_week([("Sáu", "SÁNG", "HĐTV", "Thư viện")])
    target = make_week([("Sáu", "SÁNG", "HĐTV", None)])
    assert "D3" not in run(source, target).writes


def test_long_lesson_warns_but_still_writes():
    source = make_week([("Hai", "SÁNG", "Toán", "x" * 120)])
    target = make_week([("Hai", "SÁNG", "Toán", None)])
    result = run(source, target)
    assert result.writes["E3"] == "x" * 120
    assert [w["code"] for w in result.warnings] == ["CONTENT_TOO_LONG"]
