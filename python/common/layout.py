"""Where things are on a week sheet (DETAIL_DESIGN §8.2).

1. Try the fixed coordinates of template_profile.json (the current standard file, MAU_LBG.xlsx).
2. If the sheet does not match them (older file, rows shifted…), find the table by its content:
   the header row ("Thứ / Môn / Tên bài…"), day blocks (Hai…Sáu in the "Thứ" column, using merged
   cells), sessions (SÁNG/CHIỀU in the "Buổi" column) and the signing-date cell right below the table.
The week title is always the fixed cell of the profile (A1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .normalization import clean_text

# Header labels -> logical column (compared case-insensitively, prefix match for "Đồ dùng…").
HEADER_LABELS = {
    "day": ("thứ",),
    "session": ("buổi",),
    "period": ("tiết",),
    "subject": ("môn",),
    "lesson": ("tên bài",),
    "equipment": ("đồ dùng",),
}
REQUIRED_COLUMNS = ("day", "subject", "lesson", "equipment")
MAX_HEADER_ROW = 20
MAX_TABLE_ROWS = 80


@dataclass(frozen=True)
class DayBlock:
    label: str
    date_cell: str
    sessions: dict[str, tuple[int, int]]  # session name -> (first row, last row)

    @property
    def rows(self) -> list[int]:
        return [r for first, last in self.sessions.values() for r in range(first, last + 1)]


@dataclass(frozen=True)
class Layout:
    week_title: str
    sign_date: str
    columns: dict[str, str]          # logical column -> letter
    days: list[DayBlock]
    header_row: int
    detected_by: str                 # "profile" | "content"
    notes: list[str] = field(default_factory=list)

    @property
    def slot_rows(self) -> list[int]:
        return [r for d in self.days for r in d.rows]

    def header_cells(self) -> dict[str, str]:
        """Semantic key -> cell: 'title', 'day:Hai'…, 'sign_date'."""
        cells = {"title": self.week_title}
        cells.update({f"day:{d.label}": d.date_cell for d in self.days})
        cells["sign_date"] = self.sign_date
        return cells

    def allowed_cells(self) -> set[str]:
        """Cells the engine may write on this sheet (CLAUDE.md rule 8)."""
        cols = self.columns
        cells = set(self.header_cells().values())
        for r in self.slot_rows:
            cells.update({f"{cols['lesson']}{r}", f"{cols['equipment']}{r}", f"{cols['subject']}{r}"})
        return cells


def _merged_span(ws: Worksheet, column: int, row: int) -> tuple[int, int] | None:
    for rng in ws.merged_cells.ranges:
        if rng.min_col <= column <= rng.max_col and rng.min_row <= row <= rng.max_row:
            return rng.min_row, rng.max_row
    return None


def _starts_with_label(text: str, label: str) -> bool:
    t, lab = clean_text(text).casefold(), label.casefold()
    return t == lab or t.startswith(lab + " ") or t.startswith(lab + "(")


# --- 1. fixed coordinates ------------------------------------------------------------------------

def _profile_layout(profile: dict) -> Layout:
    days = [DayBlock(d["label"], d["date_cell"], {k: tuple(v) for k, v in d["sessions"].items()}) for d in profile["days"]]
    return Layout(profile["cells"]["week_title"], profile["cells"]["sign_date"], dict(profile["columns"]),
                  days, profile["header_row"], "profile")


def _fits_profile(ws: Worksheet, profile: dict) -> bool:
    for anchor in profile["structure_anchors"]:
        if clean_text(ws[anchor["cell"]].value) != anchor["value"]:
            return False
    return all(_starts_with_label(ws[d["date_cell"]].value, d["label"]) for d in profile["days"])


# --- 2. detection by content ---------------------------------------------------------------------

def _find_header(ws: Worksheet) -> tuple[int, dict[str, str]] | None:
    for row in range(1, min(ws.max_row, MAX_HEADER_ROW) + 1):
        found: dict[str, str] = {}
        for col in range(1, min(ws.max_column, 26) + 1):
            text = clean_text(ws.cell(row, col).value).casefold()
            for key, labels in HEADER_LABELS.items():
                if key not in found and any(text == lab or text.startswith(lab) for lab in labels):
                    found[key] = get_column_letter(col)
        if all(k in found for k in REQUIRED_COLUMNS):
            return row, found
    return None


def _detect(ws: Worksheet, profile: dict) -> tuple[Layout | None, list[str]]:
    header = _find_header(ws)
    if header is None:
        return None, ["không tìm thấy hàng tiêu đề cột (Thứ / Môn / Tên bài / Đồ dùng dạy học)"]
    header_row, cols = header
    day_col = ws[f"{cols['day']}1"].column
    subject_col = ws[f"{cols['subject']}1"].column
    labels = [d["label"] for d in profile["days"]]
    last_possible = min(ws.max_row, header_row + MAX_TABLE_ROWS)

    # Day starts: first row of each label in the day column, in order.
    starts: list[tuple[str, int]] = []
    for row in range(header_row + 1, last_possible + 1):
        for lab in labels:
            if _starts_with_label(ws.cell(row, day_col).value, lab):
                starts.append((lab, row))
    found_labels = [lab for lab, _ in starts]
    if found_labels != labels:
        missing = [lab for lab in labels if lab not in found_labels]
        reason = f"không tìm thấy dòng thứ {', '.join(missing)}" if missing else "các thứ không đúng thứ tự Hai → Sáu"
        return None, [f"{reason} ở cột Thứ ({cols['day']})"]

    days: list[DayBlock] = []
    for i, (lab, start) in enumerate(starts):
        span = _merged_span(ws, day_col, start)
        if span:
            end = span[1]
        elif i + 1 < len(starts):
            end = starts[i + 1][1] - 1
        else:  # last day without merge: until the subject column runs out
            end = start
            while end + 1 <= last_possible and clean_text(ws.cell(end + 1, subject_col).value):
                end += 1
        days.append(DayBlock(lab, f"{cols['day']}{start}", _detect_sessions(ws, cols, start, end)))

    last_row = days[-1].rows[-1]
    return Layout(profile["cells"]["week_title"], _detect_sign_cell(ws, cols, last_row), cols, days,
                  header_row, "content"), []


def _detect_sessions(ws: Worksheet, cols: dict, first: int, last: int) -> dict[str, tuple[int, int]]:
    if "session" not in cols:
        return {"CẢ NGÀY": (first, last)}
    col = ws[f"{cols['session']}1"].column
    starts = [(clean_text(ws.cell(r, col).value).upper(), r) for r in range(first, last + 1)
              if clean_text(ws.cell(r, col).value)]
    if not starts:
        return {"CẢ NGÀY": (first, last)}
    if starts[0][1] != first:  # rows before the first session label belong to it
        starts[0] = (starts[0][0], first)
    sessions = {}
    for i, (name, start) in enumerate(starts):
        span = _merged_span(ws, col, start)
        end = min(span[1], last) if span else (starts[i + 1][1] - 1 if i + 1 < len(starts) else last)
        sessions[name] = (start, end)
    return sessions


def _detect_sign_cell(ws: Worksheet, cols: dict, last_row: int) -> str:
    """Signing date ("Ngày … tháng … năm …"): the lesson-column cell just below the table."""
    lesson_col = ws[f"{cols['lesson']}1"].column
    for row in range(last_row + 1, last_row + 4):
        if "ngày" in clean_text(ws.cell(row, lesson_col).value).casefold():
            return f"{cols['lesson']}{row}"
    return f"{cols['lesson']}{last_row + 1}"


# --- public --------------------------------------------------------------------------------------

def resolve_layout(ws: Worksheet, profile: dict, *, strict_merges: bool) -> tuple[Layout | None, list[str]]:
    """Layout of a week sheet, or (None, problems).

    strict_merges (target sheets): a merged range covering lesson/equipment cells of two or more
    periods would hide values we write, so it is a problem. Source sheets may merge E:F to mark a day off.
    """
    if _fits_profile(ws, profile):
        layout = _profile_layout(profile)
    else:
        layout, problems = _detect(ws, profile)
        if layout is None:
            return None, problems

    if strict_merges:
        writable_rows = set(layout.slot_rows)
        lesson_col = ws[f"{layout.columns['lesson']}1"].column
        equipment_col = ws[f"{layout.columns['equipment']}1"].column
        for rng in ws.merged_cells.ranges:
            covers_cols = rng.min_col <= equipment_col and rng.max_col >= lesson_col
            covers_rows = any(rng.min_row <= r <= rng.max_row for r in writable_rows)
            if covers_cols and covers_rows and rng.max_row > rng.min_row:
                return None, [f"có vùng gộp ô {rng} che các ô tên bài/đồ dùng"]
    return layout, []
