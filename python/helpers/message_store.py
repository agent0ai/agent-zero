"""SQLite-backed message persistence for audit and replay.

Auto-creates the ``messages`` table on first use.  All writes go through
``store()``; reads via ``get_history()`` and ``replay()``.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from python.helpers.channel_bridge import NormalizedMessage

_DEFAULT_DB_PATH = os.getenv("MESSAGE_STORE_PATH", "data/message_store.db")

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id          TEXT PRIMARY KEY,
    channel     TEXT NOT NULL,
    sender_id   TEXT NOT NULL DEFAULT '',
    sender_name TEXT NOT NULL DEFAULT '',
    text        TEXT NOT NULL DEFAULT '',
    response    TEXT NOT NULL DEFAULT '',
    timestamp   REAL NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}',
    created_at  REAL NOT NULL
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_messages_channel_ts
    ON messages (channel, timestamp DESC);
"""


class MessageStore:
    """Thread-safe, SQLite-backed message log."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._ensure_tables()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def store(self, msg: NormalizedMessage, response: str = "") -> None:
        """Persist a message and its response."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO messages
                    (id, channel, sender_id, sender_name, text, response, timestamp, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg.id,
                    msg.channel,
                    msg.sender_id,
                    msg.sender_name,
                    msg.text,
                    response,
                    msg.timestamp,
                    json.dumps(msg.metadata),
                    time.time(),
                ),
            )

    def get_history(self, channel: str, limit: int = 50, before_ts: float | None = None) -> list[dict[str, Any]]:
        """Return the most recent messages for *channel*."""
        with self._connect() as conn:
            if before_ts is not None:
                rows = conn.execute(
                    """
                    SELECT id, channel, sender_id, sender_name, text, response,
                           timestamp, metadata, created_at
                    FROM messages
                    WHERE channel = ? AND timestamp < ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (channel, before_ts, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, channel, sender_id, sender_name, text, response,
                           timestamp, metadata, created_at
                    FROM messages
                    WHERE channel = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (channel, limit),
                ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def replay(self, message_id: str) -> NormalizedMessage | None:
        """Retrieve a stored message as a ``NormalizedMessage`` for reprocessing."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, channel, sender_id, sender_name, text, response,
                       timestamp, metadata, created_at
                FROM messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()
        if row is None:
            return None
        d = self._row_to_dict(row)
        return NormalizedMessage(
            id=d["id"],
            channel=d["channel"],
            sender_id=d["sender_id"],
            sender_name=d["sender_name"],
            text=d["text"],
            timestamp=d["timestamp"],
            metadata=d["metadata"],
        )

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_CREATE_TABLE_SQL + _CREATE_INDEX_SQL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        if isinstance(d.get("metadata"), str):
            d["metadata"] = json.loads(d["metadata"])
        return d
