import pytest

from helpers import settings
from plugins._a0_connector.helpers.remote_tree import build_remote_tree_config


def test_remote_tree_inherits_current_container_settings(monkeypatch):
    config = settings.get_default_settings()
    assert config["remote_tree_inherit"] is True
    for suffix in ("max_depth", "max_files", "max_folders", "max_lines"):
        assert config[f"remote_tree_{suffix}"] == config[f"workdir_{suffix}"]
    monkeypatch.setattr(settings, "get_settings", lambda: config)
    config["workdir_max_lines"] = 1234
    assert build_remote_tree_config()["max_lines"] == 1234
    config.update(remote_tree_inherit=False, remote_tree_max_lines=0)
    assert build_remote_tree_config()["max_lines"] == 0
    assert config["workdir_max_lines"] == 1234
    config["remote_tree_inherit"] = True
    assert build_remote_tree_config()["max_lines"] == 1234


@pytest.mark.parametrize("suffix", ["max_depth", "max_files", "max_folders", "max_lines"])
@pytest.mark.parametrize("value", [None, "", "bad", -1, True, 1.5, float("inf"), float("nan"), {}, [], "2.5", "0", 0, 73])
def test_remote_tree_setting_validation(monkeypatch, suffix, value):
    defaults = settings.get_default_settings()
    monkeypatch.setattr(settings, "get_default_settings", lambda: defaults)
    monkeypatch.setattr(settings, "create_auth_token", lambda: "test-token")
    key = f"remote_tree_{suffix}"
    normalized = settings.normalize_settings({**defaults, key: value})
    expected = 0 if value in (0, "0") else 73 if value == 73 else defaults[key]
    assert normalized[key] == expected
