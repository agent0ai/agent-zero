import sqlite3
from datetime import datetime
from typing import Any


class GoogleVoiceDatabase:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbound_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    to_number TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sent_at TEXT,
                    error TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inbound_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_number TEXT NOT NULL,
                    body TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    message_hash TEXT,
                    thread_context TEXT
                )
                """
            )
            self._ensure_columns(conn)

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(inbound_messages)").fetchall()}
        if "message_hash" not in existing:
            conn.execute("ALTER TABLE inbound_messages ADD COLUMN message_hash TEXT")
        if "thread_context" not in existing:
            conn.execute("ALTER TABLE inbound_messages ADD COLUMN thread_context TEXT")

    def add_outbound(self, to_number: str, body: str, status: str) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO outbound_messages (to_number, body, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (to_number, body, status, created_at),
            )
            return int(cursor.lastrowid)

    def list_outbound(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    """
                    SELECT id, to_number, body, status, created_at, sent_at, error
                    FROM outbound_messages
                    WHERE status = ?
                    ORDER BY id DESC
                    """,
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, to_number, body, status, created_at, sent_at, error
                    FROM outbound_messages
                    ORDER BY id DESC
                    """
                ).fetchall()
        return [
            {
                "id": row[0],
                "to_number": row[1],
                "body": row[2],
                "status": row[3],
                "created_at": row[4],
                "sent_at": row[5],
                "error": row[6],
            }
            for row in rows
        ]

    def update_outbound_status(
        self,
        message_id: int,
        status: str,
        sent_at: str | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE outbound_messages
                SET status = ?, sent_at = ?, error = ?
                WHERE id = ?
                """,
                (status, sent_at, error, message_id),
            )

    def add_inbound(
        self,
        from_number: str,
        body: str,
        received_at: str,
        message_hash: str,
        thread_context: str | None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inbound_messages (from_number, body, received_at, message_hash, thread_context)
                VALUES (?, ?, ?, ?, ?)
                """,
                (from_number, body, received_at, message_hash, thread_context),
            )
            return int(cursor.lastrowid)

    def list_inbound(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, from_number, body, received_at, message_hash, thread_context
                FROM inbound_messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "from_number": row[1],
                "body": row[2],
                "received_at": row[3],
                "message_hash": row[4],
                "thread_context": row[5],
            }
            for row in rows
        ]

    def has_inbound_hash(self, message_hash: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM inbound_messages WHERE message_hash = ? LIMIT 1",
                (message_hash,),
            ).fetchone()
        return row is not None
