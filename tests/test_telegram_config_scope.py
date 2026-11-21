import importlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Update

from api.plugins import Plugins
from helpers import cache, files, plugins, integration_commands
from plugins._telegram_integration.helpers import bot_manager, handler, scopes, command_ui, slash_commands, draft_stream, heartbeat
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT, CTX_TG_BOT_CFG, CTX_TG_USER_ID, CTX_TG_CHAT_ID, CTX_TG_CHAT_TYPE,
)

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
    monkeypatch.setattr(scopes.settings, "get_settings", lambda: {"agent_profile": "agent0"})
    monkeypatch.setattr(handler.AgentContext, "_contexts", {})
    root = tmp_path / "plugins" / PLUGIN
    root.mkdir(parents=True)
    for name in ("plugin.yaml", "hooks.py", "default_config.yaml"):
        (root / name).write_text((SOURCE / name).read_text())
    config = {"bots": [{"name": "scope_test", "token": "123456:fake", "enabled": True,
                        "allowed_users": [111], "admin_users": [111]}]}
    plugins.save_plugin_config(PLUGIN, "", "", config)
    monkeypatch.setattr(manager, "ensure_dependencies", Mock())
    monkeypatch.setattr(manager.NotificationManager, "send_notification", Mock())
    monkeypatch.setattr(handler, "cleanup_old_attachments", Mock())
    return config


def message(user=111, *, chat_type="private"):
    return Update.model_validate({"update_id": 1, "message": {
        "message_id": 1, "date": 1700000000, "text": "SCOPE_TEST",
        "from": {"id": user, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 111, "type": chat_type},
    }}).message


def context(bot="scope_test", project="", profile="agent0", user=111):
    data = {CTX_TG_BOT: bot, CTX_TG_USER_ID: user, CTX_TG_CHAT_ID: 111,
            CTX_TG_CHAT_TYPE: "private", "project": project}
    return SimpleNamespace(id="ctx", data=data, config=SimpleNamespace(profile=profile),
                           get_data=lambda key: data.get(key), is_running=lambda: False)


def save_scoped(config, project, profile):
    config = deepcopy(config)
    config["bots"][0]["token"] = "654321:scoped"
    plugins.save_plugin_config(PLUGIN, project, profile, config)
    return next(bot for bot in scopes.configured_bots() if bot.project == project and bot.profile == profile)


@pytest.mark.parametrize("project,profile", SCOPES)
def test_scoped_saves_activation_and_stable_isolated_identities(telegram_config, project, profile):
    bot = save_scoped(telegram_config, project, profile)
    api = Plugins.__new__(Plugins)
    result = api._save_config({"plugin_name": PLUGIN, "project_name": project,
                              "agent_profile": profile, "settings": {"bots": [bot.config]}})
    assert result["ok"]
    assert scopes.available_bots()[0].keys() == {"scope_test", bot.key}
    assert bot.key != "scope_test" and "scoped" not in bot.key
    assert scopes.resolve(bot, project, profile or "agent0") == bot.config
    plugins.toggle_plugin(PLUGIN, False, project, profile)
    assert bot.key not in scopes.available_bots()[0]
    plugins.toggle_plugin(PLUGIN, True, project, profile)
    assert bot.key in scopes.available_bots()[0]
    assert plugins.get_plugin_meta(PLUGIN).per_project_config
    assert plugins.get_plugin_meta(PLUGIN).per_agent_config


