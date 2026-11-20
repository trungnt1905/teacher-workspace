import openpyxl
import pytest

from common.day_off_detector import detect_off_sessions
from common.timetable_parser import parse_week_sheet
from common.validators import source_date_issues, structure_problems, target_status
from helpers import CONFIG, KEYWORDS, NORMALIZER

PROFILE = CONFIG.profile


@pytest.fixture(scope="module")
def source_wb(request):
    from conftest import FIXTURES
    return openpyxl.load_workbook(FIXTURES / "lbg_mau.xlsx")


@pytest.fixture(scope="module")
def target_wb():
    from conftest import FIXTURES
    return openpyxl.load_workbook(FIXTURES / "tuan8_lop_dich.xlsx")


def test_parse_source_week_8(source_wb):
    sheet = parse_week_sheet(source_wb["TUẦN 8"], PROFILE, NORMALIZER)
    assert len(sheet.slots) == 32
    toan = sheet.by_subject()["Toán"]
    assert [s.row for s in toan] == [7, 15, 21, 25, 32]
    assert toan[0].lesson.startswith("TH và TN")
    assert sheet.by_subject()["HĐTV/HĐTT"][0].subject_raw == "HĐTT"
    assert sheet.header["A1"].strip().startswith("TUẦN 08")


def test_parse_target_uses_its_own_timetable(target_wb):
    sheet = parse_week_sheet(target_wb["TUẦN 8"], PROFILE, NORMALIZER)
    assert [s.row for s in sheet.by_subject()["Toán"]] == [6, 13, 21, 24, 32]
    assert sheet.by_subject()["HĐTV/HĐTT"][0].subject_raw == "HĐTV/HĐTT"
    assert target_status(sheet) == "ready"


def test_source_with_lessons_counts_as_has_data(source_wb):
    assert target_status(parse_week_sheet(source_wb["TUẦN 8"], PROFILE, NORMALIZER)) == "has_data"


def test_structure_ok_for_real_files(source_wb, target_wb):
    assert structure_problems(target_wb["TUẦN 8"], PROFILE, allow_day_off_merges=False) == []
    # TUẦN 7 marks Thursday off with an extra E23:F28 merge: fine for a source, not for a target.
    assert structure_problems(source_wb["TUẦN 7"], PROFILE, allow_day_off_merges=True) == []
    assert structure_problems(source_wb["TUẦN 7"], PROFILE, allow_day_off_merges=False) == ["có vùng gộp ô lạ E23:F28"]


def test_structure_detects_broken_sheet(target_wb):
    ws = target_wb.copy_worksheet(target_wb["TUẦN 8"])  # in-memory only, never saved
    ws.unmerge_cells("A3:A9")
    ws["D2"] = "Môn học"
    problems = structure_problems(ws, PROFILE, allow_day_off_merges=False)
    assert "thiếu vùng gộp ô A3:A9" in problems
    assert "ô D2 phải là “Môn”" in problems


@pytest.mark.parametrize("week", range(1, 10))
def test_source_dates_valid_for_all_sample_weeks(source_wb, week):
    sheet = parse_week_sheet(source_wb[f"TUẦN {week}"], PROFILE, NORMALIZER)
    assert source_date_issues(sheet, week, PROFILE) == []


def test_source_dates_detect_wrong_week_and_out_of_range(source_wb):
    sheet = parse_week_sheet(source_wb["TUẦN 8"], PROFILE, NORMALIZER)
    assert [i["details"]["cell"] for i in source_date_issues(sheet, 9, PROFILE)] == ["A1"]
    sheet.header["A17"] = "Tư (15/12)"
    assert [i["details"]["cell"] for i in source_date_issues(sheet, 8, PROFILE)] == ["A17"]


def test_day_off_detected_from_empty_merged_day(source_wb):
    sheet = parse_week_sheet(source_wb["TUẦN 7"], PROFILE, NORMALIZER)
    off = detect_off_sessions(sheet, KEYWORDS)
    assert {(o.day, o.session) for o in off} == {("Năm", "SÁNG"), ("Năm", "CHIỀU")}


def test_single_empty_lesson_is_not_a_day_off(source_wb):
    # HĐTN (SHDC) is always empty, but Monday morning has other lessons.
    sheet = parse_week_sheet(source_wb["TUẦN 8"], PROFILE, NORMALIZER)
    assert detect_off_sessions(sheet, KEYWORDS) == []


def test_manual_override(source_wb):
    sheet = parse_week_sheet(source_wb["TUẦN 7"], PROFILE, NORMALIZER)
    off = detect_off_sessions(sheet, KEYWORDS, [
        {"day": "Năm", "session": "CHIỀU", "is_day_off": False},
        {"day": "Hai", "is_day_off": True},
    ])
    assert {(o.day, o.session, o.detected_by) for o in off} == {
        ("Năm", "SÁNG", "auto"), ("Hai", "SÁNG", "manual"), ("Hai", "CHIỀU", "manual")}
