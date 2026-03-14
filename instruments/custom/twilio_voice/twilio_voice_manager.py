import base64
import json
import urllib.request
from typing import Any

from instruments.custom.twilio_voice.twilio_voice_db import TwilioVoiceDatabase
from python.helpers import files
from python.helpers.event_bus import EventBus, EventStore
from python.helpers.settings import get_settings


class TwilioVoiceManager:
    def __init__(self, db_path: str):
        self.db = TwilioVoiceDatabase(db_path)
        self.event_store = EventStore(files.get_abs_path("./instruments/custom/twilio_voice/data/events.db"))
        self.event_bus = EventBus(self.event_store)

    def list_calls(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.list_calls(limit=limit)

    def _get_credentials(self) -> tuple[str, str, str]:
        try:
            settings = get_settings()
        except Exception:
            settings = {}
        sid = settings.get("twilio_account_sid", "")
        token = settings.get("twilio_auth_token", "")
        from_number = settings.get("twilio_from_number", "")
        return sid, token, from_number

    def _build_twiml(self, message: str | None) -> str:
        text = message or "Hello from Agent Jumbo."
        return f"<Response><Say>{text}</Say></Response>"

    async def create_call(
        self,
        to_number: str,
        message: str | None = None,
        from_number: str | None = None,
        mock: bool = False,
    ) -> dict[str, Any]:
        sid, token, default_from = self._get_credentials()
        from_number = from_number or default_from
        call_id = self.db.add_call(to_number, from_number or "", message, status="queued")

        if mock or not (sid and token and from_number):
            await self.event_bus.emit(
                "twilio.voice.call_mocked",
                {
                    "call_id": call_id,
                    "to_number": to_number,
                    "from_number": from_number,
                    "message": message,
                },
            )
            return {"success": True, "id": call_id, "status": "queued", "mock": True}

        payload = {
            "To": to_number,
            "From": from_number,
            "Twiml": self._build_twiml(message),
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        auth = base64.b64encode(f"{sid}:{token}".encode()).decode("ascii")
        request = urllib.request.Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
            data=data,
            headers={"Authorization": f"Basic {auth}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310
                body = response.read().decode("utf-8")
            payload = json.loads(body)
            call_sid = payload.get("sid")
            status = payload.get("status", "queued")
            self.db.update_call(call_id, call_sid, status)
            await self.event_bus.emit(
                "twilio.voice.call_started",
                {
                    "call_id": call_id,
                    "call_sid": call_sid,
                    "to_number": to_number,
                    "from_number": from_number,
                    "status": status,
                },
            )
            return {"success": True, "id": call_id, "call_sid": call_sid, "status": status}
        except Exception as exc:
            self.db.update_call(call_id, None, "failed", error=str(exc))
            await self.event_bus.emit(
                "twilio.voice.call_failed",
                {
                    "call_id": call_id,
                    "to_number": to_number,
                    "from_number": from_number,
                    "error": str(exc),
                },
            )
            return {"success": False, "error": str(exc)}

    async def update_status(self, call_sid: str, status: str) -> None:
        self.db.update_call(None, call_sid, status)
        await self.event_bus.emit(
            "twilio.voice.call_status",
            {"call_sid": call_sid, "status": status},
        )
