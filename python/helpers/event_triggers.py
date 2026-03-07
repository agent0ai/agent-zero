"""Event-driven heartbeat trigger system.

Provides trigger types, the HeartbeatTrigger dataclass, and SQLite-backed
persistence for registering triggers that fire on system events, webhooks,
conditions, messages, or cron schedules.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from python.helpers import files


class TriggerType(Enum):
    CRON = "cron"
    EVENT = "event"
    WEBHOOK = "webhook"
    CONDITION = "condition"
    MESSAGE = "message"


@dataclass
class HeartbeatTrigger:
    id: str
    type: TriggerType
    config: dict[str, Any]
    items: list[dict[str, Any]]
    enabled: bool = True
    last_triggered: datetime | None = None
    trigger_count: int = 0

    @staticmethod
    def new(
        trigger_type: TriggerType,
        config: dict[str, Any],
        items: list[dict[str, Any]],
        *,
        enabled: bool = True,
    ) -> HeartbeatTrigger:
        return HeartbeatTrigger(
            id=uuid.uuid4().hex,
            type=trigger_type,
            config=config,
            items=items,
            enabled=enabled,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "config": self.config,
            "items": self.items,
            "enabled": self.enabled,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeartbeatTrigger:
        lt = data.get("last_triggered")
        return cls(
            id=data["id"],
            type=TriggerType(data["type"]),
            config=data.get("config", {}),
            items=data.get("items", []),
            enabled=bool(data.get("enabled", True)),
            last_triggered=datetime.fromisoformat(lt) if lt else None,
            trigger_count=int(data.get("trigger_count", 0)),
        )


# ---------------------------------------------------------------------------
# SQLite-backed trigger persistence
# ---------------------------------------------------------------------------

_DEFAULT_DB = "data/heartbeat_triggers.db"


class TriggerStore:
    """SQLite-backed trigger persistence."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or files.get_abs_path(_DEFAULT_DB)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heartbeat_triggers (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    items TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_triggered TEXT,
                    trigger_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def save(self, trigger: HeartbeatTrigger) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO heartbeat_triggers
                    (id, type, config, items, enabled, last_triggered, trigger_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trigger.id,
                    trigger.type.value,
                    json.dumps(trigger.config),
                    json.dumps(trigger.items),
                    int(trigger.enabled),
                    trigger.last_triggered.isoformat() if trigger.last_triggered else None,
                    trigger.trigger_count,
                ),
            )

    def get(self, trigger_id: str) -> HeartbeatTrigger | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, type, config, items, enabled, last_triggered, trigger_count "
                "FROM heartbeat_triggers WHERE id = ?",
                (trigger_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_trigger(row)

    def list_all(self) -> list[HeartbeatTrigger]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, type, config, items, enabled, last_triggered, trigger_count "
                "FROM heartbeat_triggers ORDER BY id"
            ).fetchall()
        return [self._row_to_trigger(r) for r in rows]

    def delete(self, trigger_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM heartbeat_triggers WHERE id = ?", (trigger_id,))

    def update_last_triggered(self, trigger_id: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE heartbeat_triggers SET last_triggered = ?, trigger_count = trigger_count + 1 WHERE id = ?",
                (now, trigger_id),
            )

    @staticmethod
    def _row_to_trigger(row: tuple) -> HeartbeatTrigger:
        return HeartbeatTrigger(
            id=row[0],
            type=TriggerType(row[1]),
            config=json.loads(row[2]),
            items=json.loads(row[3]),
            enabled=bool(row[4]),
            last_triggered=datetime.fromisoformat(row[5]) if row[5] else None,
            trigger_count=int(row[6]),
        )


# ---------------------------------------------------------------------------
# Trigger evaluation helpers
# ---------------------------------------------------------------------------


def evaluate_event_trigger(trigger: HeartbeatTrigger, event_type: str, payload: dict) -> bool:
    """Return True if an EVENT trigger matches the given event."""
    if trigger.type != TriggerType.EVENT or not trigger.enabled:
        return False
    pattern = trigger.config.get("event_type", "")
    if pattern == "*":
        return True
    return event_type == pattern


def evaluate_condition_trigger(trigger: HeartbeatTrigger, metrics: dict[str, Any]) -> bool:
    """Return True if a CONDITION trigger is satisfied by the given metrics."""
    if trigger.type != TriggerType.CONDITION or not trigger.enabled:
        return False
    metric_name = trigger.config.get("metric")
    threshold = trigger.config.get("threshold")
    operator = trigger.config.get("operator", ">=")
    if metric_name is None or threshold is None:
        return False
    value = metrics.get(metric_name)
    if value is None:
        return False
    ops = {
        ">=": lambda a, b: a >= b,
        ">": lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        "<": lambda a, b: a < b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    return ops.get(operator, lambda a, b: False)(value, threshold)


def evaluate_message_trigger(trigger: HeartbeatTrigger, message_text: str) -> bool:
    """Return True if a MESSAGE trigger matches the given message text."""
    if trigger.type != TriggerType.MESSAGE or not trigger.enabled:
        return False
    import re

    pattern = trigger.config.get("pattern", "")
    if not pattern:
        return False
    try:
        return bool(re.search(pattern, message_text, re.IGNORECASE))
    except re.error:
        return False