@pytest.mark.parametrize("project,profile", SCOPES)
@pytest.mark.parametrize("token", ["123456:fake", "123456:rotated"])
def test_reusing_bot_identity_in_another_scope_is_rejected_without_writes(telegram_config, project, profile, token):
    duplicate = deepcopy(telegram_config)
    duplicate["bots"][0].update(token=token, name="another_name")
    target = Path(plugins.determine_plugin_asset_path(PLUGIN, project, profile, plugins.CONFIG_FILE_NAME))
    result = Plugins.__new__(Plugins)._save_config({"plugin_name": PLUGIN, "project_name": project,
                                                  "agent_profile": profile, "settings": duplicate})
    assert result.status_code == 400
    assert "separate Telegram bot" in result.get_data(as_text=True)
    assert token not in result.get_data(as_text=True)
    assert not target.exists()
    assert scopes.available_bots()[0].keys() == {"scope_test"}


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
async def test_legacy_duplicate_scopes_pause_conflicting_bots_without_deleting_settings(telegram_config, monkeypatch, project, profile):
    path = Path(plugins.determine_plugin_asset_path(PLUGIN, project, profile, plugins.CONFIG_FILE_NAME))
    path.parent.mkdir(parents=True)
    raw = json.dumps(telegram_config)
    path.write_text(raw)
    assert not scopes.available_bots()[0]
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(message(), "scope_test", telegram_config["bots"][0])
    dispatch.assert_not_awaited()
    stop, create = AsyncMock(), Mock()
    monkeypatch.setattr(bot_manager, "get_all_bots", lambda: {"scope_test": object()})
    monkeypatch.setattr(bot_manager, "stop_bot", stop)
    monkeypatch.setattr(bot_manager, "create_bot", create)
    await manager.TelegramBotManager(agent=None).execute()
    stop.assert_awaited_once_with("scope_test")
    create.assert_not_called()
    handler.cleanup_old_attachments.assert_not_called()
    manager.ensure_dependencies.assert_not_called()
    manager.NotificationManager.send_notification.assert_called_once()
    assert path.read_text() == raw
    save_scoped(telegram_config, project, profile)
    assert len(scopes.available_bots()[0]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
@pytest.mark.parametrize("event_type", ["message", "callback"])
async def test_scoped_events_use_current_rules_and_route_before_context_creation(telegram_config, monkeypatch, project, profile, event_type):
    bot = save_scoped(telegram_config, project, profile)
    msg = message()
    event = msg if event_type == "message" else SimpleNamespace(from_user=msg.from_user, message=msg, data="a0:run:status")
    dispatch = AsyncMock()
    dispatch.__name__ = "handle_callback_query" if event_type == "callback" else "handle_message"
    wrapped = manager._make_handler(dispatch)
    await wrapped(event, bot.key, bot.config)
    dispatch.assert_awaited_once()
    assert dispatch.await_args.args[2]["_initial_scope"] == (project, profile or "agent0")
    dispatch.reset_mock()
    revoked = deepcopy(bot.config)
    revoked["allowed_users"] = [222]
    plugins.save_plugin_config(PLUGIN, project, profile, {"bots": [revoked]})
    await wrapped(event, bot.key, bot.config)
    dispatch.assert_not_awaited()
    plugins.save_plugin_config(PLUGIN, project, profile, {"bots": [bot.config]})
    plugins.toggle_plugin(PLUGIN, False, project, profile)
    await wrapped(event, bot.key, bot.config)
    dispatch.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
async def test_inherited_global_bot_obeys_scoped_disable_in_new_and_existing_chats(telegram_config, monkeypatch, project, profile):
    telegram_config["bots"][0]["default_project"] = project
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    monkeypatch.setattr(scopes.settings, "get_settings", lambda: {"agent_profile": profile or "agent0"})
    assert len(scopes.configured_bots()) == 1
    dispatch = AsyncMock()
    dispatch.__name__ = "handle_message"
    await manager._make_handler(dispatch)(message(), "scope_test", telegram_config["bots"][0])
    dispatch.assert_awaited_once()
    dispatch.reset_mock()
    plugins.toggle_plugin(PLUGIN, False, project, profile)
    for bound in (None, context(project=project, profile=profile or "agent0")):
        monkeypatch.setattr(handler, "get_bound_context", lambda *args: bound)
        await manager._make_handler(dispatch)(message(), "scope_test", telegram_config["bots"][0])
        dispatch.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["disabled", "removed", "renamed", "plugin_disabled", "token", "mode", "webhook_secret"])
