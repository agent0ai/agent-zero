import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from plugins._commands.helpers import commands
from plugins._whatsapp_integration.helpers import handler, slash_commands as slash


class FakeContext:
    _contexts = {}

    def __init__(self, id, jid='one@s.whatsapp.net', last='2026-01-01', active=False):
        self.id = id
        self.name = id
        self.data = {'wa_chat_id': jid, 'wa_active': active}
        self.config = SimpleNamespace(profile='agent0')
        self.agent0 = SimpleNamespace()
        self.last = last
        self.running = False

    def is_running(self):
        return self.running

    def output(self):
        return {'last_message': self.last}

    @classmethod
    def get(cls, id):
        return cls._contexts.get(id)


def run(coroutine):
    return asyncio.run(coroutine)


class WhatsAppCommandsTests(unittest.TestCase):
    def test_shared_resolver_custom_overrides_and_effects(self):
        ctx = FakeContext('test')
        async def check(root):
            (root / 'summarize.command.yaml').write_text('name: summarize\ndescription: Summarize\ntype: text\ntemplate_path: summarize.txt\n')
            (root / 'summarize.txt').write_text('Summarize: {raw}')
            (root / 'stop.command.yaml').write_text('name: stop\ndescription: Custom stop\ntype: text\ntemplate_path: stop.txt\n')
            (root / 'stop.txt').write_text('Override: {raw}')
            with patch.object(commands, 'get_scope_directory', return_value=str(root)), \
                 patch.object(commands, '_iter_precedence_scopes', return_value=['']), \
                 patch.object(commands, 'get_scope_payload', return_value={}), \
                 patch.object(commands, '_discover_plugin_commands', return_value=[]), \
                 patch.object(commands, '_get_context', return_value=ctx), \
                 patch.object(slash.AgentContext, 'get', return_value=ctx), \
                 patch.object(slash.projects, 'get_context_project_name', return_value=''), \
                 patch.object(slash.plugins, 'get_enabled_plugins', return_value=['_commands']), \
                 patch.object(slash, 'reply', new_callable=AsyncMock) as reply:
                self.assertEqual(await slash.handle(ctx, '/summarize hello\nworld'), 'Summarize: hello\nworld')
                self.assertEqual(await slash.handle(ctx, 'hello /summarize'), 'Summarize: hello')
                self.assertEqual(await slash.handle(ctx, '/stop custom'), 'Override: custom')
                self.assertEqual(await slash.handle(ctx, 'Read /a0/file'), 'Read /a0/file')
                self.assertIsNone(await slash.handle(ctx, '/missing'))
                self.assertIn('Unknown command', reply.call_args.args[1])
                (root / 'stop.command.yaml').unlink()
                with patch('api.stop.stop_context', return_value={'message': 'Stopped.'}) as stop:
                    self.assertIsNone(await slash.handle(ctx, '/stop'))
                    stop.assert_called_once_with(ctx)
                    self.assertEqual(reply.call_args.args[1], 'Stopped.')
                await slash.handle(ctx, '/commands')
                self.assertIn('Page 1/', reply.call_args.args[1])
                self.assertNotIn('/stream', reply.call_args.args[1])
                result = await slash.apply_result(ctx, 'goal', {'effects': [
                    {'type': 'toast', 'message': 'Goal set.'}, {'type': 'goal_changed'},
                    {'type': 'send_message', 'text': 'Objective'}]})
                self.assertEqual(result, 'Objective')
                self.assertEqual(reply.call_args.args[1], 'Goal set.')
        with tempfile.TemporaryDirectory() as root:
            run(check(Path(root)))

    def test_active_chat_binding_and_isolation(self):
        old = FakeContext('ZZZZ', last='2026-01-01')
        recent = FakeContext('AAAA', last='2026-02-01')
        other = FakeContext('other', jid='other@s.whatsapp.net')
        contexts = {ctx.id: ctx for ctx in (old, recent, other)}
        with patch.object(handler, 'AgentContext', FakeContext), \
             patch.object(slash, 'AgentContext', FakeContext), \
             patch.object(FakeContext, '_contexts', contexts), \
             patch.object(slash, 'save_tmp_chat'):
            self.assertEqual(handler._find_chats_by_jid('one@s.whatsapp.net'), ['AAAA', 'ZZZZ'])
            slash.select_session(recent, old)
            self.assertEqual(handler._find_chats_by_jid('one@s.whatsapp.net'), ['ZZZZ', 'AAAA'])
            self.assertTrue(old.data['wa_active'])
            self.assertFalse(recent.data['wa_active'])
            with self.assertRaises(ValueError):
                slash.select_session(old, other)
            recent.running = True
            with self.assertRaises(ValueError):
                slash.select_session(old, recent)

    def test_dispatch_preserves_attachments_and_checks_group_policy(self):
        ctx = FakeContext('context')
        msg = {'body': '/custom text', 'messageId': 'message', 'chatId': 'one@s.whatsapp.net', 'mediaUrls': ['file']}
        async def check():
            with patch.object(handler, '_find_chats_by_jid', return_value=['context']), \
                 patch.object(handler.AgentContext, 'get', return_value=ctx), \
                 patch.object(slash, 'handle', new_callable=AsyncMock, return_value='Rendered prompt') as resolve, \
                 patch.object(handler, '_route_to_chat', new_callable=AsyncMock) as route, \
                 patch.object(handler.wa_client, 'send_typing', new_callable=AsyncMock), \
                 patch.object(handler, 'save_tmp_chat'):
                await handler._dispatch_message({}, dict(msg, isGroup=True))
                resolve.assert_not_awaited()
                await handler._dispatch_message({'allow_group': True}, dict(msg, isGroup=True))
                resolve.assert_not_awaited()
                await handler._dispatch_message({}, dict(msg))
                self.assertEqual(route.call_args.args[0]['body'], 'Rendered prompt')
                self.assertEqual(route.call_args.args[0]['mediaUrls'], ['file'])
                self.assertEqual(ctx.data['wa_last_msg_id'], 'message')
                route.reset_mock()
                resolve.return_value = None
                await handler._dispatch_message({}, dict(msg))
                route.assert_not_awaited()
        run(check())
        for filename in ('fw.wa.user_message.md', 'fw.wa.user_message_group.md'):
            template = (Path(__file__).resolve().parents[1] / 'plugins/_whatsapp_integration/prompts' / filename).read_text()
            envelope = template.replace('{{body}}', 'literal /goal')
            self.assertEqual(commands.parse_slash_invocation(envelope)['command_name'], '')

    def test_allowed_sender_filter_precedes_command_dispatch(self):
        async def check():
            with patch.object(handler.plugins, 'get_enabled_plugins', return_value=['_whatsapp_integration']), \
                 patch.object(handler, '_refresh_typing', new_callable=AsyncMock), \
                 patch.object(handler.wa_client, 'get_messages', new_callable=AsyncMock, return_value=[
                     {'senderNumber': '111', 'body': '/stop'}, {'senderNumber': '222', 'body': '/permissions'}]), \
                 patch.object(handler, '_dispatch_message', new_callable=AsyncMock) as dispatch:
                await handler.poll_messages({'enabled': True, 'allowed_numbers': ['111']})
                dispatch.assert_awaited_once()
                self.assertEqual(dispatch.call_args.args[1]['senderNumber'], '111')
        run(check())

    def test_new_chat_preserves_original_and_export_uses_temporary_document(self):
        old, target = FakeContext('old'), FakeContext('new')
        old.data['chat_model_override'] = {'preset_name': 'Example'}
        async def check():
            with patch.object(slash, 'AgentContext', return_value=target), \
                 patch.object(slash, '_sessions', return_value=[old, target]), \
                 patch.object(slash.projects, 'get_context_project_name', return_value=''), \
                 patch.object(slash, 'save_tmp_chat'), \
                 patch.object(slash, 'reply', new_callable=AsyncMock):
                await slash.apply_result(old, 'new', {'effects': [{'type': 'new_chat'}]})
                self.assertFalse(old.data['wa_active'])
                self.assertTrue(target.data['wa_active'])
                self.assertEqual(target.data['chat_model_override'], old.data['chat_model_override'])
                self.assertIsNot(target.data['chat_model_override'], old.data['chat_model_override'])
            from plugins._whatsapp_integration.helpers import storage_paths
            target.agent0.history = SimpleNamespace(output=lambda: [])
            paths = []
            async def send(base, jid, path, **kwargs):
                self.assertEqual(jid, target.data['wa_chat_id'])
                self.assertEqual(Path(path).read_text(), 'Test transcript')
                self.assertEqual(kwargs['file_name'], 'transcript.txt')
                paths.append(path)
                return {'success': True}
            with tempfile.TemporaryDirectory() as root, \
                 patch.object(storage_paths, 'get_bridge_media_dir', return_value=root), \
                 patch('helpers.history.output_text', return_value='Test transcript'), \
                 patch.object(slash.plugins, 'get_plugin_config', return_value={}), \
                 patch.object(handler.wa_client, 'send_media', side_effect=send):
                await slash.export_transcript(target)
                self.assertTrue(paths)
                self.assertFalse(Path(paths[0]).exists())
        run(check())

    def test_settings_use_canonical_ids_and_existing_write_owners(self):
        from plugins._agent_editor.helpers import editor
        ctx = FakeContext('context')
        policy = {'mode': 'custom', 'default': 'allow', 'mcp_default': 'block', 'allowed': [], 'blocked': []}
        item = {'id': 'core:test', 'name': 'test', 'label': 'Test'}
        async def check():
            with patch.object(slash.tool_policy, 'get_policy', side_effect=lambda agent: dict(policy)), \
                 patch.object(slash.tool_policy, 'get_tool_catalog', return_value=[item]), \
                 patch.object(slash, 'reply', new_callable=AsyncMock), \
                 patch.object(editor, 'build_change_plan', return_value='plan') as build, \
                 patch.object(editor, 'apply_change_plan') as apply:
                await slash.settings_menu(ctx, 'permissions', 'core:test block')
                self.assertEqual(build.call_args.args[0]['tool_policy']['blocked'], ['core:test'])
                self.assertEqual(build.call_args.args[0]['tool_policy']['mcp_default'], 'block')
                apply.assert_called_once_with('plan')
                with self.assertRaises(ValueError):
                    await slash.settings_menu(ctx, 'permissions', 'core:response block')
                ctx.running = True
                with self.assertRaises(ValueError):
                    await slash.settings_menu(ctx, 'permissions', 'core:test allow')
        run(check())

    def test_compaction_requires_current_idle_context_confirmation(self):
        from plugins._chat_compaction.helpers import compactor
        ctx = FakeContext('current')
        ctx.run_task = lambda *args: None
        async def check():
            with patch.object(slash.plugins, 'get_enabled_plugins', return_value=['_chat_compaction']), \
                 patch.object(compactor, 'get_compaction_stats', new_callable=AsyncMock,
                              return_value={'message_count': 20, 'token_count': 2000}), \
                 patch.object(slash, 'reply', new_callable=AsyncMock) as reply, \
                 patch.object(ctx, 'run_task') as start:
                await slash.compact(ctx, '')
                self.assertIn('/compact confirm current', reply.call_args.args[1])
                start.assert_not_called()
                with self.assertRaises(ValueError):
                    await slash.compact(ctx, 'confirm old')
                await slash.compact(ctx, 'confirm current')
                start.assert_called_once()
                ctx.running = True
                with self.assertRaises(ValueError):
                    await slash.compact(ctx, 'confirm current')
        run(check())


if __name__ == '__main__':
    unittest.main()
