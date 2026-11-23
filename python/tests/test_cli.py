"""End-to-end tests through the CLI, exactly as Laravel will call it (DETAIL_DESIGN §8.3)."""

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import openpyxl
import pytest

from conftest import FIXTURES

SCRIPT = Path(__file__).resolve().parent.parent / "process_timetable.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def job(tmp_path, source="lbg_mau.xlsx", target="tuan8_lop_dich.xlsx") -> Path:
    shutil.copy(FIXTURES / source, tmp_path / "source.xlsx")
    shutil.copy(FIXTURES / target, tmp_path / "target.xlsx")
    return tmp_path


def request(job_dir, **req):
    req.setdefault("manual_days_off", [])
    (job_dir / "request.json").write_text(json.dumps(req, ensure_ascii=False), encoding="utf-8")


def read(job_dir, name):
    return json.loads((job_dir / name).read_text(encoding="utf-8"))


def cli(command, job_dir, expect=0):
    result = run(command, "--job-dir", str(job_dir))
    assert result.returncode == expect, result.stderr
    assert result.stdout == ""  # stdout is never a result channel
    return result


# --- contract -------------------------------------------------------------------------------------

def test_check_reports_dependencies_and_config():
    result = run("check")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    assert data["slots_per_week"] == 32


def test_job_command_requires_existing_job_dir(tmp_path):
    result = run("analyze", "--job-dir", str(tmp_path / "missing"))
    assert result.returncode == 2
    assert json.loads(result.stderr.splitlines()[-1])["event"] == "job_dir_missing"


def test_business_error_is_written_to_result_file(tmp_path):
    job(tmp_path)
    (tmp_path / "target.xlsx").write_bytes(b"not a zip")
    cli("list-weeks", tmp_path, expect=1)
    assert read(tmp_path, "weeks.json")["error"]["code"] == "INVALID_FILE_TYPE"


