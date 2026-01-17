import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Any, Awaitable, Callable

from python.helpers.audit import hash_event

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def add_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        created_at = datetime.utcnow().isoformat()
        event_hash = hash_event(event_type, payload)
        payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (type, payload, event_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_type, payload_json, event_hash, created_at),
            )
            event_id = int(cursor.lastrowid)
        return {
            "id": event_id,
            "type": event_type,
            "payload": payload,
            "event_hash": event_hash,
            "created_at": created_at,
        }

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, type, payload, event_hash, created_at
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "type": row[1],
                "payload": json.loads(row[2]),
                "event_hash": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]


class EventBus:
    def __init__(self, store: EventStore):
        self.store = store
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = self.store.add_event(event_type, payload)
        handlers = list(self._handlers.get(event_type, [])) + list(self._handlers.get("*", []))
        for handler in handlers:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        return event
