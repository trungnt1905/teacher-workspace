"""Subject-by-subject matching of source lessons to target slots (DETAIL_DESIGN §4.6–§4.10).

Rule of thumb: when in doubt, skip the whole subject for that week and say why — never guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .day_off_detector import OffSession, is_keyword_off
from .errors import issue
from .normalization import SubjectNormalizer
from .timetable_parser import Slot, WeekSheet

DEFAULT_LESSON_MAX_CHARS = 90


@dataclass
class WeekMatch:
    subjects: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    writes: dict[str, str | None] = field(default_factory=dict)  # target cell -> value (None clears)

    @property
    def matched_count(self) -> int:
        return sum(1 for s in self.subjects if s["status"] == "matched")


def _where(slots: list[Slot]) -> str:
    return ", ".join(f"thứ {s.day} tiết {s.period or '?'}" for s in slots)


def match_week(
    source: WeekSheet,
    target: WeekSheet,
    *,
    week_no: int,
    selected_subjects: set[str],
    off_sessions: list[OffSession],
    normalizer: SubjectNormalizer,
    keywords: list[str],
    lesson_max_chars: int = DEFAULT_LESSON_MAX_CHARS,
) -> WeekMatch:
    result = WeekMatch()
    off = {(o.day, o.session) for o in off_sessions}
    src_groups, dst_groups = source.by_subject(), target.by_subject()

    for subject in sorted(set(src_groups) | set(dst_groups)):
        if subject not in selected_subjects:
            continue
        src, dst = src_groups.get(subject, []), dst_groups.get(subject, [])
        entry = {"subject": subject, "source_count": len(src), "target_count": len(dst), "items": []}

        def skip(status: str, warning: dict):
            entry["status"] = status
            result.subjects.append(entry)
            result.warnings.append(warning)

        if not src or not dst:
            side = "file nguồn" if src else "file đích"
            skip("skipped_unknown_subject", issue(
                "UNKNOWN_SUBJECT", f"Tuần {week_no}: môn “{subject}” chỉ có ở {side}.",
                week=week_no, subject=subject))
            continue

        off_src = [s for s in src if (s.day, s.session) in off or is_keyword_off(s, keywords)]
        off_dst = [s for s in dst if (s.day, s.session) in off]
        if off_src or off_dst:
            parts = []
            if off_src:
                parts.append(f"nguồn nghỉ {_where(off_src)}")
            if off_dst:
                parts.append(f"đích có tiết vào buổi nghỉ ({_where(off_dst)})")
            skip("skipped_day_off", issue(
                "AFFECTED_BY_DAY_OFF",
                f"Tuần {week_no}, môn {subject}: {'; '.join(parts)} — cần điền thủ công.",
                week=week_no, subject=subject,
                source_rows=[s.row for s in off_src], target_rows=[s.row for s in off_dst]))
            continue

        empty = [s for s in src if not s.has_lesson]
        if empty:
            skip("skipped_empty_lesson", issue(
                "EMPTY_LESSON",
                f"Tuần {week_no}, môn {subject}: file nguồn chưa có tên bài ở {_where(empty)} — môn này không được điền.",
                week=week_no, subject=subject, source_rows=[s.row for s in empty]))
            continue

        if len(src) != len(dst):
            skip("skipped_count_mismatch", issue(
                "SUBJECT_COUNT_MISMATCH",
                f"Tuần {week_no}, môn {subject}: nguồn {len(src)} tiết, đích {len(dst)} tiết — cần điền thủ công.",
                week=week_no, subject=subject, source_count=len(src), target_count=len(dst)))
            continue

        entry["status"] = "matched"
        for order, (s, t) in enumerate(zip(src, dst), start=1):
            item = {
                "order": order,
                "source_ref": f"{s.sheet}!{s.lesson_cell}",
                "target_day": t.day,
                "target_session": t.session,
                "target_period": t.period,
                "lesson": s.lesson,
                "equipment": s.equipment,
                "target_lesson_cell": t.lesson_cell,
                "target_equipment_cell": t.equipment_cell,
            }
            result.writes[t.lesson_cell] = s.lesson
            result.writes[t.equipment_cell] = s.equipment
            if normalizer.is_group(subject) and s.subject_raw != t.subject_raw:
                # Only exception allowed to write column D (§4.10, option b).
                item["subject_rename"] = {"from": t.subject_raw, "to": s.subject_raw}
                result.writes[t.subject_cell] = s.subject_raw
            if s.lesson and len(s.lesson) > lesson_max_chars:
                result.warnings.append(issue(
                    "CONTENT_TOO_LONG",
                    f"Tuần {week_no}, thứ {t.day} tiết {t.period} ({subject}): tên bài dài, có thể bị khuất trong ô.",
                    week=week_no, cell=t.lesson_cell))
            entry["items"].append(item)
        result.subjects.append(entry)

    return result
