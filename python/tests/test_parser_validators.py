import openpyxl
import pytest

from common.day_off_detector import detect_off_sessions
from common.layout import resolve_layout
from common.timetable_parser import parse_week_sheet
from common.validators import source_date_issues, target_status
from conftest import FIXTURES
from helpers import CONFIG, KEYWORDS, NORMALIZER

PROFILE = CONFIG.profile


@pytest.fixture(scope="module")
def source_wb():
    return openpyxl.load_workbook(FIXTURES / "lbg_mau.xlsx")       # old layout (header row 2)


@pytest.fixture(scope="module")
def target_wb():
    return openpyxl.load_workbook(FIXTURES / "tuan8_lop_dich.xlsx")  # old layout, other timetable


@pytest.fixture(scope="module")
def new_wb():
    return openpyxl.load_workbook(FIXTURES / "mau_lbg_moi.xlsx")    # standard layout (header row 3)


def parse(ws, strict=False):
    layout, problems = resolve_layout(ws, PROFILE, strict_merges=strict)
    assert layout is not None, problems
    return parse_week_sheet(ws, layout, NORMALIZER)


# --- layout -------------------------------------------------------------------------------------

def test_standard_file_uses_fixed_coordinates(new_wb):
    layout, problems = resolve_layout(new_wb["MẪU"], PROFILE, strict_merges=True)
    assert problems == []
    assert layout.detected_by == "profile"
    assert layout.header_row == 3 and layout.slot_rows == list(range(4, 36))
    assert layout.header_cells()["title"] == "A1"
    assert layout.header_cells()["day:Hai"] == "A4" and layout.header_cells()["day:Sáu"] == "A30"
    assert layout.sign_date == "E36"


@pytest.mark.parametrize("fixture, sheet", [("lbg_mau.xlsx", "TUẦN 1"), ("lbg_mau.xlsx", "MẪU"), ("tuan8_lop_dich.xlsx", "TUẦN 8")])
def test_older_files_are_found_by_content(fixture, sheet):
    ws = openpyxl.load_workbook(FIXTURES / fixture)[sheet]
    layout, problems = resolve_layout(ws, PROFILE, strict_merges=True)
    assert problems == []
    assert layout.detected_by == "content"
    assert layout.header_row == 2 and layout.slot_rows == list(range(3, 35))
    assert [d.date_cell for d in layout.days] == ["A3", "A10", "A17", "A23", "A29"]
    assert layout.days[2].sessions == {"SÁNG": (17, 20), "CHIỀU": (21, 22)}
    assert layout.columns == {"day": "A", "session": "B", "period": "C", "subject": "D", "lesson": "E", "equipment": "F"}
    assert layout.sign_date == "E35"
    assert layout.header_cells()["title"] == "A1"  # always the fixed title cell


def test_day_off_merge_is_fine_in_source_but_blocks_a_target(source_wb):
    # TUẦN 7 marks Thursday off with a merged E23:F28.
    assert resolve_layout(source_wb["TUẦN 7"], PROFILE, strict_merges=False)[1] == []
    layout, problems = resolve_layout(source_wb["TUẦN 7"], PROFILE, strict_merges=True)
    assert layout is None and problems == ["có vùng gộp ô E23:F28 che các ô tên bài/đồ dùng"]


def test_sheet_without_table_reports_why(new_wb):
    ws = new_wb.copy_worksheet(new_wb["MẪU"])  # in-memory only, never saved
    ws["E3"] = "Nội dung"                      # no "Tên bài" header anywhere
    layout, problems = resolve_layout(ws, PROFILE, strict_merges=True)
    assert layout is None
    assert "không tìm thấy hàng tiêu đề cột" in problems[0]


def test_missing_day_is_reported(new_wb):
    ws = new_wb.copy_worksheet(new_wb["MẪU"])  # in-memory only
    ws["A18"] = "Thứ tư (09/09)"               # day label no longer recognisable
    layout, problems = resolve_layout(ws, PROFILE, strict_merges=True)
    assert layout is None and "thứ Tư" in problems[0]


# --- parsing ------------------------------------------------------------------------------------

def test_parse_source_week_8(source_wb):
    sheet = parse(source_wb["TUẦN 8"])
    assert len(sheet.slots) == 32
    toan = sheet.by_subject()["Toán"]
    assert [s.row for s in toan] == [7, 15, 21, 25, 32]
    assert toan[0].lesson.startswith("TH và TN")
    assert sheet.by_subject()["HĐTV/HĐTT"][0].subject_raw == "HĐTT"
    assert sheet.header["title"].strip().startswith("TUẦN 08")
    assert sheet.header_cell["title"] == "A1" and sheet.header_cell["day:Hai"] == "A3"


def test_parse_target_uses_its_own_timetable(target_wb):
    sheet = parse(target_wb["TUẦN 8"], strict=True)
    assert [s.row for s in sheet.by_subject()["Toán"]] == [6, 13, 21, 24, 32]
    assert sheet.by_subject()["HĐTV/HĐTT"][0].subject_raw == "HĐTV/HĐTT"
    assert target_status(sheet) == "ready"


def test_parse_standard_layout(new_wb):
    sheet = parse(new_wb["MẪU"], strict=True)
    assert [s.row for s in sheet.by_subject()["Toán"]] == [7, 14, 22, 25, 33]
    assert sheet.header_cell["day:Hai"] == "A4" and sheet.header_cell["sign_date"] == "E36"
    assert target_status(sheet) == "ready"


def test_source_with_lessons_counts_as_has_data(source_wb):
    assert target_status(parse(source_wb["TUẦN 8"])) == "has_data"


# --- source dates -------------------------------------------------------------------------------

@pytest.mark.parametrize("week", range(1, 10))
def test_source_dates_valid_for_all_sample_weeks(source_wb, week):
    assert source_date_issues(parse(source_wb[f"TUẦN {week}"]), week) == []


def test_source_dates_detect_wrong_week_and_out_of_range(source_wb):
    sheet = parse(source_wb["TUẦN 8"])
    assert [i["details"]["cell"] for i in source_date_issues(sheet, 9)] == ["A1"]
    sheet.header["day:Tư"] = "Tư (15/12)"
    assert [i["details"]["cell"] for i in source_date_issues(sheet, 8)] == ["A17"]


# --- days off -----------------------------------------------------------------------------------

def test_day_off_detected_from_empty_merged_day(source_wb):
    off = detect_off_sessions(parse(source_wb["TUẦN 7"]), KEYWORDS)
    assert {(o.day, o.session) for o in off} == {("Năm", "SÁNG"), ("Năm", "CHIỀU")}


def test_single_empty_lesson_is_not_a_day_off(source_wb):
    # HĐTN (SHDC) is always empty, but Monday morning has other lessons.
    assert detect_off_sessions(parse(source_wb["TUẦN 8"]), KEYWORDS) == []


def test_manual_override(source_wb):
    off = detect_off_sessions(parse(source_wb["TUẦN 7"]), KEYWORDS, [
        {"day": "Năm", "session": "CHIỀU", "is_day_off": False},
        {"day": "Hai", "is_day_off": True},
    ])
    assert {(o.day, o.session, o.detected_by) for o in off} == {
        ("Năm", "SÁNG", "auto"), ("Hai", "SÁNG", "manual"), ("Hai", "CHIỀU", "manual")}
