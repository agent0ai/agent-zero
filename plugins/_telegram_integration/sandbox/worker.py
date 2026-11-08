"""Telegram SDK, polling, webhook validation and file transport live in this guest."""
import asyncio
import base64
import io
import sys
import threading

sys.path.insert(0, '/plugin/sandbox')
import bot_manager
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, Update

loop = asyncio.new_event_loop()
threading.Thread(target=loop.run_forever, daemon=True).start()
events = {}
METHODS = {'get_me', 'set_my_commands', 'set_webhook', 'delete_webhook', 'send_message',
           'send_document', 'send_photo', 'send_voice', 'send_audio', 'send_video',
           'send_chat_action', 'get_file', 'answer_callback_query'}
RAW_METHODS = {'sendMessage', 'editMessageText', 'editMessageReplyMarkup'}


def serialize(value):
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json', by_alias=True)
    return value


async def dispatch(payload):
    action = payload['action']
    if action == 'create':
        name = payload['name']
        if name in bot_manager.get_all_bots():
            await bot_manager.stop_bot(name)
        queue = events[name] = asyncio.Queue(maxsize=100)
        def callback(kind):
            async def receive(event):
                await queue.put({'kind': kind, 'event': serialize(event)})
            return receive
        bot_manager.command_names = payload['commands']
        instance = bot_manager.create_bot(name, payload['token'], callback('message'), callback('start'),
                                          callback('control'), callback('callback'), callback('members'),
                                          payload['group_mode'])
        return serialize(await bot_manager.cache_bot_info(instance))
    if action == 'events':
        instance = bot_manager.get_bot(payload['name'])
        if not instance or (instance.task and instance.task.done()):
            raise RuntimeError('Polling stopped')
        queue = events[payload['name']]
        result = []
        while not queue.empty():
            result.append(queue.get_nowait())
        return result
    if action == 'start_polling':
        await bot_manager.start_polling(bot_manager.get_bot(payload['name']))
        return True
    if action == 'stop':
        await bot_manager.stop_bot(payload['name'])
        events.pop(payload['name'], None)
        return True
    if action == 'webhook':
        instance = bot_manager.get_bot(payload['name'])
        update = Update.model_validate(payload['update'], context={'bot': instance.bot})
        # Webhook and polling are mutually exclusive for a configured bot.
        await instance.dispatcher.feed_update(instance.bot, update)
        return await dispatch({'action': 'events', 'name': payload['name']})
    if action not in ('method', 'raw', 'download'):
        raise ValueError('Unsupported Telegram worker action')
    async with Bot(payload['token'], default=DefaultBotProperties(parse_mode=payload.get('parse_mode'))) as bot:
        if action == 'download':
            data = io.BytesIO()
            await bot.download_file(payload['path'], data)
            return base64.b64encode(data.getvalue()).decode()
        if action == 'raw':
            if payload['method'] not in RAW_METHODS:
                raise ValueError('Unsupported Telegram method')
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"https://api.telegram.org/bot{payload['token']}/{payload['method']}",
                                        json=payload['kwargs']) as response:
                    return await response.json(content_type=None)
        if payload['method'] not in METHODS:
            raise ValueError('Unsupported Telegram method')
        kwargs = payload['kwargs']
        for key, value in list(kwargs.items()):
            if isinstance(value, dict) and set(value) == {'file_name', 'file_data'}:
                kwargs[key] = BufferedInputFile(base64.b64decode(value['file_data'], validate=True), filename=value['file_name'])
        try:
            return serialize(await getattr(bot, payload['method'])(**kwargs))
        except TelegramBadRequest:
            return {'telegram_bad_request': True}


def handle(payload):
    future = asyncio.run_coroutine_threadsafe(dispatch(payload), loop)
    try:
        return future.result(timeout=110)
    except Exception as exc:
        future.cancel()
        return {'transport_error': f'Telegram transport failed ({type(exc).__name__})'}
