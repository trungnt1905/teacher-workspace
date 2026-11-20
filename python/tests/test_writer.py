import shutil
import subprocess
import zipfile

import openpyxl
import pytest

from common.errors import EngineError
from common.workbook_writer import allowed_cells, verify_written, write_workbook
from conftest import FIXTURES
from helpers import CONFIG

PROFILE = CONFIG.profile
TARGET = FIXTURES / "tuan8_lop_dich.xlsx"


def test_writes_values_and_clears_cells(tmp_path):
    out = tmp_path / "out.xlsx"
    edits = {"TUẦN 8": {"E4": "Bài mới", "F4": None, "E5": "  giữ dấu cách  \nxuống dòng"}}
    write_workbook(TARGET, out, edits, PROFILE)
    verify_written(TARGET, out, edits)
    ws = openpyxl.load_workbook(out)["TUẦN 8"]
    assert ws["E4"].value == "Bài mới"
    assert ws["F4"].value is None
    assert ws["E5"].value == "  giữ dấu cách  \nxuống dòng"


def test_refuses_cells_outside_whitelist(tmp_path):
    assert "C3" not in allowed_cells(PROFILE) and "A2" not in allowed_cells(PROFILE)
    with pytest.raises(ValueError):
        write_workbook(TARGET, tmp_path / "out.xlsx", {"TUẦN 8": {"C3": "9"}}, PROFILE)


def test_missing_sheet(tmp_path):
    with pytest.raises(EngineError) as exc:
        write_workbook(TARGET, tmp_path / "out.xlsx", {"TUẦN 99": {"E4": "x"}}, PROFILE)
    assert exc.value.code == "TARGET_WEEK_SHEET_MISSING"


def _rewrite_sheet_xml(src, dst, part, transform):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            zout.writestr(info, transform(data) if info.filename == part else data)


def test_refuses_missing_cell_and_formula_cell(tmp_path):
    no_cell = tmp_path / "no_cell.xlsx"
    _rewrite_sheet_xml(TARGET, no_cell, "xl/worksheets/sheet2.xml",
                       lambda d: d.replace(b'<c r="E4" s=', b'<c r="Z4" s='))
    with pytest.raises(EngineError, match="thiếu ô E4"):
        write_workbook(no_cell, tmp_path / "o1.xlsx", {"TUẦN 8": {"E4": "x"}}, PROFILE)

    formula = tmp_path / "formula.xlsx"
    with zipfile.ZipFile(TARGET) as z:
        xml = z.read("xl/worksheets/sheet2.xml")
    start = xml.index(b'<c r="E4"')
    end = xml.index(b">", start)
    tag = xml[start:end + 1]
    replacement = tag[:-2] + b"><f>1+1</f></c>" if tag.endswith(b"/>") else tag + b"<f>1+1</f>"
    _rewrite_sheet_xml(TARGET, formula, "xl/worksheets/sheet2.xml", lambda d: d.replace(tag, replacement, 1))
    with pytest.raises(EngineError, match="công thức"):
        write_workbook(formula, tmp_path / "o2.xlsx", {"TUẦN 8": {"E4": "x"}}, PROFILE)


def test_verify_detects_tampering(tmp_path):
    out = tmp_path / "out.xlsx"
    edits = {"TUẦN 8": {"E4": "A"}}
    write_workbook(TARGET, out, edits, PROFILE)
    tampered = tmp_path / "tampered.xlsx"
    _rewrite_sheet_xml(out, tampered, "xl/styles.xml", lambda d: d + b" ")
    with pytest.raises(EngineError) as exc:
        verify_written(TARGET, tampered, edits)
    assert exc.value.code == "OUTPUT_VERIFY_FAILED"


def _render_pages(xlsx, workdir):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(workdir), str(xlsx)],
                   check=True, capture_output=True, timeout=180)
    pdf = workdir / (xlsx.stem + ".pdf")
    pages = []
    for page in (1, 2):  # sheet MẪU
        pages.append(subprocess.run(["pdftoppm", "-r", "50", "-gray", "-f", str(page), "-l", str(page), str(pdf)],
                                    check=True, capture_output=True).stdout)
    return pages


@pytest.mark.skipif(shutil.which("soffice") is None or shutil.which("pdftoppm") is None,
                    reason="LibreOffice/poppler not installed")
def test_untouched_sheet_renders_pixel_identical(tmp_path):
    out = tmp_path / "result.xlsx"
    edits = {"TUẦN 8": {"E4": "Bài thử", "F4": None}}
    write_workbook(TARGET, out, edits, PROFILE)
    original = tmp_path / "original.xlsx"
    shutil.copy(TARGET, original)
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert _render_pages(original, tmp_path / "a") == _render_pages(out, tmp_path / "b")
