import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Update

from api.plugins import Plugins
from helpers import cache, files, plugins
from plugins._telegram_integration.helpers import bot_manager, handler


manager = importlib.import_module("plugins._telegram_integration.extensions.python.job_loop._10_telegram_bot")
PLUGIN = "_telegram_integration"
SOURCE = Path(__file__).resolve().parents[1] / "plugins" / PLUGIN
SCOPES = [("project", ""), ("", "profile"), ("project", "profile")]


@pytest.fixture
def telegram_config(monkeypatch, tmp_path):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(cache, "_cache", {})
    monkeypatch.setattr(plugins, "get_enabled_plugin_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(plugins, "after_plugin_change", Mock())
    root = tmp_path / "plugins" / PLUGIN
    root.mkdir(parents=True)
    for name in ("plugin.yaml", "hooks.py", "default_config.yaml"):
        (root / name).write_text((SOURCE / name).read_text())
    config = {"bots": [{"name": "scope_test", "token": "123456:fake", "enabled": True,
                        "allowed_users": [], "default_project": "project"}]}
    plugins.save_plugin_config(PLUGIN, "", "", config)
    monkeypatch.setattr(manager, "ensure_dependencies", Mock())
    monkeypatch.setattr(manager.NotificationManager, "send_notification", Mock())
    monkeypatch.setattr(handler, "cleanup_old_attachments", Mock())
    return config


@pytest.mark.parametrize("project,profile", SCOPES)
@pytest.mark.parametrize("action", ["save_config", "toggle_plugin"])
def test_telegram_rejects_scoped_writes_before_changing_any_files(telegram_config, project, profile, action):
    global_toggle = Path(plugins.determine_plugin_asset_path(PLUGIN, "", "", plugins.ENABLED_FILE_NAME))
    global_toggle.touch()
    global_path = Path(plugins.determine_plugin_asset_path(PLUGIN, "", "", plugins.CONFIG_FILE_NAME))
    original = global_path.read_bytes()
    api = Plugins.__new__(Plugins)
    result = getattr(api, "_" + action)({
        "plugin_name": PLUGIN, "project_name": project, "agent_profile": profile,
        "settings": {"bots": []}, "enabled": False, "clear_overrides": True,
    })
    assert result.status_code == 400
    assert "does not support" in result.get_data(as_text=True)
    assert global_path.read_bytes() == original
    assert global_toggle.exists()
    assert not Path(plugins.determine_plugin_asset_path(PLUGIN, project, profile)).exists()


@pytest.mark.parametrize("project,profile", SCOPES)
def test_plugins_that_support_scopes_keep_scoped_saves_and_activation(telegram_config, project, profile):
    root = Path(files.get_abs_path("plugins/scoped_plugin"))
    root.mkdir()
    (root / "plugin.yaml").write_text("name: scoped_plugin\nper_project_config: true\nper_agent_config: true\n")
    plugins.save_plugin_config("scoped_plugin", project, profile, {"value": 42})
    assert plugins.get_plugin_config("scoped_plugin", project_name=project, agent_profile=profile) == {"value": 42}
    plugins.toggle_plugin("scoped_plugin", False, project, profile)
    assert Path(plugins.determine_plugin_asset_path("scoped_plugin", project, profile, plugins.DISABLED_FILE_NAME)).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
@pytest.mark.parametrize("asset", ["config.json", ".toggle-0", ".toggle-1"])
async def test_legacy_scoped_settings_stop_bots_and_block_every_update(telegram_config, monkeypatch, project, profile, asset):
    legacy = Path(plugins.determine_plugin_asset_path(PLUGIN, project, profile, asset))
    legacy.parent.mkdir(parents=True)
    contents = json.dumps({"bots": [{**telegram_config["bots"][0], "enabled": False, "allowed_users": [111]}]}) if asset == "config.json" else ""
    legacy.write_text(contents)
    # The global bot is permissive; a scoped copy must never be silently ignored.
    current = plugins.get_plugin_config(PLUGIN)["bots"][0]
    assert handler._is_allowed(current, 222, None)
    assert manager._has_scoped_settings()
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(object(), "scope_test", current)
    dispatch.assert_not_awaited()
    monkeypatch.setattr(bot_manager, "get_all_bots", lambda: {"scope_test": object()})
    stop, create = AsyncMock(), Mock()
    monkeypatch.setattr(bot_manager, "stop_bot", stop)
    monkeypatch.setattr(bot_manager, "create_bot", create)
    await manager.TelegramBotManager(agent=None).execute()
    stop.assert_awaited_once_with("scope_test")
    create.assert_not_called()
    handler.cleanup_old_attachments.assert_not_called()
    manager.ensure_dependencies.assert_not_called()
    manager.NotificationManager.send_notification.assert_called_once()
    assert legacy.read_text() == contents

    telegram_config["bots"][0]["allowed_users"] = [111]
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    api = Plugins.__new__(Plugins)
    listed = api._list_configs({"plugin_name": PLUGIN, "asset_type": "config" if asset == "config.json" else "toggle"})
    assert str(legacy) in {entry["path"] for entry in listed["data"]}
    assert api._delete_config({"plugin_name": PLUGIN, "path": str(legacy)}) == {"ok": True}
    assert not manager._has_scoped_settings()
    context = AsyncMock()
    monkeypatch.setattr(handler, "_get_or_create_context", context)
    outsider = Update.model_validate({"update_id": 1, "message": {
        "message_id": 1, "date": 1700000000, "text": "OUTSIDER_AGENT_TRIGGER",
        "from": {"id": 222, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 222, "type": "private"},
    }}).message
    await manager._make_handler(handler.handle_message)(outsider, "scope_test", current)
    context.assert_not_awaited()
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(object(), "scope_test", current)
    assert dispatch.await_args.args[2]["allowed_users"] == [111]
    assert handler._get_project(dispatch.await_args.args[2], 111) == "project"


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["disabled", "removed", "renamed", "plugin_disabled"])
async def test_telegram_updates_never_fall_back_to_revoked_config(telegram_config, change):
    captured = dict(telegram_config["bots"][0])
    if change == "disabled":
        telegram_config["bots"][0]["enabled"] = False
    elif change == "removed":
        telegram_config["bots"] = []
    elif change == "renamed":
        telegram_config["bots"][0]["name"] = "renamed"
    else:
        plugins.toggle_plugin(PLUGIN, False)
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(object(), "scope_test", captured)
    dispatch.assert_not_awaited()


def test_telegram_scopes_are_not_advertised(telegram_config):
    meta = plugins.get_plugin_meta(PLUGIN)
    assert not meta.per_project_config and not meta.per_agent_config