async def test_events_never_fall_back_to_removed_or_old_connections(telegram_config, change):
    if change == "webhook_secret":
        telegram_config["bots"][0].update(mode="webhook", webhook_url="https://example.invalid", webhook_secret="s" * 32)
    captured = dict(telegram_config["bots"][0])
    if change == "disabled":
        telegram_config["bots"][0]["enabled"] = False
    elif change == "removed":
        telegram_config["bots"] = []
    elif change == "renamed":
        telegram_config["bots"][0]["name"] = "renamed"
    elif change == "plugin_disabled":
        plugins.toggle_plugin(PLUGIN, False)
    else:
        telegram_config["bots"][0][change] = "webhook" if change == "mode" else "changed"
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(message(), "scope_test", captured)
    dispatch.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
async def test_scoped_bots_start_even_when_global_plugin_is_disabled(telegram_config, monkeypatch, project, profile):
    bot = save_scoped(telegram_config, project, profile)
    plugins.toggle_plugin(PLUGIN, False)
    plugins.toggle_plugin(PLUGIN, True, project, profile)
    assert scopes.available_bots()[0].keys() == {bot.key}
    instance = SimpleNamespace()
    create = Mock(return_value=instance)
    start = AsyncMock()
    monkeypatch.setattr(bot_manager, "get_all_bots", lambda: {})
    monkeypatch.setattr(bot_manager, "create_bot", create)
    monkeypatch.setattr(bot_manager, "cache_bot_info", AsyncMock())
    monkeypatch.setattr(bot_manager, "register_bot_commands", AsyncMock())
    monkeypatch.setattr(bot_manager, "start_polling", start)
    bridge = importlib.import_module("extensions.python.job_loop._11_scoped_telegram")
    await bridge.ScopedTelegramBots(agent=None).execute()
    assert create.call_args.kwargs["name"] == bot.key
    start.assert_awaited_once_with(instance)


@pytest.mark.asyncio
async def test_revocation_stops_replies_streaming_and_heartbeat(telegram_config, monkeypatch):
    ctx = context()
    instance = SimpleNamespace(bot=SimpleNamespace(token=telegram_config["bots"][0]["token"]))
    monkeypatch.setattr(bot_manager, "get_bot", lambda key: instance)
    assert scopes.authorized_bot(ctx) is instance
    plugins.toggle_plugin(PLUGIN, False, "project")
    ctx.data["project"] = "project"
    assert scopes.authorized_bot(ctx) is None
    assert draft_stream._bot_instance(ctx) is None
    assert not await heartbeat._send_heartbeat(ctx, 60)
    temp = Mock()
    monkeypatch.setattr(handler, "_temp_bot", temp)
    assert "no longer authorized" in await handler.send_telegram_reply(ctx, "PRIVATE", ["private.txt"])
    temp.assert_not_called()


def test_scoped_bots_cannot_escape_through_session_or_scope_selection(telegram_config, monkeypatch):
    bot = save_scoped(telegram_config, "project", "profile")
    source = context(bot.key, "project", "profile")
    target = context(bot.key, "other", "profile")
    assert not scopes.can_select_session(source, target)
    target.data["project"] = "project"
    target.data[CTX_TG_USER_ID] = 222
    assert not scopes.can_select_session(source, target)
    target.data[CTX_TG_USER_ID] = 111
    assert scopes.can_select_session(source, target)
    for project, profile in [("", "profile"), ("other", "profile"), ("project", "other")]:
        with pytest.raises(PermissionError):
            scopes.require_scope(source, project, profile)
    with pytest.raises(PermissionError):
        integration_commands._authorize_scope(source, "other", "profile")


@pytest.mark.asyncio
async def test_session_picker_and_direct_selection_do_not_leak_other_users(telegram_config, monkeypatch):
    source = context()
    mine = context()
    mine.id, mine.name = "mine", "My conversation"
    foreign = context(user=222)
    foreign.id, foreign.name = "foreign", "SECRET TITLE"
    webui = context()
    webui.id, webui.name = "webui", "Owner chat"
    webui.data.pop(CTX_TG_BOT)
    for ctx in (mine, foreign, webui):
        ctx.output = lambda: {"last_message": ""}
    monkeypatch.setattr(command_ui.AgentContext, "all", lambda: [mine, foreign, webui])
    assert [item.context for item in command_ui._session_items(source)] == [mine, webui]
    with pytest.raises(PermissionError):
        await slash_commands.select_session(source, foreign)
    telegram_config["bots"][0]["admin_users"] = []
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    assert [item.context for item in command_ui._session_items(source)] == [mine]
    with pytest.raises(PermissionError):
        await slash_commands.select_session(source, webui)


