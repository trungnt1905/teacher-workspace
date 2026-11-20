import json
import re

import openpyxl
import pytest

from common.config import ConfigError, load_config


@pytest.fixture(scope="module")
def config():
    return load_config()


def test_profile_has_32_slots_in_row_order(config):
    rows = config.slot_rows()
    assert rows == list(range(3, 35))


def test_default_excluded_subjects_are_known(config):
    group_keys = {g["key"] for g in config.subjects["interchangeable_groups"]}
    assert set(config.subjects["default_excluded_subjects"]) <= set(config.subjects["subjects"]) | group_keys


def test_invalid_config_is_rejected(tmp_path, config):
    profile = dict(config.profile, days=[{"label": "Hai", "sessions": {"SÁNG": [6, 3]}}])
    (tmp_path / "template_profile.json").write_text(json.dumps(profile), encoding="utf-8")
    (tmp_path / "subject_config.json").write_text(json.dumps(config.subjects), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def _week_sheets(workbook, pattern):
    return [ws for ws in workbook.worksheets if re.match(pattern, ws.title)]


def _check_anchors(ws, profile):
    for anchor in profile["structure_anchors"]:
        value = str(ws[anchor["cell"]].value or "")
        if "value" in anchor:
            assert value.strip() == anchor["value"], f"{ws.title}!{anchor['cell']}"
        else:
            assert anchor["value_contains"] in value, f"{ws.title}!{anchor['cell']}"


@pytest.mark.parametrize("fixture", ["lbg_mau.xlsx", "tuan8_lop_dich.xlsx"])
def test_profile_matches_real_workbooks(config, fixtures_dir, fixture):
    """The fixed coordinates in template_profile.json must match the teacher's real files."""
    profile = config.profile
    wb = openpyxl.load_workbook(fixtures_dir / fixture)
    expected = set(profile["expected_merged_ranges"])

    sheets = [wb[profile["template_sheet"]], *_week_sheets(wb, profile["week_sheet_pattern"])]
    assert len(sheets) > 1

    for ws in sheets:
        _check_anchors(ws, profile)
        merged = {str(r) for r in ws.merged_cells.ranges}
        # Source sheets may add merges inside E:F to mark a day off (e.g. lbg_mau TUẦN 7: E23:F28).
        extra = merged - expected
        assert expected <= merged, f"{ws.title}: missing merges {sorted(expected - merged)}"
        assert all(re.fullmatch(r"E\d+:F\d+", r) for r in extra), f"{ws.title}: unexpected merges {extra}"
        for day in profile["days"]:
            assert str(ws[day["date_cell"]].value or "").startswith(day["label"]), f"{ws.title}!{day['date_cell']}"
