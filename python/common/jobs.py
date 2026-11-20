"""Job commands run by the CLI: list-weeks, analyze, generate (DETAIL_DESIGN §8.3, §8.4, §8.10).

Job directory layout (§11.1): source.xlsx, target.xlsx, request.json -> weeks.json / analysis.json /
generate.json / result.xlsx. The uploaded files are never modified.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from openpyxl.workbook.workbook import Workbook

from .config import Config, load_config
from .day_off_detector import detect_off_sessions
from .errors import EngineError, issue
from .normalization import SubjectNormalizer
from .timetable_matcher import DEFAULT_LESSON_MAX_CHARS, match_week
from .timetable_parser import WeekSheet, header_cells, parse_week_sheet
from .validators import source_date_issues, structure_problems, target_status
from .workbook_reader import open_workbook, week_sheets
from .workbook_writer import verify_written, write_workbook

SOURCE, TARGET, REQUEST = "source.xlsx", "target.xlsx", "request.json"
ANALYSIS, RESULT = "analysis.json", "result.xlsx"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


@dataclass
class Inputs:
    cfg: Config
    normalizer: SubjectNormalizer
    source: Workbook
    target: Workbook
    source_weeks: dict[int, list[str]]
    target_weeks: dict[int, list[str]]


def _load_inputs(job_dir: Path) -> Inputs:
    cfg = load_config()
    profile = cfg.profile
    source = open_workbook(job_dir / SOURCE, "File nguồn")
    # The target only needs week sheets; MẪU is optional (it is just what the teacher copies from).
    target = open_workbook(job_dir / TARGET, "File đích")
    source_weeks = week_sheets(source, profile)
    if not source_weeks:
        raise EngineError("NO_WEEK_SHEETS", "File nguồn không có sheet tuần nào (tên dạng “TUẦN 1”).")
    return Inputs(cfg, SubjectNormalizer(cfg.subjects), source, target, source_weeks, week_sheets(target, profile))


@dataclass
class WeekInspection:
    week_number: int
    source_sheet: str | None
    target_sheet: str | None
    target_status: str
    errors: list[dict]
    source: WeekSheet | None = None
    target: WeekSheet | None = None

    @property
    def selectable(self) -> bool:
        return not self.errors and self.target_status == "ready"

    def summary(self) -> dict:
        return {
            "week_number": self.week_number,
            "source_sheet": self.source_sheet,
            "target_sheet": self.target_sheet,
            "target_status": self.target_status,
            "selectable": self.selectable,
            "errors": self.errors,
        }


def _inspect_week(no: int, inp: Inputs) -> WeekInspection:
    profile = inp.cfg.profile
    src_names, dst_names = inp.source_weeks.get(no, []), inp.target_weeks.get(no, [])
    errors: list[dict] = []
    src_name = src_names[0] if src_names else None
    dst_name = dst_names[0] if len(dst_names) == 1 else None

    if len(src_names) > 1:
        errors.append(issue("DUPLICATE_WEEK_SHEET", f"File nguồn có nhiều sheet cùng là tuần {no}: {', '.join(src_names)}.",
                            week=no, sheets=src_names))
    if not src_names:
        errors.append(issue("SOURCE_WEEK_SHEET_MISSING", f"File nguồn không có sheet tuần {no}.", week=no))

    if len(dst_names) > 1:
        status = "duplicate"
        errors.append(issue("DUPLICATE_WEEK_SHEET", f"File đích có nhiều sheet cùng là tuần {no}: {', '.join(dst_names)}.",
                            week=no, sheets=dst_names))
    elif not dst_names:
        status = "missing"
        errors.append(issue("TARGET_WEEK_SHEET_MISSING",
                            f"Chưa có sheet tuần {no} trong file đích — hãy tạo sheet tuần (copy sheet {profile['template_sheet']} "
                            f"hoặc một sheet tuần khác).", week=no))
    else:
        problems = structure_problems(inp.target[dst_name], profile, allow_day_off_merges=False)
        if problems:
            status = "invalid_structure"
            errors.append(issue("INVALID_SHEET_STRUCTURE",
                                f"Sheet {dst_name} của file đích không đúng cấu trúc mẫu: {'; '.join(problems)}.",
                                week=no, sheet=dst_name, problems=problems))
        else:
            status = "ready"

    inspection = WeekInspection(no, src_name, dst_name, status, errors)

    if src_name and len(src_names) == 1:
        problems = structure_problems(inp.source[src_name], profile, allow_day_off_merges=True)
        if problems:
            errors.append(issue("INVALID_SHEET_STRUCTURE",
                                f"Sheet {src_name} của file nguồn không đúng cấu trúc mẫu: {'; '.join(problems)}.",
                                week=no, sheet=src_name, problems=problems))
        else:
            inspection.source = parse_week_sheet(inp.source[src_name], profile, inp.normalizer)

    if status == "ready":
        inspection.target = parse_week_sheet(inp.target[dst_name], profile, inp.normalizer)
        if target_status(inspection.target) == "has_data":
            inspection.target_status = "has_data"
            errors.append(issue("TARGET_WEEK_HAS_DATA", f"Sheet {dst_name} đã có dữ liệu, bỏ qua.", week=no, sheet=dst_name))

    return inspection


def _subject_list(inp: Inputs) -> list[str]:
    """Subjects found in source week sheets and the target week sheets (+ MẪU if present), config order first."""
    profile, found = inp.cfg.profile, set()
    sheets = [inp.source[n] for names in inp.source_weeks.values() for n in names]
    sheets += [inp.target[n] for names in inp.target_weeks.values() for n in names]
    if profile["template_sheet"] in inp.target.sheetnames:
        sheets.append(inp.target[profile["template_sheet"]])
    for ws in sheets:
        found.update(s.subject for s in parse_week_sheet(ws, profile, inp.normalizer).slots if s.subject)
    order = dict.fromkeys(inp.normalizer.key(s) for s in inp.cfg.subjects["subjects"])
    known = [s for s in order if s in found]
    return known + sorted(found - set(known))


def list_weeks(job_dir: Path) -> dict:
    inp = _load_inputs(job_dir)
    weeks = [_inspect_week(no, inp).summary() for no in inp.source_weeks]
    subjects = _subject_list(inp)
    excluded = set(inp.cfg.subjects.get("default_excluded_subjects", []))
    return {
        "success": True,
        "weeks": weeks,
        "subjects": subjects,
        "default_selected_subjects": [s for s in subjects if s not in excluded],
        # Day/session labels for the day-off toggles in the UI (no layout hardcoded in the frontend).
        "days": [{"label": d["label"], "sessions": list(d["sessions"])} for d in inp.cfg.profile["days"]],
    }


def _validate_request(request: dict) -> dict:
    weeks = request.get("weeks")
    subjects = request.get("selected_subjects")
    manual = request.get("manual_days_off", [])
    if not isinstance(weeks, list) or not weeks or not all(isinstance(w, int) for w in weeks):
        raise EngineError("INVALID_REQUEST", "Chưa chọn tuần nào để xử lý.")
    if not isinstance(subjects, list) or not subjects or not all(isinstance(s, str) for s in subjects):
        raise EngineError("INVALID_REQUEST", "Chưa chọn môn nào để đồng bộ.")
    if not isinstance(manual, list) or not all(isinstance(m, dict) for m in manual):
        raise EngineError("INVALID_REQUEST", "Danh sách ngày nghỉ chỉnh tay không hợp lệ.")
    return {"weeks": sorted(set(weeks)), "selected_subjects": sorted(set(subjects)), "manual_days_off": manual}


def analyze(job_dir: Path) -> dict:
    request = _validate_request(read_json(job_dir / REQUEST))
    inp = _load_inputs(job_dir)
    profile, subj_cfg = inp.cfg.profile, inp.cfg.subjects
    keywords = subj_cfg.get("day_off_keywords", ["nghỉ"])
    selected = set(request["selected_subjects"])
    max_chars = profile.get("lesson_max_chars", DEFAULT_LESSON_MAX_CHARS)

    weeks = []
    for no in request["weeks"]:
        ins = _inspect_week(no, inp)
        week = {**ins.summary(), "status": "blocked", "days_off": [], "subjects": [], "warnings": [], "writes": {}}
        weeks.append(week)
        if not ins.selectable or ins.source is None:
            continue

        date_errors = source_date_issues(ins.source, no, profile)
        if date_errors:
            week["errors"].extend(date_errors)
            continue

        manual = [m for m in request["manual_days_off"] if m.get("week_number") == no]
        off = detect_off_sessions(ins.source, keywords, manual)
        match = match_week(ins.source, ins.target, week_no=no, selected_subjects=selected, off_sessions=off,
                           normalizer=inp.normalizer, keywords=keywords, lesson_max_chars=max_chars)

        week.update(status="ready", days_off=[o.to_dict() for o in off], subjects=match.subjects,
                    warnings=match.warnings)
        if match.matched_count:
            header = {cell: ins.source.header.get(cell) for cell in header_cells(profile)}
            week["writes"] = {**header, **match.writes}

    result = {
        "success": True,
        "source_sha256": sha256(job_dir / SOURCE),
        "target_sha256": sha256(job_dir / TARGET),
        "request": request,
        "can_generate": any(w["status"] == "ready" and w["writes"] for w in weeks),
        "weeks": weeks,
    }
    write_json(job_dir / ANALYSIS, result)
    return result


def generate(job_dir: Path) -> dict:
    request = _validate_request(read_json(job_dir / REQUEST))
    analysis_path = job_dir / ANALYSIS
    if not analysis_path.exists():
        raise EngineError("ANALYSIS_OUTDATED", "Chưa có kết quả phân tích, vui lòng phân tích lại.")
    analysis = read_json(analysis_path)
    if (analysis.get("request") != request
            or analysis.get("source_sha256") != sha256(job_dir / SOURCE)
            or analysis.get("target_sha256") != sha256(job_dir / TARGET)):
        raise EngineError("ANALYSIS_OUTDATED", "Lựa chọn hoặc file đã thay đổi, vui lòng phân tích lại.")
    if not analysis.get("can_generate"):
        raise EngineError("NOTHING_TO_GENERATE", "Không có tuần/môn nào đủ điều kiện để điền.")

    profile = load_config().profile
    edits = {w["target_sheet"]: w["writes"] for w in analysis["weeks"] if w["status"] == "ready" and w["writes"]}

    tmp = job_dir / "result.partial.xlsx"  # openpyxl (used by verify) only opens *.xlsx names
    try:
        write_workbook(job_dir / TARGET, tmp, edits, profile)
        verify_written(job_dir / TARGET, tmp, edits)
        os.replace(tmp, job_dir / RESULT)
    finally:
        tmp.unlink(missing_ok=True)

    manual_todo = [
        {"week_number": w["week_number"], "code": warn["code"], "message": warn["message"]}
        for w in analysis["weeks"] for warn in w["warnings"]
        if warn["code"] != "CONTENT_TOO_LONG"
    ] + [
        {"week_number": w["week_number"], "code": err["code"], "message": err["message"]}
        for w in analysis["weeks"] for err in w["errors"]
    ]
    return {
        "success": True,
        "output_file": RESULT,
        "weeks_filled": sorted(w["week_number"] for w in analysis["weeks"] if w["target_sheet"] in edits),
        "cells_written": sum(len(e) for e in edits.values()),
        "manual_todo": manual_todo,
    }
