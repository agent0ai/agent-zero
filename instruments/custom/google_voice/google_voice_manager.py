import hashlib
from datetime import datetime, timezone
from typing import Any

from instruments.custom.google_voice.google_voice_adapter import get_google_voice_session
from instruments.custom.google_voice.google_voice_db import GoogleVoiceDatabase
from python.helpers import files
from python.helpers.event_bus import EventBus, EventStore
from python.helpers.task_scheduler import PlannedTask, TaskPlan, TaskScheduler


class GoogleVoiceManager:
    def __init__(self, db_path: str):
        self.db = GoogleVoiceDatabase(db_path)
        self.user_data_dir = files.get_abs_path("./instruments/custom/google_voice/data/profile")
        self.event_store = EventStore(files.get_abs_path("./instruments/custom/google_voice/data/events.db"))
        self.event_bus = EventBus(self.event_store)

    async def start_session(self) -> dict[str, Any]:
        session = get_google_voice_session(self.user_data_dir, headless=False)
        await session.ensure()
        return {"status": "ready"}

    def draft_outbound(self, to_number: str, body: str) -> dict[str, Any]:
        message_id = self.db.add_outbound(to_number, body, status="draft")
        return {"id": message_id, "to_number": to_number, "body": body, "status": "draft"}

    def list_outbound(self, status: str | None = None) -> list[dict[str, Any]]:
        return self.db.list_outbound(status)

    async def approve_and_send(self, message_id: int) -> dict[str, Any]:
        messages = self.db.list_outbound()
        message = next((item for item in messages if item["id"] == message_id), None)
        if not message:
            return {"success": False, "error": "Message not found"}
        if message["status"] == "sent":
            return {"success": True, "message": message}

        self.db.update_outbound_status(message_id, "approved")
        session = get_google_voice_session(self.user_data_dir, headless=False)
        try:
            await session.send_sms(message["to_number"], message["body"])
        except Exception as exc:
            self.db.update_outbound_status(message_id, "failed", error=str(exc))
            return {"success": False, "error": str(exc)}

        sent_at = datetime.utcnow().isoformat()
        self.db.update_outbound_status(message_id, "sent", sent_at=sent_at)
        updated = {
            **message,
            "status": "sent",
            "sent_at": sent_at,
            "error": None,
        }
        await self.event_bus.emit(
            "google_voice.sms.sent",
            {
                "message_id": message_id,
                "to_number": message["to_number"],
                "body": message["body"],
                "sent_at": sent_at,
            },
        )
        return {"success": True, "message": updated}

    async def sync_inbound(self, limit: int = 10) -> dict[str, Any]:
        session = get_google_voice_session(self.user_data_dir, headless=False)
        items = await session.fetch_inbox(limit=limit)
        created: list[dict[str, Any]] = []
        for item in items:
            message_hash = hashlib.sha256(f"{item['from_number']}|{item['body']}".encode()).hexdigest()
            if self.db.has_inbound_hash(message_hash):
                continue
            received_at = datetime.utcnow().isoformat()
            thread_context = item.get("thread_context") if isinstance(item, dict) else None
            inbound_id = self.db.add_inbound(
                item["from_number"],
                item["body"],
                received_at,
                message_hash=message_hash,
                thread_context=thread_context if isinstance(thread_context, str) else None,
            )
            payload = {
                "id": inbound_id,
                "from_number": item["from_number"],
                "body": item["body"],
                "received_at": received_at,
                "message_hash": message_hash,
                "thread_context": thread_context,
            }
            created.append(payload)
            await self.event_bus.emit("google_voice.sms.inbound", payload)
            await self._create_followup_task(payload)
        return {"count": len(created), "items": created}

    def list_inbound(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.list_inbound(limit=limit)

    async def _create_followup_task(self, payload: dict[str, Any]) -> None:
        plan = TaskPlan.create(todo=[datetime.now(timezone.utc)])
        context = payload.get("thread_context") or payload.get("body")
        task = PlannedTask.create(
            name=f"Reply to SMS from {payload['from_number']}",
            system_prompt="You are a helpful assistant.",
            prompt=f"New SMS received:\n{context}",
            plan=plan,
            attachments=[],
        )
        await TaskScheduler.get().add_task(task, create_context=False)
