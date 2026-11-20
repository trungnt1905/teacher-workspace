"""Builders for synthetic week sheets used by matcher tests."""

from common.config import load_config
from common.normalization import SubjectNormalizer, clean_text
from common.timetable_parser import Slot, WeekSheet

CONFIG = load_config()
NORMALIZER = SubjectNormalizer(CONFIG.subjects)
KEYWORDS = CONFIG.subjects["day_off_keywords"]


def make_week(rows: list[tuple], name: str = "TUẦN 1") -> WeekSheet:
    """rows: (day, session, subject, lesson[, equipment]) in timetable order; row numbers are assigned 3, 4, ..."""
    slots = []
    for i, entry in enumerate(rows):
        day, session, subject, lesson, *rest = entry
        row = 3 + i
        slots.append(Slot(
            sheet=name, day=day, session=session, row=row, period=str(i + 1),
            subject_raw=clean_text(subject), subject=NORMALIZER.key(subject),
            lesson=lesson, equipment=rest[0] if rest else None,
            subject_cell=f"D{row}", lesson_cell=f"E{row}", equipment_cell=f"F{row}",
        ))
    return WeekSheet(name=name, slots=slots)
