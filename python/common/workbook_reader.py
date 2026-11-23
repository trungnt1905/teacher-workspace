"""Open uploaded workbooks safely and locate week sheets (read-only; DETAIL_DESIGN §8.1).

openpyxl automatically parses with defusedxml when it is installed (requirements.txt).
"""

from __future__ import annotations

import re
import zipfile
from collections import defaultdict
from pathlib import Path

import openpyxl
from openpyxl.workbook.workbook import Workbook

from .errors import EngineError
from .normalization import clean_text, week_number

# Guard against zip bombs before openpyxl inflates anything.
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_PARTS = 2000


def _check_package(path: Path, label: str) -> None:
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            names = {i.filename for i in infos}
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                raise EngineError("INVALID_FILE_TYPE", f"{label} không đúng định dạng .xlsx.", file=label)
            if len(infos) > MAX_PARTS or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
                raise EngineError("WORKBOOK_CORRUPT", f"{label} quá lớn sau khi giải nén.", file=label)
    except zipfile.BadZipFile as exc:
        raise EngineError("INVALID_FILE_TYPE", f"{label} không đúng định dạng .xlsx.", file=label) from exc


def open_workbook(path: Path, label: str) -> Workbook:
    """label: user-facing name, e.g. 'File nguồn' / 'File đích'."""
    _check_package(path, label)
    try:
        return openpyxl.load_workbook(path, data_only=False)
    except EngineError:
        raise
    except Exception as exc:  # noqa: BLE001 — any parse failure means a broken workbook
        raise EngineError("WORKBOOK_CORRUPT", f"Không mở được {label.lower()}, file có thể bị lỗi.", file=label) from exc


_TITLE_WEEK = re.compile(r"^TU[ẦA]N\s*0*(\d{1,2})\b", re.IGNORECASE)


def week_sheets(wb: Workbook, profile: dict) -> dict[int, list[str]]:
    """week number -> sheet names (more than one name means duplicates).

    The week comes from the sheet name ("TUẦN 10"). Since each week may now be its own file, a sheet
    with another name (e.g. "Sheet1") is also accepted when its title cell (A1) starts with "TUẦN n".
    The template sheet (MẪU) is not a week — except when it is the workbook's ONLY sheet: a one-week
    file made straight from the template keeps the name "MẪU", and its week comes from A1.
    """
    found: dict[int, list[str]] = defaultdict(list)
    only_sheet = len(wb.worksheets) == 1
    for ws in wb.worksheets:
        if clean_text(ws.title).casefold() == clean_text(profile["template_sheet"]).casefold() and not only_sheet:
            continue
        number = week_number(ws.title, profile["week_sheet_pattern"])
        if number is None:
            title = _TITLE_WEEK.match(clean_text(ws[profile["cells"]["week_title"]].value))
            number = int(title.group(1)) if title else None
        if number is not None:
            found[number].append(ws.title)
    return dict(sorted(found.items()))
