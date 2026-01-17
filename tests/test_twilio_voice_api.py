import json
from types import SimpleNamespace

from python.api.twilio_voice_call import TwilioVoiceCall
from python.api.twilio_voice_list import TwilioVoiceList


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_twilio_voice_call_and_list(tmp_path, monkeypatch):
    from python.helpers import files

    db_path = tmp_path / "twilio_voice.db"
    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    call_handler = TwilioVoiceCall(SimpleNamespace(), SimpleNamespace())
    call_result = await call_handler.process(
        {"to_number": "+15551234567", "message": "Hello", "mock": True},
        DummyRequest({"to_number": "+15551234567", "message": "Hello", "mock": True}),
    )

    assert call_result["success"] is True

    list_handler = TwilioVoiceList(SimpleNamespace(), SimpleNamespace())
    list_result = await list_handler.process({}, DummyRequest({}))

    assert list_result["success"] is True
    assert len(list_result["calls"]) == 1
