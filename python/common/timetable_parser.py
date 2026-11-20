"""Read one week sheet into ordered slots using the fixed coordinates of template_profile.json (§8.2, §8.7)."""

from __future__ import annotations

from dataclasses import dataclass, field

from openpyxl.worksheet.worksheet import Worksheet

from .normalization import SubjectNormalizer, clean_text, raw_text


@dataclass(frozen=True)
class Slot:
    """One period row. Used both for source lesson records and target slots."""

    sheet: str
    day: str
    session: str
    row: int
    period: str
    subject_raw: str          # cleaned text of the subject cell
    subject: str              # canonical key (alias/group applied)
    lesson: str | None        # verbatim text to copy (None = empty)
    equipment: str | None
    subject_cell: str
    lesson_cell: str
    equipment_cell: str

    @property
    def has_lesson(self) -> bool:
        return self.lesson is not None


@dataclass
class WeekSheet:
    name: str
    slots: list[Slot]
    header: dict[str, str | None] = field(default_factory=dict)  # cell -> verbatim text (title, day dates, sign date)

    def by_subject(self) -> dict[str, list[Slot]]:
        """Subject key -> slots in row order. Slots without a subject are ignored."""
        groups: dict[str, list[Slot]] = {}
        for slot in self.slots:
            if slot.subject:
                groups.setdefault(slot.subject, []).append(slot)
        return groups


def header_cells(profile: dict) -> list[str]:
    cells = [profile["cells"]["week_title"]]
    cells += [day["date_cell"] for day in profile["days"]]
    cells.append(profile["cells"]["sign_date"])
    return cells


def parse_week_sheet(ws: Worksheet, profile: dict, normalizer: SubjectNormalizer) -> WeekSheet:
    cols = profile["columns"]
    slots: list[Slot] = []
    for day in profile["days"]:
        for session, (first, last) in day["sessions"].items():
            for row in range(first, last + 1):
                subject_cell = f"{cols['subject']}{row}"
                lesson_cell = f"{cols['lesson']}{row}"
                equipment_cell = f"{cols['equipment']}{row}"
                subject_raw = clean_text(ws[subject_cell].value)
                slots.append(Slot(
                    sheet=ws.title,
                    day=day["label"],
                    session=session,
                    row=row,
                    period=clean_text(ws[f"{cols['period']}{row}"].value),
                    subject_raw=subject_raw,
                    subject=normalizer.key(subject_raw),
                    lesson=raw_text(ws[lesson_cell].value),
                    equipment=raw_text(ws[equipment_cell].value),
                    subject_cell=subject_cell,
                    lesson_cell=lesson_cell,
                    equipment_cell=equipment_cell,
                ))
    header = {cell: raw_text(ws[cell].value) for cell in header_cells(profile)}
    return WeekSheet(name=ws.title, slots=slots, header=header)
