"""Structure, target-status and source-date checks (DETAIL_DESIGN §4.5, §4.11, §8.2)."""

from __future__ import annotations

import re
from datetime import date

from openpyxl.worksheet.worksheet import Worksheet

from .errors import issue
from .normalization import clean_text
from .timetable_parser import WeekSheet

_EXTRA_DAY_OFF_MERGE = re.compile(r"E\d+:F\d+")

_TITLE = re.compile(
    r"TU[ẦA]N\s*0*(\d{1,2})\s*\(\s*Từ\s+(\d{1,2})/(\d{1,2})/(\d{4})\s+đến\s+(\d{1,2})/(\d{1,2})/(\d{4})\s*\)",
    re.IGNORECASE,
)
_DAY = re.compile(r"\(\s*(\d{1,2})/(\d{1,2})\s*\)")
_SIGN = re.compile(r"Ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.IGNORECASE)


def structure_problems(ws: Worksheet, profile: dict, *, allow_day_off_merges: bool) -> list[str]:
    """Human-readable mismatches against the profile; empty list = structure OK.

    Source sheets may add merges inside columns E:F to mark a day off (lbg_mau TUẦN 7: E23:F28).
    Target sheets must match the template exactly, otherwise lesson cells could be hidden by a merge.
    """
    problems = []
    for anchor in profile["structure_anchors"]:
        if clean_text(ws[anchor["cell"]].value) != anchor["value"]:
            problems.append(f"ô {anchor['cell']} phải là “{anchor['value']}”")

    expected = set(profile["expected_merged_ranges"])
    merged = {str(r) for r in ws.merged_cells.ranges}
    for missing in sorted(expected - merged):
        problems.append(f"thiếu vùng gộp ô {missing}")
    for extra in sorted(merged - expected):
        if not (allow_day_off_merges and _EXTRA_DAY_OFF_MERGE.fullmatch(extra)):
            problems.append(f"có vùng gộp ô lạ {extra}")
    return problems


def target_status(sheet: WeekSheet) -> str:
    """'has_data' if any lesson cell already has content, else 'ready' (structure checked separately)."""
    return "has_data" if any(slot.has_lesson for slot in sheet.slots) else "ready"


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def source_date_issues(sheet: WeekSheet, week_no: int, profile: dict) -> list[dict]:
    """Validate title/day/sign-date text before it is copied verbatim to the target (§4.11)."""
    issues = []

    def bad(cell: str, reason: str):
        issues.append(issue("INVALID_SOURCE_DATE",
                            f"Không đọc được ngày tháng ở ô {cell} của {sheet.name} trong file nguồn: {reason}.",
                            week=week_no, cell=cell))

    title_cell = profile["cells"]["week_title"]
    match = _TITLE.search(sheet.header.get(title_cell) or "")
    if not match:
        bad(title_cell, "tiêu đề tuần không đúng mẫu “TUẦN n (Từ dd/mm/yyyy đến dd/mm/yyyy)”")
        return issues

    title_week = int(match.group(1))
    start = _safe_date(int(match.group(4)), int(match.group(3)), int(match.group(2)))
    end = _safe_date(int(match.group(7)), int(match.group(6)), int(match.group(5)))
    if title_week != week_no:
        bad(title_cell, f"tiêu đề ghi tuần {title_week} nhưng tên sheet là tuần {week_no}")
    if not start or not end or start > end:
        bad(title_cell, "khoảng ngày không hợp lệ")
        return issues

    for day in profile["days"]:
        cell = day["date_cell"]
        text = sheet.header.get(cell) or ""
        found = _DAY.search(text)
        if not clean_text(text).startswith(day["label"]) or not found:
            bad(cell, f"phải có dạng “{day['label']} (dd/mm)”")
            continue
        d, m = int(found.group(1)), int(found.group(2))
        candidates = {_safe_date(start.year, m, d), _safe_date(end.year, m, d)} - {None}
        if not any(start <= c <= end for c in candidates):
            bad(cell, f"ngày {d:02d}/{m:02d} nằm ngoài khoảng của tuần")

    sign_cell = profile["cells"]["sign_date"]
    sign_text = sheet.header.get(sign_cell)
    if sign_text:  # optional: some files leave the signing line empty
        sign = _SIGN.search(sign_text)
        if not sign or not _safe_date(int(sign.group(3)), int(sign.group(2)), int(sign.group(1))):
            bad(sign_cell, "ngày ký phải có dạng “Ngày d tháng m năm yyyy”")
    return issues
