from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict
from typing import Any, Iterable

from python.helpers import memory as memory_helper
from agent import Agent

from .schemas import Persona, UserProfile, SurveyField


def _now_ts() -> int:
    return int(time.time())


class SurveyDB:
    """Structured persistence for personas, profiles, and survey answers."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._init_schema()

    @staticmethod
    def for_agent(agent: Agent) -> "SurveyDB":
        base = memory_helper.get_memory_subdir_abs(agent)
        path = os.path.join(base, "survey_profiles.db")
        return SurveyDB(path)

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS personas (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT NOT NULL,
              constraints_json TEXT NOT NULL,
              created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profiles (
              id TEXT PRIMARY KEY,
              persona_id TEXT NULL REFERENCES personas(id) ON DELETE SET NULL,
              data_json TEXT NOT NULL,
              updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS survey_sessions (
              id TEXT PRIMARY KEY,
              url TEXT NOT NULL,
              persona_id TEXT NULL REFERENCES personas(id) ON DELETE SET NULL,
              profile_id TEXT NULL REFERENCES profiles(id) ON DELETE SET NULL,
              started_at INTEGER NOT NULL,
              completed_at INTEGER NULL,
              status TEXT NOT NULL,
              notes TEXT NULL
            );

            CREATE TABLE IF NOT EXISTS survey_answers (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
              question_text TEXT NULL,
              field_kind TEXT NOT NULL,
              selector TEXT NULL,
              answer_text TEXT NOT NULL,
              field_json TEXT NOT NULL,
              raw_json TEXT NULL,
              processed INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_survey_answers_processed
              ON survey_answers(processed, created_at);
            """
        )
        self._conn.commit()

    # ---- Persona/profile API -------------------------------------------------

    def upsert_persona(self, persona: Persona) -> None:
        self._conn.execute(
            """
            INSERT INTO personas(id, name, description, constraints_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name,
              description=excluded.description,
              constraints_json=excluded.constraints_json;
            """,
            (
                persona.id,
                persona.name,
                persona.description,
                json.dumps(persona.constraints or {}, ensure_ascii=False),
                _now_ts(),
            ),
        )
        self._conn.commit()

    def get_persona(self, persona_id: str) -> Persona | None:
        row = self._conn.execute(
            "SELECT id, name, description, constraints_json FROM personas WHERE id=?",
            (persona_id,),
        ).fetchone()
        if not row:
            return None
        return Persona(
            id=row[0],
            name=row[1],
            description=row[2],
            constraints=json.loads(row[3] or "{}"),
        )

    def upsert_profile(self, profile: UserProfile) -> None:
        self._conn.execute(
            """
            INSERT INTO profiles(id, persona_id, data_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              persona_id=excluded.persona_id,
              data_json=excluded.data_json,
              updated_at=excluded.updated_at;
            """,
            (
                profile.id,
                profile.persona_id,
                json.dumps(profile.data or {}, ensure_ascii=False),
                _now_ts(),
            ),
        )
        self._conn.commit()

    def get_profile(self, profile_id: str) -> UserProfile | None:
        row = self._conn.execute(
            "SELECT id, persona_id, data_json FROM profiles WHERE id=?", (profile_id,)
        ).fetchone()
        if not row:
            return None
        return UserProfile(
            id=row[0],
            persona_id=row[1],
            data=json.loads(row[2] or "{}"),
        )

    # ---- Survey session/answers API -----------------------------------------

    def create_session(
        self,
        session_id: str,
        url: str,
        persona_id: str | None,
        profile_id: str | None,
        status: str = "running",
        notes: str | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO survey_sessions(id, url, persona_id, profile_id, started_at, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, url, persona_id, profile_id, _now_ts(), status, notes),
        )
        self._conn.commit()

    def complete_session(self, session_id: str, status: str = "completed") -> None:
        self._conn.execute(
            """
            UPDATE survey_sessions
            SET completed_at=?, status=?
            WHERE id=?
            """,
            (_now_ts(), status, session_id),
        )
        self._conn.commit()

    def insert_answer(
        self,
        answer_id: str,
        session_id: str,
        question_text: str | None,
        field: SurveyField,
        answer_text: str,
        raw: dict[str, Any] | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO survey_answers(
              id, session_id, question_text, field_kind, selector, answer_text,
              field_json, raw_json, processed, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                answer_id,
                session_id,
                question_text,
                field.kind.value,
                field.selector,
                answer_text,
                json.dumps(asdict(field), ensure_ascii=False),
                json.dumps(raw, ensure_ascii=False) if raw else None,
                _now_ts(),
            ),
        )
        self._conn.commit()

    def fetch_unprocessed_answers(
        self, limit: int = 200
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, session_id, question_text, field_kind, selector, answer_text, field_json, raw_json, created_at
            FROM survey_answers
            WHERE processed=0
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "session_id": row[1],
                    "question_text": row[2],
                    "field_kind": row[3],
                    "selector": row[4],
                    "answer_text": row[5],
                    "field": json.loads(row[6] or "{}"),
                    "raw": json.loads(row[7]) if row[7] else None,
                    "created_at": row[8],
                }
            )
        return results

    def fetch_unprocessed_answer_events(self, limit: int = 200) -> list[dict[str, Any]]:
        """Fetch unprocessed answers with session context (url/profile/persona)."""
        rows = self._conn.execute(
            """
            SELECT
              a.id, a.session_id, a.question_text, a.field_kind, a.selector, a.answer_text,
              a.field_json, a.raw_json, a.created_at,
              s.url, s.persona_id, s.profile_id
            FROM survey_answers a
            JOIN survey_sessions s ON s.id = a.session_id
            WHERE a.processed=0
            ORDER BY a.created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "session_id": row[1],
                    "question_text": row[2],
                    "field_kind": row[3],
                    "selector": row[4],
                    "answer_text": row[5],
                    "field": json.loads(row[6] or "{}"),
                    "raw": json.loads(row[7]) if row[7] else None,
                    "created_at": row[8],
                    "url": row[9],
                    "persona_id": row[10],
                    "profile_id": row[11],
                }
            )
        return results

    def mark_answers_processed(self, answer_ids: Iterable[str]) -> None:
        ids = list(answer_ids)
        if not ids:
            return
        cur = self._conn.cursor()
        cur.executemany(
            "UPDATE survey_answers SET processed=1 WHERE id=?",
            [(i,) for i in ids],
        )
        self._conn.commit()

