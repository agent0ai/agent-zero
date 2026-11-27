import asyncio
from unittest.mock import patch
import pytest
pytest.importorskip('aiogram')
from aiogram.types import Update
from plugins._telegram_integration.sandbox import bot_manager


def test_guest_dispatch_filters_groups_and_routes_private_commands():
    async def check():
        received = []
        async def receive(message):
            received.append(message.text)
        with patch.object(bot_manager, '_bots', {}), patch.object(bot_manager, 'command_names', ['goal', 'status']):
            bot = bot_manager.create_bot('test', '123456:test', receive, receive, on_command_control=receive, group_mode='off')
            try:
                for chat_type, text in [('group', '/status'), ('group', '/start'), ('private', '/goal test')]:
                    update = Update.model_validate({'update_id': 1, 'message': {
                        'message_id': 1, 'date': 1700000000, 'text': text,
                        'from': {'id': 42, 'is_bot': False, 'first_name': 'Test'},
                        'chat': {'id': 42, 'type': chat_type},
                        'entities': [{'type': 'bot_command', 'offset': 0, 'length': len(text.split()[0])}],
                    }})
                    await bot.dispatcher.feed_update(bot.bot, update)
                assert received == ['/goal test']
            finally:
                await bot.bot.session.close()
    asyncio.run(check())