def test_secrets_are_not_added_to_persisted_context_config(telegram_config):
    ctx = context()
    scopes.remember_config(ctx, {**telegram_config["bots"][0], "webhook_secret": "secret"})
    assert "token" not in ctx.data[CTX_TG_BOT_CFG]
    assert "webhook_secret" not in ctx.data[CTX_TG_BOT_CFG]
    assert ctx.data[CTX_TG_BOT_CFG]["allowed_users"] == [111]


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
async def test_real_webhook_dispatch_preserves_scoped_authentication(telegram_config, monkeypatch, project, profile):
    from plugins._telegram_integration.api import webhook
    config = deepcopy(telegram_config)
    config["bots"][0].update(mode="webhook", webhook_url="https://example.invalid", webhook_secret="s" * 32)
    bot = save_scoped(config, project, profile)
    received = []

    async def receive(event, bot_name, bot_cfg):
        received.append((bot_name, bot_cfg["_initial_scope"]))

    async def receive_bound(event):
        await manager._make_handler(receive)(event, bot.key, bot.config)

    monkeypatch.setattr(bot_manager, "_bots", {})
    monkeypatch.setattr(webhook, "ensure_dependencies", Mock())
    instance = bot_manager.create_bot(bot.key, bot.config["token"], receive_bound, receive_bound)
    instance.webhook_active = True
    instance.webhook_secret = "s" * 32
    instance.bot.set_webhook = AsyncMock()
    try:
        await bot_manager.setup_webhook(instance, "https://example.invalid", "s" * 32)
        from urllib.parse import parse_qs, urlsplit
        assert parse_qs(urlsplit(instance.bot.set_webhook.call_args.kwargs["url"]).query)["bot"] == [bot.key]
        endpoint = webhook.TelegramWebhook.__new__(webhook.TelegramWebhook)
        request = SimpleNamespace(args={"bot": bot.key}, headers={"X-Telegram-Bot-Api-Secret-Token": "s" * 32})
        payload = {"update_id": 1, "message": message().model_dump(mode="json", exclude_none=True)}
        assert await endpoint.process(payload, request) == {"ok": True}
        assert received == [(bot.key, (project, profile or "agent0"))]
        received.clear()
        request.headers["X-Telegram-Bot-Api-Secret-Token"] = "wrong"
        assert (await endpoint.process(payload, request)).status_code == 403
        assert not received
        request.headers["X-Telegram-Bot-Api-Secret-Token"] = "s" * 32
        plugins.toggle_plugin(PLUGIN, False, project, profile)
        await endpoint.process(payload, request)
        assert not received
    finally:
        await instance.bot.session.close()


@pytest.mark.asyncio
async def test_project_profile_commands_and_callbacks_validate_before_mutation(telegram_config, monkeypatch):
    bot = save_scoped(telegram_config, "project", "profile")
    ctx = context(bot.key, "project", "profile")
    ctx.agent0 = SimpleNamespace(config=ctx.config)
    ctx.set_data = lambda key, value: ctx.data.update({key: value})
    monkeypatch.setattr(command_ui.projects, "get_active_projects_list", lambda: [{"name": "other", "title": "Other"}])
    monkeypatch.setattr(command_ui.subagents, "get_all_agents_list", lambda: [{"key": "other", "label": "Other"}])
    activate, deactivate = Mock(), Mock()
    monkeypatch.setattr(command_ui.projects, "activate_project", activate)
    monkeypatch.setattr(command_ui.projects, "deactivate_project", deactivate)
    for command in ("/project other", "/project none", "/agent other"):
        with pytest.raises(PermissionError):
            integration_commands.try_handle_command(ctx, command, integration="telegram")
    for data in ("tg:project:set:0", "tg:project:clear", "tg:agent:set:0"):
        with pytest.raises(PermissionError):
            await command_ui.handle_callback(ctx, "token", 111, 1, data)
    activate.assert_not_called()
    deactivate.assert_not_called()
    assert ctx.config.profile == "profile"


