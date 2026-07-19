import asyncio

from plugins._telegram_integration.helpers import handler
from plugins._telegram_integration.helpers import telegram_client as tc
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_REPLY_TO,
)


class FakeBotInstance:
    class Bot:
        token = "token"

    bot = Bot()


class FakeContext:
    def __init__(self):
        self.data = {
            CTX_TG_BOT: "main",
            CTX_TG_CHAT_ID: 123,
            CTX_TG_REPLY_TO: 456,
        }


class FakeTempBot:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeMediaBot:
    def __init__(self):
        self.calls = []

    async def send_voice(self, **kwargs):
        self.calls.append(("voice", kwargs))
        return type("Message", (), {"message_id": 11})()

    async def send_audio(self, **kwargs):
        self.calls.append(("audio", kwargs))
        return type("Message", (), {"message_id": 12})()

    async def send_video(self, **kwargs):
        self.calls.append(("video", kwargs))
        return type("Message", (), {"message_id": 13})()


def test_telegram_client_native_media_helpers(monkeypatch):
    bot = FakeMediaBot()
    monkeypatch.setattr(tc.os.path, "isfile", lambda path: True)

    voice_id = asyncio.run(tc.send_voice(bot, 123, "voice.ogg", reply_to_message_id=456))
    audio_id = asyncio.run(tc.send_audio(bot, 123, "song.mp3", reply_to_message_id=456))
    video_id = asyncio.run(tc.send_video(bot, 123, "clip.mp4", reply_to_message_id=456))

    assert (voice_id, audio_id, video_id) == (11, 12, 13)
    assert [kind for kind, _ in bot.calls] == ["voice", "audio", "video"]
    assert bot.calls[0][1]["chat_id"] == 123
    assert bot.calls[0][1]["reply_to_message_id"] == 456


def test_telegram_reply_routes_native_media_attachments(monkeypatch):
    calls = []

    def fake_temp_bot(*args, **kwargs):
        return FakeTempBot()

    async def record(kind, bot, chat_id, path, reply_to_message_id=None, **kwargs):
        calls.append(
            {
                "kind": kind,
                "chat_id": chat_id,
                "path": path,
                "reply_to_message_id": reply_to_message_id,
            }
        )
        return len(calls)

    monkeypatch.setattr(handler, "get_bot", lambda name: FakeBotInstance())
    monkeypatch.setattr(handler, "_temp_bot", fake_temp_bot)
    monkeypatch.setattr(handler.files, "fix_dev_path", lambda path: path)
    monkeypatch.setattr(handler.tc, "send_photo", lambda *a, **kw: record("photo", *a, **kw))
    monkeypatch.setattr(handler.tc, "send_voice", lambda *a, **kw: record("voice", *a, **kw))
    monkeypatch.setattr(handler.tc, "send_audio", lambda *a, **kw: record("audio", *a, **kw))
    monkeypatch.setattr(handler.tc, "send_video", lambda *a, **kw: record("video", *a, **kw))
    monkeypatch.setattr(handler.tc, "send_file", lambda *a, **kw: record("document", *a, **kw))

    error = asyncio.run(
        handler.send_telegram_reply(
            FakeContext(),
            "",
            ["image.png", "voice.ogg", "song.mp3", "clip.mp4", "archive.zip"],
        )
    )

    assert error is None
    assert calls == [
        {"kind": "photo", "chat_id": 123, "path": "image.png", "reply_to_message_id": 456},
        {"kind": "voice", "chat_id": 123, "path": "voice.ogg", "reply_to_message_id": 456},
        {"kind": "audio", "chat_id": 123, "path": "song.mp3", "reply_to_message_id": 456},
        {"kind": "video", "chat_id": 123, "path": "clip.mp4", "reply_to_message_id": 456},
        {"kind": "document", "chat_id": 123, "path": "archive.zip", "reply_to_message_id": 456},
    ]
