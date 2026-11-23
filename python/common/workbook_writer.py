"""Write cell values by patching sheet XML inside the .xlsx package (DETAIL_DESIGN §5.3).

Never use openpyxl to save: it rewrites merged-cell styles and row heights in every sheet.
Here every package part except the patched sheet XML is copied byte-for-byte, and inside the
patched sheets only the value of whitelisted <c> elements changes (style attribute `s` is kept).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path, PurePosixPath

import openpyxl
from lxml import etree

from .errors import EngineError

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
WORKBOOK_PART, APP_PART = "xl/workbook.xml", "docProps/app.xml"
_BAD_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")
NS = {"m": NS_MAIN}
M = f"{{{NS_MAIN}}}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

# Untrusted input: no entity expansion, no network, no huge trees.
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False, remove_blank_text=False)

_CELL_REF = re.compile(r"^([A-Z]+)(\d+)$")


def _parse(data: bytes):
    return etree.fromstring(data, _PARSER)


def sheet_parts(z: zipfile.ZipFile) -> dict[str, str]:
    """Sheet name -> part path inside the package (e.g. 'xl/worksheets/sheet2.xml')."""
    workbook = _parse(z.read("xl/workbook.xml"))
    rels = _parse(z.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels}
    parts = {}
    for sheet in workbook.iterfind("m:sheets/m:sheet", NS):
        target = targets[sheet.get(f"{{{NS_REL}}}id")]
        path = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("xl") / target)
        parts[sheet.get("name")] = path
    return parts


def _find_cell(root, ref: str):
    row_no = _CELL_REF.match(ref).group(2)
    row = root.find(f"m:sheetData/m:row[@r='{row_no}']", NS)
    return None if row is None else row.find(f"m:c[@r='{ref}']", NS)


def _set_value(cell, value: str | None) -> None:
    for child in list(cell):
        if child.tag in (M + "v", M + "is"):
            cell.remove(child)
    if value is None:
        cell.attrib.pop("t", None)
        return
    cell.set("t", "inlineStr")
    inline = etree.SubElement(cell, M + "is")
    text = etree.SubElement(inline, M + "t")
    text.text = value
    text.set(XML_SPACE, "preserve")


def _patch_sheet(data: bytes, edits: dict[str, str | None], sheet_name: str) -> bytes:
    root = _parse(data)
    for ref, value in edits.items():
        cell = _find_cell(root, ref)
        if cell is None:
            raise EngineError("INVALID_SHEET_STRUCTURE",
                              f"Sheet {sheet_name} trong file đích thiếu ô {ref} (sheet phải được copy từ MẪU).",
                              sheet=sheet_name, cell=ref)
        if cell.find(M + "f") is not None:
            raise EngineError("INVALID_SHEET_STRUCTURE",
                              f"Ô {ref} của sheet {sheet_name} đang chứa công thức, hệ thống không ghi đè.",
                              sheet=sheet_name, cell=ref)
        _set_value(cell, value)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _quoted(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def _rename_in_workbook(data: bytes, renames: dict[str, str]) -> bytes:
    """Rename <sheet name=…> and fix sheet references in defined names (print area/titles…)."""
    root = _parse(data)
    for sheet in root.iterfind("m:sheets/m:sheet", NS):
        if sheet.get("name") in renames:
            sheet.set("name", renames[sheet.get("name")])
    for dn in root.iterfind("m:definedNames/m:definedName", NS):
        text = dn.text or ""
        for old, new in renames.items():
            text = text.replace(_quoted(old) + "!", _quoted(new) + "!")
            text = re.sub(r"(^|[=,(\s])" + re.escape(old) + "!", lambda m: m.group(1) + _quoted(new) + "!", text)
        dn.text = text
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rename_in_app_props(data: bytes, renames: dict[str, str]) -> bytes:
    """Sheet titles listed in docProps/app.xml (TitlesOfParts)."""
    root = _parse(data)
    for item in root.iter(f"{{{NS_VT}}}lpstr"):
        if item.text in renames:
            item.text = renames[item.text]
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def write_workbook(src: Path, dst: Path, edits_by_sheet: dict[str, dict[str, str | None]],
                   allowed_by_sheet: dict[str, set[str]], renames: dict[str, str] | None = None) -> None:
    """Copy src to dst, applying value edits to the named sheets. src is never modified.

    allowed_by_sheet: whitelist per sheet, from that sheet's Layout.allowed_cells() (CLAUDE.md rule 8).
    renames: old sheet name -> new tab name (only for a one-sheet target that received week n, §4.1).
    Edits are keyed by the ORIGINAL sheet names.
    """
    renames = renames or {}
    for sheet, edits in edits_by_sheet.items():
        outside = sorted(set(edits) - allowed_by_sheet.get(sheet, set()))
        if outside:
            raise ValueError(f"Refusing to write non-whitelisted cells on {sheet}: {outside}")

    with zipfile.ZipFile(src) as zin:
        parts = sheet_parts(zin)
        missing = [s for s in [*edits_by_sheet, *renames] if s not in parts]
        if missing:
            raise EngineError("TARGET_WEEK_SHEET_MISSING", f"File đích không có sheet {', '.join(missing)}.",
                              sheets=missing)
        for old, new in renames.items():
            if not new or len(new) > 31 or _BAD_SHEET_CHARS.search(new) or (new in parts and new != old):
                raise ValueError(f"Invalid new sheet name {new!r} for {old!r}")
        by_part = {parts[s]: (s, e) for s, e in edits_by_sheet.items() if e}

        with zipfile.ZipFile(dst, "w") as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename in by_part:
                    sheet, edits = by_part[info.filename]
                    data = _patch_sheet(data, edits, sheet)
                elif renames and info.filename == WORKBOOK_PART:
                    data = _rename_in_workbook(data, renames)
                elif renames and info.filename == APP_PART:
                    data = _rename_in_app_props(data, renames)
                zout.writestr(info, data)


def verify_written(src: Path, dst: Path, edits_by_sheet: dict[str, dict[str, str | None]],
                   renames: dict[str, str] | None = None) -> None:
    """Post-write self-check (§5.4). Raises AssertionError-like EngineError on any deviation."""
    renames = renames or {}

    def fail(reason: str):
        raise EngineError("OUTPUT_VERIFY_FAILED", "File kết quả không vượt qua bước tự kiểm tra.", reason=reason)

    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if a.namelist() != b.namelist():
            fail("package parts differ")
        patched = {sheet_parts(a)[s] for s, e in edits_by_sheet.items() if e}
        renamed_parts = {WORKBOOK_PART, APP_PART} if renames else set()
        for name in a.namelist():
            if name in renamed_parts:
                continue
            if name not in patched and a.read(name) != b.read(name):
                fail(f"unexpected change in {name}")
        for part in patched:
            before, after = _parse(a.read(part)), _parse(b.read(part))
            styles_before = {c.get("r"): c.get("s") for c in before.iter(M + "c")}
            styles_after = {c.get("r"): c.get("s") for c in after.iter(M + "c")}
            if styles_before != styles_after:
                fail(f"cell set or styles changed in {part}")

    wb = openpyxl.load_workbook(dst)
    expected_names = [renames.get(n, n) for n in openpyxl.load_workbook(src, read_only=True).sheetnames]
    if wb.sheetnames != expected_names:
        fail(f"sheet names {wb.sheetnames} != {expected_names}")
    for sheet, edits in edits_by_sheet.items():
        ws = wb[renames.get(sheet, sheet)]
        for ref, value in edits.items():
            if ws[ref].value != value:
                fail(f"{sheet}!{ref} reads back {ws[ref].value!r}")
