import copy
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sentence_transformers = types.ModuleType("sentence_transformers")
sentence_transformers.SentenceTransformer = object
sys.modules.setdefault("sentence_transformers", sentence_transformers)

from api.message import Message
from helpers import message_queue


class _Request:
    content_type = "application/json"

    @staticmethod
    def get_json():
        return {
            "text": "keep this message",
            "context": "chat-1",
            "message_id": "message-1",
        }


class _Log:
    def log(self, **_kwargs):
        return None


class _Context:
    def __init__(self):
        self.id = "chat-1"
        self.data = {}
        self.output_data = {}
        self.log = _Log()
        self.communicated = []

    def get_agent(self):
        return object()

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value

    def set_output_data(self, key, value):
        self.output_data[key] = value

    def communicate(self, message):
        self.communicated.append(message)
        return "task"


@pytest.mark.asyncio
async def test_user_message_is_persisted_as_pending_before_dispatch(monkeypatch):
    from api import message as message_api

    context = _Context()
    handler = Message.__new__(Message)
    handler.use_context = lambda _context_id: context
    events = []
    persisted_queue = []

    async def no_extensions(*_args, **_kwargs):
        return None

    def save_chat(saved_context):
        events.append("persisted")
        persisted_queue.extend(copy.deepcopy(message_queue.get_queue(saved_context)))

    def communicate(message):
        events.append("dispatched")
        context.communicated.append(message)
        return "task"

    monkeypatch.setattr(message_api.extension, "call_extensions_async", no_extensions)
    monkeypatch.setattr(message_api.persist_chat, "save_tmp_chat", save_chat)
    monkeypatch.setattr(context, "communicate", communicate)

    task, returned_context = await handler.communicate({}, _Request())

    assert task == "task"
    assert returned_context is context
    assert events == ["persisted", "dispatched"]
    assert persisted_queue == [
        {
            "id": "message-1",
            "seq": 1,
            "text": "keep this message",
            "attachments": [],
        }
    ]
    assert message_queue.get_queue(context) == []
    assert context.communicated[0].id == "message-1"
