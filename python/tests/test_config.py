import json

import pytest

from common.config import ConfigError, load_config


@pytest.fixture(scope="module")
def config():
    return load_config()


def test_profile_has_32_slots_in_row_order(config):
    # Standard file MAU_LBG.xlsx: header on row 3, periods on rows 4–35.
    assert config.slot_rows() == list(range(4, 36))


def test_default_excluded_subjects_are_known(config):
    group_keys = {g["key"] for g in config.subjects["interchangeable_groups"]}
    assert set(config.subjects["default_excluded_subjects"]) <= set(config.subjects["subjects"]) | group_keys


def test_invalid_config_is_rejected(tmp_path, config):
    profile = dict(config.profile, days=[{"label": "Hai", "sessions": {"SÁNG": [6, 3]}}])
    (tmp_path / "template_profile.json").write_text(json.dumps(profile), encoding="utf-8")
    (tmp_path / "subject_config.json").write_text(json.dumps(config.subjects), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(tmp_path)
