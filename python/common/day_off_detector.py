"""Off periods and off sessions (DETAIL_DESIGN §4.8).

- Off period (source): lesson cell empty, or subject/lesson text contains a day-off keyword ("nghỉ").
- Off session: every period of a (day, session) in the source is off. Teachers can override per session.
"""

from __future__ import annotations

from dataclasses import dataclass

from .normalization import has_keyword
from .timetable_parser import Slot, WeekSheet

Session = tuple[str, str]  # (day label, session name)


@dataclass(frozen=True)
class OffSession:
    day: str
    session: str
    detected_by: str  # "auto" | "manual"

    def to_dict(self) -> dict:
        return {"day": self.day, "session": self.session, "detected_by": self.detected_by}


def is_off_period(slot: Slot, keywords: list[str]) -> bool:
    return not slot.has_lesson or has_keyword(slot.subject_raw, keywords) or has_keyword(slot.lesson, keywords)


def is_keyword_off(slot: Slot, keywords: list[str]) -> bool:
    return has_keyword(slot.subject_raw, keywords) or has_keyword(slot.lesson, keywords)


def detect_off_sessions(source: WeekSheet, keywords: list[str], manual: list[dict] | None = None) -> list[OffSession]:
    """manual: [{"day": "Năm", "session": "SÁNG" (optional = whole day), "is_day_off": bool}]."""
    sessions: dict[Session, list[Slot]] = {}
    for slot in source.slots:
        sessions.setdefault((slot.day, slot.session), []).append(slot)

    off = {key: "auto" for key, slots in sessions.items() if all(is_off_period(s, keywords) for s in slots)}

    for override in manual or []:
        targets = [k for k in sessions if k[0] == override.get("day")
                   and (not override.get("session") or k[1] == override["session"])]
        for key in targets:
            if override.get("is_day_off"):
                off[key] = "manual"
            else:
                off.pop(key, None)

    return [OffSession(day, session, how) for (day, session), how in off.items()]