@pytest.mark.asyncio
async def test_context_creation_uses_scope_and_retains_session_without_credentials(telegram_config, monkeypatch):
    bot = save_scoped(telegram_config, "project", "profile")
    contexts = {}
    def initialize(*, override_settings):
        assert override_settings == {"agent_profile": "profile"}
        return SimpleNamespace(profile="profile")
    def create(config, name):
        ctx = context(bot.key, "", config.profile)
        ctx.agent0 = SimpleNamespace(config=config)
        contexts[ctx.id] = ctx
        return ctx
    monkeypatch.setattr(handler, "initialize_agent", initialize)
    monkeypatch.setattr(handler.subagents, "get_available_agents_dict", lambda project: {"profile": object()})
    # Use a callable factory with the same lookup contract as AgentContext.
    create.get = contexts.get
    monkeypatch.setattr(handler, "AgentContext", create)
    monkeypatch.setattr(handler.projects, "activate_project", lambda id, project: contexts[id].data.update(project=project))
    monkeypatch.setattr(handler, "_inherit_model_override", Mock())
    current = manager._get_current_bot_cfg(bot.key, message(), bot.config)
    ctx = await handler._get_or_create_context(bot.key, current, message())
    assert ctx and ctx.config.profile == "profile" and ctx.data["project"] == "project"
    assert ctx.data[CTX_TG_BOT] == bot.key
    assert "token" not in ctx.data[CTX_TG_BOT_CFG]
    assert await handler._get_or_create_context(bot.key, current, message()) is ctx


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [{"allowed_users": {}}, {"admin_users": "111"}, {"enabled": "false"}, {"group_mode": "typo"}])
async def test_invalid_security_settings_fail_closed(telegram_config, monkeypatch, bad):
    path = Path(plugins.determine_plugin_asset_path(PLUGIN, "", "", plugins.CONFIG_FILE_NAME))
    telegram_config["bots"][0].update(bad)
    path.write_text(json.dumps(telegram_config))
    dispatch = AsyncMock()
    await manager._make_handler(dispatch)(message(), "scope_test", {})
    dispatch.assert_not_awaited()
    stop = AsyncMock()
    monkeypatch.setattr(bot_manager, "get_all_bots", lambda: {"scope_test": object()})
    monkeypatch.setattr(bot_manager, "stop_bot", stop)
    await manager.TelegramBotManager(agent=None).execute()
    stop.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("project,profile", SCOPES)
async def test_inherited_bot_can_be_enabled_only_in_a_scope(telegram_config, monkeypatch, project, profile):
    telegram_config["bots"][0]["default_project"] = project
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    plugins.toggle_plugin(PLUGIN, False)
    plugins.toggle_plugin(PLUGIN, True, project, profile)
    monkeypatch.setattr(scopes.settings, "get_settings", lambda: {"agent_profile": profile or "agent0"})
    assert scopes.available_bots()[0].keys() == {"scope_test"}
    dispatch = AsyncMock()
    dispatch.__name__ = "handle_message"
    await manager._make_handler(dispatch)(message(), "scope_test", telegram_config["bots"][0])
    dispatch.assert_awaited_once()
    assert not scopes.resolve(scopes.configured_bots()[0], "", "unrelated")


@pytest.mark.asyncio
async def test_saving_equivalent_connection_defaults_does_not_drop_events(telegram_config):
    captured = dict(telegram_config["bots"][0])
    telegram_config["bots"][0].update(mode="polling", webhook_url="https://unused.invalid", webhook_secret="unused")
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    dispatch = AsyncMock()
    dispatch.__name__ = "handle_message"
    await manager._make_handler(dispatch)(message(), "scope_test", captured)
    dispatch.assert_awaited_once()
    telegram_config["bots"][0].update(mode="webhook", webhook_url="https://example.invalid/", webhook_secret="s" * 32)
    captured = {**telegram_config["bots"][0], "webhook_url": "https://example.invalid"}
    plugins.save_plugin_config(PLUGIN, "", "", telegram_config)
    dispatch.reset_mock()
    await manager._make_handler(dispatch)(message(), "scope_test", captured)
    dispatch.assert_awaited_once()
