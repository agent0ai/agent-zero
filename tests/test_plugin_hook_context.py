import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import plugins


def _capture_hook_context(monkeypatch):
    captured = {}

    def call_plugin_hook(plugin_name, hook_name, default=None, **kwargs):
        captured.update(
            plugin_name=plugin_name,
            hook_name=hook_name,
            hook_context=kwargs["hook_context"],
        )
        return default

    monkeypatch.setattr(plugins, "call_plugin_hook", call_plugin_hook)
    return captured


def test_get_plugin_config_forwards_caller_to_hook(monkeypatch):
    captured = _capture_hook_context(monkeypatch)
    monkeypatch.setattr(
        plugins, "find_plugin_asset", lambda *_args, **_kwargs: {"path": "config.json"}
    )
    monkeypatch.setattr(plugins.files, "exists", lambda _path: True)
    monkeypatch.setattr(plugins.files, "read_file", lambda _path: '{"enabled": true}')

    assert plugins.get_plugin_config.__wrapped__("example", caller="ui") == {
        "enabled": True
    }
    assert captured == {
        "plugin_name": "example",
        "hook_name": "get_plugin_config",
        "hook_context": {"caller": "ui"},
    }


def test_save_plugin_config_forwards_caller_to_hook(monkeypatch):
    captured = _capture_hook_context(monkeypatch)
    saved = []
    monkeypatch.setattr(
        plugins, "determine_plugin_asset_path", lambda *_args, **_kwargs: "config.json"
    )
    monkeypatch.setattr(
        plugins.files, "write_file", lambda path, content: saved.append((path, content))
    )

    plugins.save_plugin_config.__wrapped__(
        "example", "", "", {"enabled": True}, caller="agent"
    )

    assert captured == {
        "plugin_name": "example",
        "hook_name": "save_plugin_config",
        "hook_context": {"caller": "agent"},
    }
    assert saved == [("config.json", '{"enabled": true}')]
