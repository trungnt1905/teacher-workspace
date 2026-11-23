"""Load and sanity-check the JSON configuration files in python/config/.

Default (fixed) coordinates live in template_profile.json; sheets that do not match them are
located by content (common/layout.py). Nothing in the engine may hardcode coordinates (DETAIL_DESIGN §8.2).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class ConfigError(ValueError):
    """Raised when a configuration file is missing required data or is inconsistent."""


@dataclass(frozen=True)
class Config:
    profile: dict
    subjects: dict

    def slot_rows(self) -> list[int]:
        """All timetable rows in top-to-bottom order (one row = one period)."""
        rows: list[int] = []
        for day in self.profile["days"]:
            for first, last in day["sessions"].values():
                rows.extend(range(first, last + 1))
        return rows


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing config file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path.name}: {exc}") from exc


def _validate_profile(profile: dict) -> None:
    for key in ("template_sheet", "week_sheet_pattern", "header_row", "cells", "structure_anchors",
                "days", "columns"):
        if key not in profile:
            raise ConfigError(f"template_profile.json: missing '{key}'")

    re.compile(profile["week_sheet_pattern"])

    rows: list[int] = []
    for day in profile["days"]:
        for name, (first, last) in day["sessions"].items():
            if first > last:
                raise ConfigError(f"template_profile.json: {day['label']} {name} has rows {first}>{last}")
            rows.extend(range(first, last + 1))
    if rows != sorted(rows) or len(rows) != len(set(rows)):
        raise ConfigError("template_profile.json: day/session rows must be ascending and non-overlapping")


def _validate_subjects(subjects: dict) -> None:
    known = set(subjects.get("subjects", []))
    if not known:
        raise ConfigError("subject_config.json: 'subjects' must not be empty")
    group_keys = set()
    for group in subjects.get("interchangeable_groups", []):
        if not group.get("key") or not group.get("members"):
            raise ConfigError("subject_config.json: each interchangeable group needs 'key' and 'members'")
        group_keys.add(group["key"])
    unknown_excluded = set(subjects.get("default_excluded_subjects", [])) - known - group_keys
    if unknown_excluded:
        raise ConfigError(f"subject_config.json: excluded subjects not in 'subjects': {sorted(unknown_excluded)}")
    for target in subjects.get("subject_aliases", {}).values():
        if target not in known:
            raise ConfigError(f"subject_config.json: alias target '{target}' not in 'subjects'")


def load_config(config_dir: Path = CONFIG_DIR) -> Config:
    profile = _load_json(config_dir / "template_profile.json")
    subjects = _load_json(config_dir / "subject_config.json")
    _validate_profile(profile)
    _validate_subjects(subjects)
    return Config(profile=profile, subjects=subjects)
