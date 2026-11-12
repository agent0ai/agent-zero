import asyncio
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.types import Update

from plugins._commands.helpers import commands
from plugins._telegram_integration import hooks
from plugins._telegram_integration.helpers import bot_manager, handler, scopes, slash_commands as slash


class TelegramCommandsTests(unittest.TestCase):
    def test_only_current_administrators_can_persist_tool_permissions(self):
        from plugins._telegram_integration.helpers import settings_ui as ui
        manager = importlib.import_module("plugins._telegram_integration.extensions.python.job_loop._10_telegram_bot")
        ctx = SimpleNamespace(id="ctx", config=SimpleNamespace(profile="restricted"),
                              agent0=SimpleNamespace(), data={}, is_running=lambda: False)
        item = {"id": "plugin:_code_execution:code_execution_tool", "name": "code_execution_tool",
                "label": "Code execution", "description": ""}
        policy = {"mode": "custom", "default": "block", "mcp_default": "block",
                  "allowed": [], "blocked": [item["id"]]}
        bot_cfg = {"name": "test", "token": "123456:fake", "enabled": True, "allowed_users": [42, 7], "admin_users": [7]}
        query = SimpleNamespace(from_user=SimpleNamespace(id=42, username=None), answer=AsyncMock(),
                                message=SimpleNamespace(chat=SimpleNamespace(id=1, type="private"), message_id=2))
        instance = SimpleNamespace(bot=SimpleNamespace(token="token"))

        async def check(root):
            policy_path = root / "restricted/plugins/_tool_access/config.json"
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(json.dumps(policy))
            original = policy_path.read_bytes()
            with patch.object(ui.editor, "USER_AGENTS_ROOT", root), \
                 patch.object(ui.plugins, "determine_plugin_asset_path", return_value=str(policy_path)), \
                 patch.object(ui.editor, "_invalidate_profile_caches"), \
                 patch.object(ui.projects, "get_context_project_name", return_value=""), \
                 patch.object(ui.plugins, "get_enabled_plugins", return_value=["_commands"]), \
                 patch.object(ui.plugins, "get_plugin_config", return_value={"bots": [bot_cfg]}), \
                 patch.object(ui.plugins, "get_toggle_state", return_value="enabled"), \
                 patch.object(scopes, "configured_bots", return_value=[scopes.BotConfig("", "", bot_cfg)]), \
                 patch.object(scopes, "enabled", return_value=True), \
                 patch.object(handler, "get_bound_context", return_value=ctx), \
                 patch.object(ui.tool_policy, "get_tool_catalog", return_value=[item]), \
                 patch.object(ui.tool_policy, "get_policy", side_effect=lambda agent: json.loads(policy_path.read_text())), \
                 patch.object(ui.tc, "raw_send_text", new_callable=AsyncMock), \
                 patch.object(handler, "get_bot", return_value=instance), \
                 patch.object(handler, "_get_or_create_context_from_user", new_callable=AsyncMock, return_value=ctx):
                callback = manager._make_handler(handler.handle_callback_query)
                query.data = "a0:toolset:allow:" + ui._key(ctx, item["id"])
                for allowed, admins in (([], None), ([42], []), ([42, 7], [7]), ([7], [42])):
                    with self.subTest(allowed=allowed, admins=admins):
                        policy_path.write_bytes(original)
                        bot_cfg.update(allowed_users=allowed)
                        bot_cfg.pop("admin_users", None)
                        if admins is not None:
                            bot_cfg["admin_users"] = admins
                        await callback(query, "test", dict(bot_cfg))
                        self.assertEqual(policy_path.read_bytes(), original)
                        self.assertFalse(ui.tool_policy.resolve_tool(
                            ctx.agent0, item["name"], canonical_id=item["id"]).allowed)

                bot_cfg.update(allowed_users=[42, 7], admin_users=[7])
                query.from_user.id = 7
                await callback(query, "test", dict(bot_cfg))
                saved = json.loads(policy_path.read_text())
                self.assertEqual(saved["allowed"], [item["id"]])
                self.assertEqual(saved["blocked"], [])
                self.assertTrue(ui.tool_policy.ensure_tool_allowed(
                    ctx.agent0, item["name"], canonical_id=item["id"]).allowed)

                captured = dict(bot_cfg)
                bot_cfg["admin_users"] = []
                query.data = "a0:toolset:block:" + ui._key(ctx, item["id"])
                await callback(query, "test", captured)
                self.assertEqual(json.loads(policy_path.read_text()), saved)

        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(check(Path(directory)))

    def test_administrator_membership_is_separate_from_message_access(self):
        for config, user_id, username, allowed, admin in (
            ({}, 42, None, True, False),
            ({"admin_users": []}, 42, None, True, False),
            ({"allowed_users": [42]}, 42, None, True, False),
            ({"allowed_users": [42], "admin_users": [7]}, 42, None, True, False),
            ({"allowed_users": [42], "admin_users": [7]}, 7, None, False, True),
            ({"admin_users": [" 42 "]}, 42, None, True, True),
            ({"admin_users": ["@operator"]}, 42, "operator", True, True),
            ({"admin_users": ["OPERATOR"]}, 42, "operator", True, True),
        ):
            with self.subTest(config=config, user_id=user_id, username=username):
                self.assertEqual(handler._is_allowed(config, user_id, username), allowed)
                self.assertEqual(handler._is_admin(config, user_id, username), admin)

    def test_settings_menus_check_sender_on_every_command_route(self):
        from plugins._telegram_integration.helpers import settings_ui as ui
        ctx = SimpleNamespace(id="ctx", config=SimpleNamespace(profile="restricted"),
                              agent0=SimpleNamespace(), data={}, is_running=lambda: False)
        instance = SimpleNamespace(bot=SimpleNamespace(token="token"), bot_info=SimpleNamespace(username="OurBot"))
        bot_cfg = {"allowed_users": [42, 7], "admin_users": [7]}
        items = [{"name": name, "path": name, "source_scope_key": "builtin"} for name in ("permissions", "plugins")]
        policy = {"mode": "custom", "default": "block", "mcp_default": "block", "allowed": [], "blocked": []}

        async def check():
            with patch.object(handler, "get_bot", return_value=instance), \
                 patch.object(handler, "_get_or_create_context", new_callable=AsyncMock, return_value=ctx), \
                 patch.object(handler, "_get_or_create_context_from_user", new_callable=AsyncMock, return_value=ctx), \
                 patch.object(slash, "available_commands", return_value=items), \
                 patch.object(commands, "resolve_command_invocation", new_callable=AsyncMock) as resolve, \
                 patch.object(slash.command_ui, "handle_command", new_callable=AsyncMock, return_value=False), \
                 patch.object(slash.command_ui, "handle_callback", new_callable=AsyncMock, return_value=False), \
                 patch.object(slash.integration_commands, "try_handle_command", return_value=None), \
                 patch.object(ui.projects, "get_context_project_name", return_value=""), \
                 patch.object(ui.tool_policy, "get_tool_catalog", return_value=[]), \
                 patch.object(ui.tool_policy, "get_policy", return_value=policy), \
                 patch.object(ui, "_plugin_items", return_value=[]), \
                 patch.object(ui.tc, "raw_send_text", new_callable=AsyncMock) as send:
                for user_id in (42, 7):
                    for name in ("permissions", "plugins"):
                        effect = ({"type": "open_agent_editor", "view": "permissions"} if name == "permissions"
                                  else {"type": "open_modal", "path": "/components/plugins/list/plugin-list.html"})
                        resolve.return_value = {"result": {"effects": [effect]}}
                        message = Update.model_validate({"update_id": 1, "message": {
                            "message_id": 2, "date": 1700000000, "text": f"/{name}@OurBot",
                            "from": {"id": user_id, "is_bot": False, "first_name": "Test"},
                            "chat": {"id": 1, "type": "private"},
                        }}).message
                        for route in ("message", "run_callback", "text_callback"):
                            with self.subTest(user_id=user_id, command=name, route=route):
                                send.reset_mock()
                                if route == "message":
                                    await handler.handle_message(message, "test", bot_cfg)
                                else:
                                    data = f"a0:run:{name}" if route == "run_callback" else message.text
                                    query = SimpleNamespace(from_user=message.from_user, message=message,
                                                            data=data, answer=AsyncMock())
                                    await handler.handle_callback_query(query, "test", bot_cfg)
                                send.assert_awaited_once()
                                if user_id == 7:
                                    self.assertIn("inline_keyboard", send.call_args.args[5])
                                else:
                                    self.assertIn("administrator", send.call_args.args[2])
                                    self.assertIsNone(send.call_args.args[5])
        asyncio.run(check())

    @patch.object(scopes, "configured_bots", return_value=[])
    def test_config_names_and_connection_changes(self, _configured):
        config = {"bots": [{"name": "", "token": " 123456:secret ", "enabled": True, "admin_users": [7]}]}
        normalized = hooks.get_plugin_config(config)
        self.assertEqual(normalized["bots"][0]["name"], "bot_123456")
        self.assertEqual(normalized["bots"][0]["token"], "123456:secret")
        self.assertEqual(normalized["bots"][0]["admin_users"], [7])
        self.assertEqual(config["bots"][0]["name"], "")
        self.assertEqual(hooks.save_plugin_config(normalized), normalized)
        with self.assertRaises(ValueError):
            hooks.save_plugin_config({"bots": normalized["bots"] * 2})
        self.assertNotIn("secret", hooks.get_plugin_config({"bots": [{"token": "secret"}]})["bots"][0]["name"])

        manager = importlib.import_module("plugins._telegram_integration.extensions.python.job_loop._10_telegram_bot")
        current = SimpleNamespace(bot=SimpleNamespace(token="old"), webhook_active=False,
                                  group_mode="mention", task=SimpleNamespace(done=lambda: False))
        replacement = SimpleNamespace()
        async def check():
            with patch.object(scopes.plugins, "get_plugin_config", return_value=normalized), \
                 patch.object(scopes.plugins, "get_toggle_state", return_value="enabled"), \
                 patch.object(scopes, "configured_bots", return_value=[scopes.BotConfig("", "", normalized["bots"][0])]), \
                 patch.object(scopes, "enabled", return_value=True), \
                 patch.object(manager, "ensure_dependencies"), \
                 patch("plugins._telegram_integration.helpers.migration.prepare_upgrade"), \
                 patch.object(handler, "cleanup_old_attachments"), \
                 patch.object(bot_manager, "get_all_bots", return_value={"bot_123456": current}), \
                 patch.object(bot_manager, "stop_bot", new_callable=AsyncMock) as stop, \
                 patch.object(bot_manager, "create_bot", return_value=replacement), \
                 patch.object(bot_manager, "cache_bot_info", new_callable=AsyncMock), \
                 patch.object(bot_manager, "register_bot_commands", new_callable=AsyncMock), \
                 patch.object(bot_manager, "start_polling", new_callable=AsyncMock) as start:
                await manager.TelegramBotManager(agent=None).execute()
                stop.assert_awaited_once_with("bot_123456")
                start.assert_awaited_once_with(replacement)
                stop.reset_mock()
                current.bot.token = "123456:secret"
                await manager.TelegramBotManager(agent=None).execute()
                stop.assert_not_awaited()
        asyncio.run(check())

    def test_shared_commands_and_telegram_effects(self):
        ctx = SimpleNamespace(id="test-context", agent0=SimpleNamespace(), is_running=lambda: False)
        async def check(root):
            scope = root / "commands"
            scope.mkdir()
            (scope / "summarize.command.yaml").write_text(
                'name: summarize\ndescription: Summarize input\ntype: text\ntemplate_path: summarize.txt\n')
            (scope / "summarize.txt").write_text('Summarize: {raw}')
            (scope / "stop.command.yaml").write_text(
                'name: stop\ndescription: Custom stop\ntype: text\ntemplate_path: stop.txt\n')
            (scope / "stop.txt").write_text('Override: {raw}')
            with patch.object(commands, "get_scope_directory", return_value=str(scope)), \
                 patch.object(commands, "_iter_precedence_scopes", return_value=[""]), \
                 patch.object(commands, "get_scope_payload", return_value={}), \
                 patch.object(commands, "_discover_plugin_commands", return_value=[]), \
                 patch.object(commands, "_get_context", return_value=ctx), \
                 patch.object(slash.AgentContext, "get", return_value=ctx), \
                 patch.object(slash.projects, "get_context_project_name", return_value=""), \
                 patch.object(slash.plugins, "get_enabled_plugins", return_value=["_commands"]), \
                 patch.object(slash, "reply", new_callable=AsyncMock) as reply, \
                 patch.object(slash.command_ui, "handle_command", new_callable=AsyncMock, return_value=False):
                self.assertEqual(await slash.handle(ctx, "token", 1, 2, "/summarize hello\nworld"), "Summarize: hello\nworld")
                self.assertEqual(await slash.handle(ctx, "token", 1, 2, "hello /summarize"), "Summarize: hello")
                self.assertEqual(await slash.handle(ctx, "token", 1, 2, "/stop custom"), "Override: custom")
                self.assertEqual(await slash.handle(ctx, "token", 1, 2, "Read /a0/file"), "Read /a0/file")
                self.assertIsNone(await slash.handle(ctx, "token", 1, 2, "/missing"))
                self.assertIn("Unknown command", reply.call_args.args[3])
                scope.joinpath("stop.command.yaml").unlink()
                with patch("api.stop.stop_context", return_value={"message": "Stopped."}) as stop:
                    self.assertIsNone(await slash.handle(ctx, "token", 1, 2, "/stop"))
                    stop.assert_called_once_with(ctx)
                    self.assertEqual(reply.call_args.args[3], "Stopped.")
                self.assertIsNone(await slash.handle(ctx, "token", 1, 2, "/attach"))
                self.assertIn("attachment button", reply.call_args.args[3])
                await slash.send_menu(ctx, "token", 1, 2)
                markup = reply.call_args.args[4]
                self.assertTrue(all(len(button["callback_data"].encode()) <= 64 for row in markup["inline_keyboard"] for button in row))
                names = dict(slash.menu_commands())
                self.assertIn("computer_use", names)
                self.assertIn("summarize", names)
                self.assertTrue(all(len(name) <= 32 and "-" not in name for name in names))
                handled, text = await slash.handle_callback(ctx, "token", 1, 2, "a0:run:summarize example")
                self.assertTrue(handled)
                self.assertEqual(text, "Summarize: example")
                ctx.is_running = lambda: True
                with self.assertRaises(ValueError):
                    await slash.handle_callback(ctx, "token", 1, 2, "a0:compact:test-context")
                with self.assertRaises(ValueError):
                    await slash.select_session(ctx, ctx)
                result = await slash.apply_result(ctx, "token", 1, 2, "goal", {
                    "effects": [{"type": "goal_changed"}, {"type": "toast", "message": "Goal set."},
                                {"type": "send_message", "text": "Objective"}]})
                self.assertEqual(result, "Objective")
                self.assertEqual(reply.call_args.args[3], "Goal set.")
                self.assertIsNone(await slash.apply_result(ctx, "token", 1, 2, "empty", {}))
                self.assertEqual(reply.call_args.args[3], "/empty complete.")
        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(check(Path(directory)))

    def test_settings_menus_validate_scope_and_use_existing_owners(self):
        from plugins._telegram_integration.helpers import settings_ui as ui
        ctx = SimpleNamespace(id="ctx", config=SimpleNamespace(profile="agent0"),
                              agent0=SimpleNamespace(), is_running=lambda: False)
        item = {"id": "core:test", "name": "test", "label": "Test tool", "description": ""}
        policy = {"mode": "custom", "default": "allow", "mcp_default": "block", "allowed": [], "blocked": []}
        meta = SimpleNamespace(title="Test plugin", always_enabled=False)
        async def check():
            with patch.object(ui.projects, "get_context_project_name", return_value="project"), \
                 patch.object(ui.plugins, "get_enabled_plugins", return_value=["_commands"]), \
                 patch.object(ui.tool_policy, "get_tool_catalog", return_value=[item]), \
                 patch.object(ui.tool_policy, "get_policy", side_effect=lambda agent: dict(policy)), \
                 patch.object(ui.tc, "raw_send_text", new_callable=AsyncMock) as send, \
                 patch.object(ui.editor, "build_change_plan", return_value="plan") as build, \
                 patch.object(ui.editor, "apply_change_plan") as apply, \
                 patch.object(ui, "_plugin_items", return_value=[("example", meta)]), \
                 patch.object(ui.plugins, "get_toggle_state", return_value="disabled"), \
                 patch.object(ui.plugins, "toggle_plugin") as toggle:
                for kind in ("permissions", "plugins"):
                    with self.assertRaises(PermissionError):
                        await ui.show(ctx, "token", 1, 2, kind)
                for action in ("pluginspage", "permissionspage", "plugin", "tool", "toolset", "policy"):
                    with self.subTest(action=action), self.assertRaises(PermissionError):
                        await ui.handle_callback(ctx, "token", 1, 2, action, "untrusted")
                send.assert_not_awaited()
                build.assert_not_called()
                apply.assert_not_called()
                toggle.assert_not_called()
                self.assertFalse(await ui.handle_callback(ctx, "token", 1, 2, "run", "status"))
                await ui.show(ctx, "token", 1, 2, "permissions", is_admin=True)
                for row in send.call_args.args[5]["inline_keyboard"]:
                    for button in row:
                        self.assertLessEqual(len(button['callback_data'].encode()), 64)
                key = ui._key(ctx, item['id'])
                await ui.handle_callback(ctx, "token", 1, 2, "toolset", "block:" + key, is_admin=True)
                patch_data = build.call_args.args[0]
                self.assertEqual(patch_data['tool_policy']['blocked'], ['core:test'])
                self.assertEqual(patch_data['tool_policy']['mcp_default'], 'block')
                apply.assert_called_once_with('plan')
                ctx.config.profile = 'other'
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", "allow:" + key, is_admin=True)
                ctx.config.profile = 'agent0'
                ctx.is_running = lambda: True
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", "allow:" + key, is_admin=True)
                ctx.is_running = lambda: False
                await ui.handle_callback(ctx, "token", 1, 2, "plugin", 'on:' + ui._key(ctx, 'example'), is_admin=True)
                toggle.assert_called_once_with('example', True)
                meta.always_enabled = True
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "plugin", 'off:' + ui._key(ctx, 'example'), is_admin=True)
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", 'block:' + ui._key(ctx, 'core:response'), is_admin=True)
        asyncio.run(check())

    def test_real_dispatch_and_bot_suffix(self):
        instance = SimpleNamespace(bot_info=SimpleNamespace(username="OurBot"))
        self.assertEqual(handler._normalize_bot_command("/goal@ourbot multi\nline", instance), "/goal multi\nline")
        self.assertIsNone(handler._normalize_bot_command("/goal@otherbot test", instance))
        template = (Path(__file__).resolve().parents[1] / "plugins/_telegram_integration/prompts/fw.telegram.user_message.md").read_text()
        envelope = template.replace("{{sender}}", "Tester").replace("{{body}}", "literal /goal")
        self.assertEqual(commands.parse_slash_invocation(envelope)["command_name"], "")
        async def check():
            received = []
            async def receive(message):
                received.append(message.text)
            with patch.object(bot_manager, "_bots", {}):
                bot = bot_manager.create_bot("test", "123456:test", receive, receive,
                                             on_command_control=receive, group_mode="off")
                try:
                    for chat_type, text in [("group", "/status"), ("group", "/start"), ("private", "/goal test")]:
                        update = Update.model_validate({"update_id": 1, "message": {
                            "message_id": 1, "date": 1700000000, "text": text,
                            "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                            "chat": {"id": 42, "type": chat_type},
                            "entities": [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}],
                        }})
                        await bot.dispatcher.feed_update(bot.bot, update)
                    self.assertEqual(received, ["/goal test"])
                finally:
                    await bot.bot.session.close()
        asyncio.run(check())


if __name__ == "__main__":
    unittest.main()
