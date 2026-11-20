"""Text normalization: Unicode NFC, whitespace, subject names and week sheet names (DETAIL_DESIGN §4.10)."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")


def clean_text(value) -> str:
    """NFC-normalize, collapse whitespace runs and trim. None -> ''."""
    if value is None:
        return ""
    return _WS.sub(" ", unicodedata.normalize("NFC", str(value))).strip()


def raw_text(value) -> str | None:
    """Cell text to copy verbatim into the target: NFC only, keeps inner spacing/newlines.

    Returns None for empty/whitespace-only cells so the target cell is cleared.
    """
    if value is None:
        return None
    text = unicodedata.normalize("NFC", str(value))
    return text if text.strip() else None


class SubjectNormalizer:
    """Maps raw subject cell text to a canonical subject key.

    Order: clean -> alias -> canonical spelling from the subject list -> interchangeable group key.
    Comparison is case-insensitive. Unknown subjects keep their cleaned text as key.
    """

    def __init__(self, subject_config: dict):
        self._canonical = {s.casefold(): s for s in subject_config.get("subjects", [])}
        self._aliases = {clean_text(k).casefold(): v for k, v in subject_config.get("subject_aliases", {}).items()}
        self._groups: dict[str, str] = {}
        self.group_keys: set[str] = set()
        for group in subject_config.get("interchangeable_groups", []):
            self.group_keys.add(group["key"])
            for member in group["members"]:
                self._groups[clean_text(member).casefold()] = group["key"]

    def key(self, raw) -> str:
        text = clean_text(raw)
        if not text:
            return ""
        folded = text.casefold()
        if folded in self._aliases:
            text = self._aliases[folded]
            folded = text.casefold()
        if folded in self._groups:
            return self._groups[folded]
        return self._canonical.get(folded, text)

    def is_group(self, key: str) -> bool:
        return key in self.group_keys


def week_number(sheet_name: str, pattern: str) -> int | None:
    """'TUẦN 09' -> 9 using the profile's week_sheet_pattern; None if not a week sheet."""
    match = re.match(pattern, clean_text(sheet_name), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def has_keyword(value, keywords: list[str]) -> bool:
    text = clean_text(value).casefold()
    return any(k.casefold() in text for k in keywords)
