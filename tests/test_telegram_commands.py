import asyncio
import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.types import Update

from plugins._commands.helpers import commands
from plugins._telegram_integration import hooks
from plugins._telegram_integration.helpers import bot_manager, handler, slash_commands as slash


class TelegramCommandsTests(unittest.TestCase):
    def test_config_names_and_connection_changes(self):
        config = {"bots": [{"name": "", "token": " 123456:secret ", "enabled": True}]}
        normalized = hooks.get_plugin_config(config)
        self.assertEqual(normalized["bots"][0]["name"], "bot_123456")
        self.assertEqual(normalized["bots"][0]["token"], "123456:secret")
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
            with patch.object(manager.plugins, "get_plugin_config", return_value=normalized), \
                 patch.object(manager, "ensure_dependencies"), \
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
                await ui.show(ctx, "token", 1, 2, "permissions")
                for row in send.call_args.args[5]["inline_keyboard"]:
                    for button in row:
                        self.assertLessEqual(len(button['callback_data'].encode()), 64)
                key = ui._key(ctx, item['id'])
                await ui.handle_callback(ctx, "token", 1, 2, "toolset", "block:" + key)
                patch_data = build.call_args.args[0]
                self.assertEqual(patch_data['tool_policy']['blocked'], ['core:test'])
                self.assertEqual(patch_data['tool_policy']['mcp_default'], 'block')
                apply.assert_called_once_with('plan')
                ctx.config.profile = 'other'
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", "allow:" + key)
                ctx.config.profile = 'agent0'
                ctx.is_running = lambda: True
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", "allow:" + key)
                ctx.is_running = lambda: False
                await ui.handle_callback(ctx, "token", 1, 2, "plugin", 'on:' + ui._key(ctx, 'example'))
                toggle.assert_called_once_with('example', True)
                meta.always_enabled = True
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "plugin", 'off:' + ui._key(ctx, 'example'))
                with self.assertRaises(ValueError):
                    await ui.handle_callback(ctx, "token", 1, 2, "toolset", 'block:' + ui._key(ctx, 'core:response'))
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
