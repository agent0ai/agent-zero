import json
from types import SimpleNamespace

from python.api.google_voice_outbound_create import GoogleVoiceOutboundCreate
from python.api.google_voice_outbound_list import GoogleVoiceOutboundList


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_google_voice_outbound_create_and_list(tmp_path, monkeypatch):
    from python.helpers import files

    db_path = tmp_path / "google_voice.db"
    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    create_handler = GoogleVoiceOutboundCreate(SimpleNamespace(), SimpleNamespace())
    create_result = await create_handler.process(
        {"to_number": "+15551234567", "body": "Hello there"},
        DummyRequest({"to_number": "+15551234567", "body": "Hello there"}),
    )

    assert create_result["success"] is True
    assert create_result["message"]["status"] == "draft"

    list_handler = GoogleVoiceOutboundList(SimpleNamespace(), SimpleNamespace())
    list_result = await list_handler.process({}, DummyRequest({}))

    assert list_result["success"] is True
    assert len(list_result["messages"]) == 1
