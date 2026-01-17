import sqlite3
from datetime import datetime
from typing import Any


class TwilioVoiceDatabase:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_sid TEXT,
                    to_number TEXT NOT NULL,
                    from_number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    error TEXT
                )
                """
            )

    def add_call(self, to_number: str, from_number: str, message: str | None, status: str) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO calls (to_number, from_number, message, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (to_number, from_number, message, status, created_at),
            )
            return int(cursor.lastrowid)

    def update_call(
        self,
        call_id: int | None,
        call_sid: str | None,
        status: str,
        error: str | None = None,
    ) -> None:
        updated_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            if call_id is not None:
                conn.execute(
                    """
                    UPDATE calls
                    SET call_sid = COALESCE(call_sid, ?),
                        status = ?,
                        updated_at = ?,
                        error = ?
                    WHERE id = ?
                    """,
                    (call_sid, status, updated_at, error, call_id),
                )
                return
            if call_sid:
                conn.execute(
                    """
                    UPDATE calls
                    SET status = ?, updated_at = ?, error = ?
                    WHERE call_sid = ?
                    """,
                    (status, updated_at, error, call_sid),
                )

    def list_calls(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, call_sid, to_number, from_number, status, message, created_at, updated_at, error
                FROM calls
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "call_sid": row[1],
                "to_number": row[2],
                "from_number": row[3],
                "status": row[4],
                "message": row[5],
                "created_at": row[6],
                "updated_at": row[7],
                "error": row[8],
            }
            for row in rows
        ]