def test_target_without_template_sheet_works(tmp_path):
    """MẪU is optional in the target: only week sheets matter."""
    job(tmp_path)
    wb_path = tmp_path / "target.xlsx"
    wb = openpyxl.load_workbook(wb_path)  # throwaway copy; openpyxl save is fine for building test input
    del wb["MẪU"]
    wb.save(wb_path)
    cli("list-weeks", tmp_path)
    weeks = read(tmp_path, "weeks.json")
    assert [w["week_number"] for w in weeks["weeks"] if w["selectable"]] == [8]
    request(tmp_path, weeks=[8], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    cli("generate", tmp_path)
    assert read(tmp_path, "generate.json")["weeks_filled"] == [8]


# --- list-weeks -----------------------------------------------------------------------------------

def test_list_weeks_statuses_and_subjects(tmp_path):
    cli("list-weeks", job(tmp_path))
    data = read(tmp_path, "weeks.json")
    # Only weeks present in the TARGET are listed (the target has TUẦN 8 only; source weeks 1–9 are ignored).
    statuses = {w["week_number"]: w["target_status"] for w in data["weeks"]}
    assert statuses == {8: "ready"}
    assert [w["week_number"] for w in data["weeks"] if w["selectable"]] == [8]
    assert "HĐTV/HĐTT" in data["subjects"] and "HĐTV" not in data["subjects"]
    assert data["days"][0] == {"label": "Hai", "sessions": ["SÁNG", "CHIỀU"]}
    assert [d["label"] for d in data["days"]] == ["Hai", "Ba", "Tư", "Năm", "Sáu"]
    assert set(data["default_selected_subjects"]) == {
        "Tiếng Việt", "Toán", "Khoa học", "Đạo đức", "HĐTN", "HĐTN (SHDC)", "HĐTN (SHL)", "GDTC chung"}


def test_target_week_missing_in_source_is_reported(tmp_path):
    job(tmp_path)
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")  # test input: add a TUẦN 12 sheet
    wb.copy_worksheet(wb["TUẦN 8"]).title = "TUẦN 12"
    wb.save(tmp_path / "target.xlsx")
    cli("list-weeks", tmp_path)
    weeks = {w["week_number"]: w for w in read(tmp_path, "weeks.json")["weeks"]}
    assert sorted(weeks) == [8, 12]
    assert weeks[8]["selectable"] is True
    assert weeks[12]["selectable"] is False
    assert weeks[12]["errors"][0]["code"] == "SOURCE_WEEK_SHEET_MISSING"


def test_single_template_sheet_is_the_week(tmp_path):
    """A one-week file made from the template keeps the sheet name MẪU; its week comes from A1."""
    job(tmp_path, target="mau_lbg_moi.xlsx")  # only the MẪU sheet, A1 = "TUẦN 01 (…)"
    cli("list-weeks", tmp_path)
    weeks = read(tmp_path, "weeks.json")["weeks"]
    assert [(w["week_number"], w["target_sheet"], w["selectable"]) for w in weeks] == [(1, "MẪU", True)]
    request(tmp_path, weeks=[1], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    cli("generate", tmp_path)
    out = openpyxl.load_workbook(tmp_path / "result.xlsx")["MẪU"]
    assert out["E7"].value  # first Toán period of the standard layout is filled


@pytest.mark.parametrize("case", ["template_with_other_sheet", "template_without_week_title"])
def test_target_without_week_sheets(tmp_path, case):
    job(tmp_path, target="mau_lbg_moi.xlsx")
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")  # test input only
    if case == "template_with_other_sheet":
        wb.create_sheet("Ghi chú")         # MẪU is not the only sheet any more -> not a week
    else:
        wb["MẪU"]["A1"] = "LỊCH BÁO GIẢNG"  # only sheet, but no "TUẦN n" title
    wb.save(tmp_path / "target.xlsx")
    cli("list-weeks", tmp_path, expect=1)
    assert read(tmp_path, "weeks.json")["error"]["code"] == "NO_TARGET_WEEK_SHEETS"


def _standard_target(tmp_path, sheet_name):
    """Target = the new standard file (header row 3) with MẪU turned into one week sheet."""
    job(tmp_path, target="mau_lbg_moi.xlsx")
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")  # test input only
    wb["MẪU"].title = sheet_name
    wb.save(tmp_path / "target.xlsx")


def test_old_layout_source_into_standard_layout_target(tmp_path):
    _standard_target(tmp_path, "TUẦN 1")
    request(tmp_path, weeks=[1], selected_subjects=["Toán", "Tiếng Việt", "Khoa học"])
    cli("analyze", tmp_path)
    week = read(tmp_path, "analysis.json")["weeks"][0]
    assert week["status"] == "ready", week["errors"]
    assert {s["subject"]: s["status"] for s in week["subjects"]} == {
        "Toán": "matched", "Tiếng Việt": "matched", "Khoa học": "matched"}
    sign = next(c for c in week["header_changes"] if c["field"] == "sign_date")
    assert sign["cell"] == "E36"  # target's own cell (source uses E35)

    cli("generate", tmp_path)
    out = openpyxl.load_workbook(tmp_path / "result.xlsx")["TUẦN 1"]
    src = openpyxl.load_workbook(FIXTURES / "lbg_mau.xlsx")["TUẦN 1"]
    src_toan = [src[f"E{r}"].value for r in range(3, 35) if src[f"D{r}"].value == "Toán"]
    assert [out[f"E{r}"].value for r in (7, 14, 22, 25, 33)] == src_toan  # standard layout rows
    assert "04 tháng 9" in out["E36"].value
    assert out["E3"].value == "Tên bài"  # header row untouched
    with zipfile.ZipFile(tmp_path / "target.xlsx") as a, zipfile.ZipFile(tmp_path / "result.xlsx") as b:
        assert [n for n in a.namelist() if a.read(n) != b.read(n)] == ["xl/worksheets/sheet1.xml"]


def test_week_taken_from_title_when_sheet_name_is_not_a_week(tmp_path):
    _standard_target(tmp_path, "Sheet1")  # one-week file; A1 = "TUẦN 01 (…)"
    cli("list-weeks", tmp_path)
    weeks = read(tmp_path, "weeks.json")["weeks"]
    assert [(w["week_number"], w["target_sheet"], w["selectable"]) for w in weeks] == [(1, "Sheet1", True)]


# --- analyze + generate ---------------------------------------------------------------------------

def full_run(tmp_path, subjects):
    job(tmp_path)
    request(tmp_path, weeks=[8], selected_subjects=subjects)
    cli("analyze", tmp_path)
    cli("generate", tmp_path)
    return read(tmp_path, "analysis.json"), read(tmp_path, "generate.json")


def test_week_8_all_subjects(tmp_path):
    cli("list-weeks", job(tmp_path))
    subjects = read(tmp_path, "weeks.json")["subjects"]
    analysis, gen = full_run(tmp_path, subjects)

    week = analysis["weeks"][0]
    statuses = {s["subject"]: s["status"] for s in week["subjects"]}
    assert statuses.pop("HĐTN (SHDC)") == "skipped_empty_lesson"
    assert set(statuses.values()) == {"matched"}
    assert gen["weeks_filled"] == [8]
    assert [t["code"] for t in gen["manual_todo"]] == ["EMPTY_LESSON"]

    out = openpyxl.load_workbook(tmp_path / "result.xlsx")["TUẦN 8"]
    src = openpyxl.load_workbook(FIXTURES / "lbg_mau.xlsx")["TUẦN 8"]
    # Toán: source rows 7,15,21,25,32 -> target rows 6,13,21,24,32 (target's own timetable)
    for s_row, t_row in zip([7, 15, 21, 25, 32], [6, 13, 21, 24, 32]):
        assert out[f"E{t_row}"].value.strip() == src[f"E{s_row}"].value.strip()
    assert out["D30"].value == "HĐTT"           # group rename (§4.10)
    assert out["A1"].value == src["A1"].value   # header copied verbatim
    assert out["E35"].value == src["E35"].value


def test_week_8_default_subjects_leaves_specialist_subjects_untouched(tmp_path):
    analysis, _ = full_run(tmp_path, ["Tiếng Việt", "Toán", "Khoa học", "Đạo đức", "HĐTN", "HĐTN (SHL)", "GDTC chung"])
    out = openpyxl.load_workbook(tmp_path / "result.xlsx")["TUẦN 8"]
    target = openpyxl.load_workbook(FIXTURES / "tuan8_lop_dich.xlsx")["TUẦN 8"]
    for row in range(3, 35):
        if target[f"D{row}"].value in ("Tiếng Anh", "Tin học ", "Âm nhạc", "Mỹ thuật", "GDTC", "Công nghệ",
                                       "Lịch sử & Địa lí", "HĐTV/HĐTT"):
            assert out[f"E{row}"].value == target[f"E{row}"].value
            assert out[f"D{row}"].value == target[f"D{row}"].value


def test_only_patched_sheet_changes_and_styles_kept(tmp_path):
    full_run(tmp_path, ["Toán"])
    with zipfile.ZipFile(tmp_path / "target.xlsx") as a, zipfile.ZipFile(tmp_path / "result.xlsx") as b:
        assert a.namelist() == b.namelist()
        changed = [n for n in a.namelist() if a.read(n) != b.read(n)]
    assert changed == ["xl/worksheets/sheet2.xml"]  # TUẦN 8 only


def test_inputs_are_never_modified(tmp_path):
    full_run(tmp_path, ["Toán"])
    assert (tmp_path / "source.xlsx").read_bytes() == (FIXTURES / "lbg_mau.xlsx").read_bytes()
    assert (tmp_path / "target.xlsx").read_bytes() == (FIXTURES / "tuan8_lop_dich.xlsx").read_bytes()


def test_result_used_as_next_target_reports_has_data(tmp_path):
    full_run(tmp_path, ["Toán"])
    shutil.copy(tmp_path / "result.xlsx", tmp_path / "target.xlsx")
    cli("list-weeks", tmp_path)
    week8 = next(w for w in read(tmp_path, "weeks.json")["weeks"] if w["week_number"] == 8)
    assert week8["target_status"] == "has_data"
    assert week8["errors"][0]["code"] == "TARGET_WEEK_HAS_DATA"


def test_day_off_week_7_against_target_timetable(tmp_path):
    """Source TUẦN 7 (Thursday off) into a target sheet with the target class timetable."""
    job(tmp_path)
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")
    wb["TUẦN 8"].title = "TUẦN 7"  # pretend the teacher copied MẪU as TUẦN 7 (same timetable)
    wb.save(tmp_path / "target.xlsx")
    request(tmp_path, weeks=[7], selected_subjects=["Tiếng Việt", "Toán", "Khoa học", "Đạo đức", "HĐTN",
                                                     "HĐTN (SHL)", "GDTC chung"])
    cli("analyze", tmp_path)
    week = read(tmp_path, "analysis.json")["weeks"][0]
    assert {(d["day"], d["session"]) for d in week["days_off"]} == {("Năm", "SÁNG"), ("Năm", "CHIỀU")}
    statuses = {s["subject"]: s["status"] for s in week["subjects"]}
    assert statuses == {"Tiếng Việt": "skipped_day_off", "Toán": "skipped_day_off", "HĐTN": "skipped_day_off",
                        "Khoa học": "matched", "Đạo đức": "matched", "HĐTN (SHL)": "matched",
                        "GDTC chung": "matched"}


def test_blocked_weeks_are_reported_not_generated(tmp_path):
    job(tmp_path)
    request(tmp_path, weeks=[3, 8], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    weeks = {w["week_number"]: w for w in read(tmp_path, "analysis.json")["weeks"]}
    assert weeks[3]["status"] == "blocked"
    assert weeks[3]["errors"][0]["code"] == "TARGET_WEEK_SHEET_MISSING"
    cli("generate", tmp_path)
    gen = read(tmp_path, "generate.json")
    assert gen["weeks_filled"] == [8]
    assert any(t["code"] == "TARGET_WEEK_SHEET_MISSING" for t in gen["manual_todo"])


@pytest.mark.parametrize("change", ["request", "target"])
def test_generate_refuses_outdated_analysis(tmp_path, change):
    job(tmp_path)
    request(tmp_path, weeks=[8], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    if change == "request":
        request(tmp_path, weeks=[8], selected_subjects=["Toán", "Tiếng Việt"])
    else:
        with open(tmp_path / "target.xlsx", "ab") as f:
            f.write(b"\0")
    cli("generate", tmp_path, expect=1)
    assert read(tmp_path, "generate.json")["error"]["code"] == "ANALYSIS_OUTDATED"
    assert not (tmp_path / "result.xlsx").exists()


def test_nothing_to_generate(tmp_path):
    job(tmp_path)
    request(tmp_path, weeks=[3], selected_subjects=["Toán"])  # week 3 has no sheet in the target
    cli("analyze", tmp_path)
    assert read(tmp_path, "analysis.json")["can_generate"] is False
    cli("generate", tmp_path, expect=1)
    assert read(tmp_path, "generate.json")["error"]["code"] == "NOTHING_TO_GENERATE"


def _target_with_week_7_copied_from_week_8(tmp_path):
    """Teacher copied the target's TUẦN 8 sheet as TUẦN 7 but did not fix its title/dates."""
    job(tmp_path)
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")  # throwaway copy; openpyxl save is fine for test input
    wb["TUẦN 8"].title = "TUẦN 7"
    wb.save(tmp_path / "target.xlsx")


def test_title_and_dates_follow_source_and_are_previewed(tmp_path):
    _target_with_week_7_copied_from_week_8(tmp_path)
    request(tmp_path, weeks=[7], selected_subjects=["Khoa học"])
    cli("analyze", tmp_path)
    changes = {c["cell"]: c for c in read(tmp_path, "analysis.json")["weeks"][0]["header_changes"]}
    assert changes["A1"]["label"] == "Tiêu đề tuần"
    assert changes["A1"]["from"].strip().startswith("TUẦN 08")
    assert changes["A1"]["to"].strip() == "TUẦN 07 (Từ 19/10/2026 đến 23/10/2026)"
    assert (changes["A3"]["label"], changes["A3"]["from"], changes["A3"]["to"]) == ("Thứ Hai", "Hai (26/10)", "Hai (19/10)")
    assert changes["E35"]["from"] is None and "16 tháng 10" in changes["E35"]["to"]

    cli("generate", tmp_path)
    ws = openpyxl.load_workbook(tmp_path / "result.xlsx")["TUẦN 7"]
    assert ws["A1"].value.strip().startswith("TUẦN 07") and ws["A29"].value == "Sáu (23/10)"


def test_title_and_dates_fixed_even_when_no_subject_is_filled(tmp_path):
    _target_with_week_7_copied_from_week_8(tmp_path)
    # Thursday of week 7 is a day off: Toán is skipped, nothing else selected
    request(tmp_path, weeks=[7], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    analysis = read(tmp_path, "analysis.json")
    week = analysis["weeks"][0]
    assert [s["status"] for s in week["subjects"]] == ["skipped_day_off"]
    assert analysis["can_generate"] is True
    assert set(week["writes"]) == {c["cell"] for c in week["header_changes"]}

    cli("generate", tmp_path)
    ws = openpyxl.load_workbook(tmp_path / "result.xlsx")["TUẦN 7"]
    assert ws["A1"].value.strip().startswith("TUẦN 07")
    assert ws["E7"].value is None  # no lesson written


def test_no_header_change_when_target_already_matches(tmp_path):
    job(tmp_path, target="lbg_mau.xlsx")
    wb = openpyxl.load_workbook(tmp_path / "target.xlsx")  # test input: empty the lessons of TUẦN 8
    for row in range(3, 35):
        wb["TUẦN 8"][f"E{row}"] = None
    wb.save(tmp_path / "target.xlsx")
    request(tmp_path, weeks=[8], selected_subjects=["Toán"])
    cli("analyze", tmp_path)
    assert read(tmp_path, "analysis.json")["weeks"][0]["header_changes"] == []


def test_invalid_request(tmp_path):
    job(tmp_path)
    request(tmp_path, weeks=[], selected_subjects=["Toán"])
    cli("analyze", tmp_path, expect=1)
    assert read(tmp_path, "analysis.json")["error"]["code"] == "INVALID_REQUEST"
