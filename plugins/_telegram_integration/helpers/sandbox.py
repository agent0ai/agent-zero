"""Small Telegram control/data types; no transport SDK in the outer runtime."""
import asyncio
import base64
from pathlib import Path
from helpers.sandbox_worker import SandboxWorker

worker = SandboxWorker('_telegram_integration', idle_seconds=None)


async def rpc(payload):
    # A cancelled control request must not terminate other bots in the shared guest.
    task = asyncio.create_task(worker.acall(payload))
    try:
        result = await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.gather(task, return_exceptions=True)
        raise
    if isinstance(result, dict) and 'transport_error' in result:
        raise RuntimeError(result['transport_error'])
    return result


class TelegramBadRequest(Exception):
    pass


class TelegramEvent:
    def __init__(self, value, bot):
        self._value, self._bot = value, bot

    def __getattr__(self, name):
        value = self._value.get('from' if name == 'from_user' else name)
        return decode(value, self._bot)

    async def reply(self, text):
        return await self._bot.send_message(chat_id=self.chat.id, text=text,
                                            reply_to_message_id=self.message_id)

    async def answer(self, text=''):
        return await self._bot.answer_callback_query(callback_query_id=self.id, text=text)


def decode(value, bot):
    if isinstance(value, dict):
        return TelegramEvent(value, bot)
    if isinstance(value, list):
        return [decode(item, bot) for item in value]
    return value


def buffered_file(data, filename):
    return {'file_name': filename, 'file_data': base64.b64encode(data).decode()}


def input_file(path):
    return buffered_file(Path(path).read_bytes(), Path(path).name)


class Bot:
    def __init__(self, token, *, parse_mode=None):
        self.token, self.parse_mode = token, parse_mode
        self.session = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        pass  # Each guest request closes its transport session.

    def __getattr__(self, method):
        async def invoke(**kwargs):
            result = await rpc({'action': 'method', 'method': method, 'token': self.token,
                                         'parse_mode': self.parse_mode, 'kwargs': kwargs})
            if isinstance(result, dict) and result.get('telegram_bad_request'):
                raise TelegramBadRequest('Telegram rejected the request')
            return decode(result, self)
        return invoke

    async def download_file(self, path, destination):
        data = await rpc({'action': 'download', 'token': self.token, 'path': path})
        Path(destination).write_bytes(base64.b64decode(data, validate=True))
