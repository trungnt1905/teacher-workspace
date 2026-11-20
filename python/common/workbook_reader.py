"""Open uploaded workbooks safely and locate week sheets (read-only; DETAIL_DESIGN §8.1).

openpyxl automatically parses with defusedxml when it is installed (requirements.txt).
"""

from __future__ import annotations

import zipfile
from collections import defaultdict
from pathlib import Path

import openpyxl
from openpyxl.workbook.workbook import Workbook

from .errors import EngineError
from .normalization import week_number

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


def week_sheets(wb: Workbook, profile: dict) -> dict[int, list[str]]:
    """week number -> sheet names (more than one name means duplicates)."""
    found: dict[int, list[str]] = defaultdict(list)
    for name in wb.sheetnames:
        number = week_number(name, profile["week_sheet_pattern"])
        if number is not None:
            found[number].append(name)
    return dict(sorted(found.items()))
