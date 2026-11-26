from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import files


_SESSION_SECONDS = 24 * 60 * 60
_USERNAME = re.compile(r"[a-z0-9][a-z0-9_.-]{0,63}", re.ASCII)
ADMIN_ACTOR_ID = "admin"

_SCHEMA = """
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1))
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_account ON sessions(account_id);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    native_name TEXT NOT NULL,
    retired INTEGER NOT NULL DEFAULT 0 CHECK (retired IN (0, 1))
);
CREATE UNIQUE INDEX IF NOT EXISTS active_project_name ON projects(native_name) WHERE retired = 0;
CREATE TABLE IF NOT EXISTS memberships (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    PRIMARY KEY (account_id, project_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY,
    happened_at INTEGER NOT NULL DEFAULT (unixepoch()),
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    account_id TEXT REFERENCES accounts(id),
    project_id TEXT REFERENCES projects(id)
);
CREATE TABLE IF NOT EXISTS team_runs (
    id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    project_id TEXT NOT NULL REFERENCES projects(id),
    account_id TEXT NOT NULL REFERENCES accounts(id),
    request_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    runtime_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('starting', 'running', 'stopping', 'completed', 'failed', 'stopped', 'interrupted')),
    accepting_queue INTEGER NOT NULL DEFAULT 1,
    began_at INTEGER NOT NULL DEFAULT (unixepoch()),
    finished_at INTEGER,
    UNIQUE (context_id, account_id, request_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_run_per_chat ON team_runs(context_id)
    WHERE state IN ('starting', 'running', 'stopping');
CREATE TABLE IF NOT EXISTS team_queue_items (
    seq INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES team_runs(id),
    item_id TEXT NOT NULL,
    text TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'queued' CHECK (state IN ('queued', 'taken', 'removed', 'cancelled')),
    interject INTEGER NOT NULL DEFAULT 0,
    UNIQUE (run_id, item_id)
);
CREATE INDEX IF NOT EXISTS team_queue_pending ON team_queue_items(run_id, state, seq);
CREATE TABLE IF NOT EXISTS team_audit_grants (
    actor_id TEXT NOT NULL,
    project_id TEXT NOT NULL REFERENCES projects(id),
    transcript INTEGER NOT NULL CHECK (transcript IN (0, 1)),
    PRIMARY KEY (actor_id, project_id)
);
COMMIT;
"""

_ACTIVE_RUN = "state IN ('starting', 'running', 'stopping')"
_RUN_SELECT = """SELECT team_runs.*, accounts.username FROM team_runs
                 JOIN accounts ON accounts.id = team_runs.account_id"""


@dataclass(frozen=True)
class TeamAccount:
    id: str
    username: str
    enabled: bool


@dataclass(frozen=True)
class TeamRun:
    id: str
    context_id: str
    project_id: str
    account_id: str
    username: str
    request_id: str
    state: str
    kind: str = "message"

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TeamRun":
        return cls(row["id"], row["context_id"], row["project_id"], row["account_id"],
                   row["username"], row["request_id"], row["state"], row["kind"])


class ActiveRunConflict(ValueError):
    def __init__(self, run: TeamRun):
        super().__init__(f"{run.username} is holding this chat ({run.state}).")
        self.run = run


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not _USERNAME.fullmatch(username):
        raise ValueError("Use 1 to 64 letters, numbers, dots, underscores or hyphens for the username.")
    return username


def _password_hash(password: str) -> str:
    if not 12 <= len(password) <= 256:
        raise ValueError("Use a password between 12 and 256 characters.")
    return generate_password_hash(password)


def _session_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TeamStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.parent.is_symlink():
            raise ValueError("The team database needs a local storage directory.")
        os.close(os.open(path, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600))
        with closing(self._connect()) as db:
            db.executescript(_SCHEMA)
        with self._write() as db:
            db.execute(
                "INSERT OR IGNORE INTO accounts(id, username, password_hash, enabled) VALUES (?, ?, '', 0)",
                (ADMIN_ACTOR_ID, "Platform administrator"),
            )
            columns = {row["name"] for row in db.execute("PRAGMA table_info(audit_events)")}
            for column in ("context_id", "run_id", "result"):
                if column not in columns:
                    db.execute(f"ALTER TABLE audit_events ADD COLUMN {column} TEXT")
            run_columns = {row["name"] for row in db.execute("PRAGMA table_info(team_runs)")}
            if "accepting_queue" not in run_columns:
                db.execute("ALTER TABLE team_runs ADD COLUMN accepting_queue INTEGER NOT NULL DEFAULT 1")
            if "kind" not in run_columns:
                db.execute("ALTER TABLE team_runs ADD COLUMN kind TEXT NOT NULL DEFAULT 'message'")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            yield db

    @staticmethod
    def _audit(db: sqlite3.Connection, action: str, actor_id: str, *,
               account_id: str | None = None, project_id: str | None = None,
               context_id: str | None = None, run_id: str | None = None, result: str | None = None) -> int:
        cursor = db.execute(
            """INSERT INTO audit_events(action, actor_id, account_id, project_id, context_id, run_id, result)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (action, actor_id, account_id, project_id, context_id, run_id, result),
        )
        return cursor.lastrowid

    def start_project_activity(self, action: str, actor_id: str, project_id: str,
                               *, context_id: str | None = None) -> int:
        with self._write() as db:
            return self._audit(db, action, actor_id, project_id=project_id, context_id=context_id, result="started")

    def finish_project_activity(self, event_id: int, result: str) -> None:
        with self._write() as db:
            db.execute("UPDATE audit_events SET result = ? WHERE id = ? AND result = 'started'", (result, event_id))

    @staticmethod
    def _current_project_member(db: sqlite3.Connection, account_id: str, project_id: str) -> bool:
        return bool(db.execute(
            """SELECT 1 FROM memberships
               JOIN accounts ON accounts.id = memberships.account_id AND accounts.enabled = 1
               JOIN projects ON projects.id = memberships.project_id AND projects.retired = 0
               WHERE memberships.account_id = ? AND memberships.project_id = ?""",
            (account_id, project_id),
        ).fetchone())

    def set_audit_grant(self, recipient: str, project_id: str, permission: str) -> None:
        if permission not in ("none", "events", "transcript"):
            raise ValueError("Choose an audit permission.")
        with self._write() as db:
            if recipient != "admin" and not self._current_project_member(db, recipient, project_id):
                raise ValueError("Assign this member to the project before granting audit access.")
            if permission == "none":
                db.execute("DELETE FROM team_audit_grants WHERE actor_id = ? AND project_id = ?", (recipient, project_id))
            else:
                db.execute(
                    """INSERT INTO team_audit_grants(actor_id, project_id, transcript) VALUES (?, ?, ?)
                       ON CONFLICT(actor_id, project_id) DO UPDATE SET transcript = excluded.transcript""",
                    (recipient, project_id, permission == "transcript"),
                )
            self._audit(db, "audit.grant", "admin", account_id=recipient if recipient != "admin" else None,
                        project_id=project_id, result=permission)

    def audit_grants(self, actor_id: str | None = None) -> list[dict]:
        with closing(self._connect()) as db:
            rows = db.execute(
                """SELECT g.actor_id, g.project_id, g.transcript, p.native_name AS name
                   FROM team_audit_grants AS g JOIN projects AS p ON p.id = g.project_id
                   WHERE p.retired = 0 AND (? IS NULL OR g.actor_id = ?)
                   ORDER BY p.native_name, g.actor_id""",
                (actor_id, actor_id),
            ).fetchall()
            return [{**dict(row), "transcript": bool(row["transcript"])} for row in rows
                    if row["actor_id"] == "admin" or self._current_project_member(db, row["actor_id"], row["project_id"])]

    def audit_projects(self) -> list[dict]:
        with closing(self._connect()) as db:
            return [dict(row) for row in db.execute("SELECT id, native_name AS name, retired FROM projects ORDER BY native_name, retired")]

    def audit_project_accounts(self, project_ids: list[str]) -> list[TeamAccount]:
        if not project_ids:
            return []
        placeholders = ",".join("?" for _ in project_ids)
        with closing(self._connect()) as db:
            rows = db.execute(
                f"""SELECT DISTINCT a.id, a.username, a.enabled FROM accounts a JOIN memberships m ON a.id = m.account_id
                    WHERE m.project_id IN ({placeholders}) ORDER BY a.username""",
                project_ids,
            )
            return [TeamAccount(row["id"], row["username"], bool(row["enabled"])) for row in rows]

    def authorize_transcript(self, actor_id: str, project_id: str, context_id: str) -> bool:
        with self._write() as db:
            granted = bool(db.execute(
                """SELECT 1 FROM team_audit_grants
                   WHERE actor_id = ? AND project_id = ? AND transcript = 1""",
                (actor_id, project_id),
            ).fetchone())
            if actor_id != "admin":
                granted = granted and self._current_project_member(db, actor_id, project_id)
            self._audit(db, "transcript.view", actor_id, project_id=project_id, context_id=context_id,
                        result="ok" if granted else "denied")
            return granted

    def audit_events(self, actor_id: str, filters: dict, project_ids: list[str] | None) -> dict:
        conditions, parameters = [], []
        if project_ids is not None:
            ids = ",".join("?" for _ in project_ids)
            conditions.append(
                f"""e.project_id IN ({ids}) AND EXISTS (
                    SELECT 1 FROM team_audit_grants g
                    JOIN memberships m ON m.account_id = g.actor_id AND m.project_id = g.project_id
                    JOIN accounts am ON am.id = m.account_id AND am.enabled = 1
                    JOIN projects ap ON ap.id = m.project_id AND ap.retired = 0
                    WHERE g.actor_id = ? AND g.project_id = e.project_id)""")
            parameters.extend([*project_ids, actor_id])
        if account_id := filters.get("account_id"):
            conditions.append("(e.actor_id = ? OR e.account_id = ?)")
            parameters.extend((account_id, account_id))
        for key, expression in (
            ("project_id", "e.project_id = ?"), ("context_id", "e.context_id = ?"), ("action", "e.action = ?"),
            ("from", "e.happened_at >= ?"), ("until", "e.happened_at <= ?"), ("before_id", "e.id < ?"),
        ):
            if key in filters:
                conditions.append(expression)
                parameters.append(filters[key])
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        with closing(self._connect()) as db:
            rows = db.execute(
                f"""SELECT e.*, a.username AS actor_name, b.username AS account_name, p.native_name AS project
                    FROM audit_events e LEFT JOIN accounts a ON a.id = e.actor_id
                    LEFT JOIN accounts b ON b.id = e.account_id LEFT JOIN projects p ON p.id = e.project_id
                    {where} ORDER BY e.id DESC LIMIT 101""",
                parameters,
            ).fetchall()
        return {"events": [dict(row) for row in rows[:100]], "before_id": rows[99]["id"] if len(rows) > 100 else None}

    def create_account(self, username: str, password: str, *, actor_id: str) -> TeamAccount:
        account = TeamAccount(uuid4().hex, normalize_username(username), True)
        password_hash = _password_hash(password)
        with self._write() as db:
            if db.execute("SELECT 1 FROM accounts WHERE username = ?", (account.username,)).fetchone():
                raise ValueError("That username is already in use.")
            db.execute(
                "INSERT INTO accounts(id, username, password_hash) VALUES (?, ?, ?)",
                (account.id, account.username, password_hash),
            )
            self._audit(db, "account.create", actor_id, account_id=account.id)
        return account

    def list_accounts(self) -> list[TeamAccount]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT id, username, enabled FROM accounts WHERE id != ? ORDER BY username", (ADMIN_ACTOR_ID,)).fetchall()
        return [TeamAccount(row["id"], row["username"], bool(row["enabled"])) for row in rows]

    def set_account_enabled(self, account_id: str, enabled: bool, *, actor_id: str) -> None:
        with self._write() as db:
            changed = db.execute("UPDATE accounts SET enabled = ? WHERE id = ? AND id != ?", (enabled, account_id, ADMIN_ACTOR_ID))
            if not changed.rowcount:
                raise ValueError("Account not found.")
            if not enabled:
                db.execute("DELETE FROM sessions WHERE account_id = ?", (account_id,))
            action = "account.enable" if enabled else "account.disable"
            self._audit(db, action, actor_id, account_id=account_id)

    def reset_password(self, account_id: str, password: str, *, actor_id: str) -> None:
        password_hash = _password_hash(password)
        with self._write() as db:
            changed = db.execute("UPDATE accounts SET password_hash = ? WHERE id = ? AND id != ?", (password_hash, account_id, ADMIN_ACTOR_ID))
            if not changed.rowcount:
                raise ValueError("Account not found.")
            db.execute("DELETE FROM sessions WHERE account_id = ?", (account_id,))
            self._audit(db, "account.password_reset", actor_id, account_id=account_id)

    def sign_in(self, username: str, password: str) -> str | None:
        if len(username) > 64 or len(password) > 256:
            return None
        with closing(self._connect()) as db:
            account = db.execute(
                "SELECT id, password_hash FROM accounts WHERE username = ? AND enabled = 1",
                (username.strip().lower(),),
            ).fetchone()
        if account is None or not check_password_hash(account["password_hash"], password):
            return None

        token = secrets.token_urlsafe(32)
        now = int(time.time())
        with self._write() as db:
            db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            # Recheck the original hash under the write lock in case a reset raced the password check.
            result = db.execute(
                """INSERT INTO sessions(token_hash, account_id, expires_at)
                   SELECT ?, id, ? FROM accounts WHERE id = ? AND password_hash = ? AND enabled = 1""",
                (_session_hash(token), now + _SESSION_SECONDS, account["id"], account["password_hash"]),
            )
            if result.rowcount == 0:
                return None
        return token

    def account_for_session(self, token: str) -> TeamAccount | None:
        if len(token) != 43:
            return None
        with closing(self._connect()) as db:
            row = db.execute(
                """SELECT accounts.id, accounts.username FROM sessions
                   JOIN accounts ON accounts.id = sessions.account_id
                   WHERE token_hash = ? AND expires_at > ? AND enabled = 1""",
                (_session_hash(token), int(time.time())),
            ).fetchone()
        return TeamAccount(row["id"], row["username"], True) if row else None

    def revoke_session(self, token: str) -> None:
        with self._write() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (_session_hash(token),))

    def project_id(self, native_name: str) -> str | None:
        with closing(self._connect()) as db:
            row = db.execute(
                "SELECT id FROM projects WHERE native_name = ? AND retired = 0", (native_name,),
            ).fetchone()
        return row["id"] if row else None

    def project_has_predecessor(self, native_name: str) -> bool:
        with closing(self._connect()) as db:
            return db.execute(
                "SELECT 1 FROM projects WHERE native_name = ? AND retired = 1 LIMIT 1", (native_name,),
            ).fetchone() is not None

    def bind_project(self, native_name: str, project_id: str) -> None:
        with self._write() as db:
            db.execute("UPDATE projects SET retired = 1 WHERE native_name = ? AND retired = 0", (native_name,))
            db.execute("INSERT INTO projects(id, native_name) VALUES (?, ?)", (project_id, native_name))

    def set_membership(self, account_id: str, project_id: str, granted: bool, *, actor_id: str) -> None:
        with self._write() as db:
            account = db.execute("SELECT 1 FROM accounts WHERE id = ? AND id != ?", (account_id, ADMIN_ACTOR_ID)).fetchone()
            project = db.execute("SELECT 1 FROM projects WHERE id = ? AND retired = 0", (project_id,)).fetchone()
            if not account or not project:
                raise ValueError("Account or project not found.")
            if granted:
                change = db.execute("INSERT OR IGNORE INTO memberships VALUES (?, ?)", (account_id, project_id))
            else:
                change = db.execute("DELETE FROM memberships WHERE account_id = ? AND project_id = ?", (account_id, project_id))
                db.execute("DELETE FROM team_audit_grants WHERE actor_id = ? AND project_id = ?", (account_id, project_id))
            if change.rowcount:
                action = "project.grant" if granted else "project.revoke"
                self._audit(db, action, actor_id, account_id=account_id, project_id=project_id)

    def memberships(self, account_id: str, *, include_disabled: bool = False) -> dict[str, str]:
        with closing(self._connect()) as db:
            rows = db.execute(
                """SELECT projects.native_name, projects.id FROM memberships
                   JOIN projects ON projects.id = memberships.project_id
                   JOIN accounts ON accounts.id = memberships.account_id
                   WHERE memberships.account_id = ? AND projects.retired = 0 AND (accounts.enabled = 1 OR ?)""",
                (account_id, include_disabled),
            ).fetchall()
        return {row["native_name"]: row["id"] for row in rows}

    def reserve_run(self, *, context_id: str, project_id: str, account_id: str, runtime_id: str,
                    request_id: str, request_digest: str, kind: str = "message") -> tuple[TeamRun, bool]:
        with self._write() as db:
            member = db.execute(
                """SELECT a.username FROM accounts a
                   JOIN projects p ON p.id = ? AND p.retired = 0
                   LEFT JOIN memberships m ON m.account_id = a.id AND m.project_id = p.id
                   WHERE a.id = ? AND (a.id = ? OR (a.enabled = 1 AND m.account_id IS NOT NULL))""",
                (project_id, account_id, ADMIN_ACTOR_ID),
            ).fetchone()
            if member is None:
                raise PermissionError("Project access denied.")

            existing = db.execute(
                _RUN_SELECT + " WHERE context_id = ? AND account_id = ? AND request_id = ?",
                (context_id, account_id, request_id),
            ).fetchone()
            if existing:
                if existing["request_digest"] != request_digest or existing["project_id"] != project_id or existing["kind"] != kind:
                    raise ValueError("The message ID was already used for a different request.")
                return TeamRun.from_row(existing), False

            active = db.execute(_RUN_SELECT + f" WHERE context_id = ? AND {_ACTIVE_RUN}", (context_id,)).fetchone()
            if active:
                raise ActiveRunConflict(TeamRun.from_row(active))

            run = TeamRun(uuid4().hex, context_id, project_id, account_id, member["username"], request_id, "starting", kind)
            db.execute(
                """INSERT INTO team_runs(id, context_id, project_id, account_id, request_id, request_digest,
                   runtime_id, state, kind, accepting_queue) VALUES (?, ?, ?, ?, ?, ?, ?, 'starting', ?, ?)""",
                (run.id, context_id, project_id, account_id, request_id, request_digest, runtime_id, kind, kind == "message"),
            )
            self._audit(db, "message.accept", account_id, project_id=project_id,
                        context_id=context_id, run_id=run.id, result="starting")
            return run, True

    def active_run(self, context_id: str) -> TeamRun | None:
        with closing(self._connect()) as db:
            row = db.execute(_RUN_SELECT + f" WHERE context_id = ? AND {_ACTIVE_RUN}", (context_id,)).fetchone()
        return TeamRun.from_row(row) if row else None

    def active_runs(self) -> dict[str, TeamRun]:
        with closing(self._connect()) as db:
            rows = db.execute(_RUN_SELECT + f" WHERE {_ACTIVE_RUN}").fetchall()
        return {row["context_id"]: TeamRun.from_row(row) for row in rows}

    def start_run(self, run: TeamRun) -> bool:
        with self._write() as db:
            change = db.execute("UPDATE team_runs SET state = 'running' WHERE id = ? AND state = 'starting'", (run.id,))
            return change.rowcount == 1

    def request_stop(self, run: TeamRun, actor_id: str) -> bool:
        with self._write() as db:
            change = db.execute(
                "UPDATE team_runs SET state = 'stopping' WHERE id = ? AND state IN ('starting', 'running')", (run.id,),
            )
            if change.rowcount:
                self._audit(db, "message.stop", actor_id, project_id=run.project_id,
                            context_id=run.context_id, run_id=run.id, result="stopping")
            return change.rowcount == 1

    @staticmethod
    def _queue_is_open(db: sqlite3.Connection, run: TeamRun) -> bool:
        row = db.execute(
            """SELECT 1 FROM team_runs LEFT JOIN memberships
                 ON memberships.account_id = team_runs.account_id AND memberships.project_id = team_runs.project_id
               JOIN accounts ON accounts.id = team_runs.account_id
               JOIN projects ON projects.id = team_runs.project_id
               WHERE team_runs.id = ? AND team_runs.state IN ('starting', 'running')
                 AND team_runs.accepting_queue = 1 AND projects.retired = 0
                 AND (accounts.id = ? OR (accounts.enabled = 1 AND memberships.account_id IS NOT NULL))""",
            (run.id, ADMIN_ACTOR_ID),
        ).fetchone()
        return bool(row)

    @staticmethod
    def _queue_count(db: sqlite3.Connection, run_id: str) -> int:
        return db.execute("SELECT count(*) FROM team_queue_items WHERE run_id = ? AND state = 'queued'", (run_id,)).fetchone()[0]

    def add_queued_message(self, run: TeamRun, item_id: str, text: str) -> int:
        fingerprint = hashlib.sha256(text.encode()).hexdigest()
        with self._write() as db:
            if not self._queue_is_open(db, run):
                raise ValueError("This run is no longer accepting queued messages.")
            existing = db.execute(
                "SELECT fingerprint FROM team_queue_items WHERE run_id = ? AND item_id = ?", (run.id, item_id),
            ).fetchone()
            if existing and existing["fingerprint"] != fingerprint:
                raise ValueError("That queued message ID was already used.")
            if not existing:
                db.execute("INSERT INTO team_queue_items(run_id, item_id, text, fingerprint) VALUES (?, ?, ?, ?)",
                           (run.id, item_id, text, fingerprint))
                self._audit(db, "queue.add", run.account_id, project_id=run.project_id,
                            context_id=run.context_id, run_id=run.id, result="queued")
            return self._queue_count(db, run.id)

    def edit_queue(self, run: TeamRun, *, item_id: str | None, remove: bool, first_only: bool = False) -> tuple[int, int]:
        with self._write() as db:
            if not self._queue_is_open(db, run):
                raise ValueError("This run's queue is closed.")
            update = "state = 'removed', text = ''" if remove else "interject = 1"
            change = db.execute(
                f"""UPDATE team_queue_items SET {update}
                    WHERE run_id = ? AND state = 'queued' AND (? IS NULL OR item_id = ?)
                    AND (? = 0 OR seq = (SELECT min(seq) FROM team_queue_items WHERE run_id = ? AND state = 'queued'))""",
                (run.id, item_id, item_id, first_only, run.id),
            )
            if change.rowcount:
                self._audit(db, "queue.remove" if remove else "queue.interject", run.account_id,
                            project_id=run.project_id, context_id=run.context_id, run_id=run.id,
                            result="removed" if remove else "promoted")
            return change.rowcount, self._queue_count(db, run.id)

    def take_queued_message(self, run: TeamRun, *, interject: bool) -> tuple[str, str] | None:
        with self._write() as db:
            if not self._queue_is_open(db, run):
                return None
            row = db.execute(
                """SELECT seq, item_id, text FROM team_queue_items
                   WHERE run_id = ? AND state = 'queued' AND (? = 0 OR interject = 1)
                   ORDER BY seq LIMIT 1""",
                (run.id, interject),
            ).fetchone()
            if not row:
                if not interject:
                    db.execute("UPDATE team_runs SET accepting_queue = 0 WHERE id = ?", (run.id,))
                return None
            db.execute("UPDATE team_queue_items SET state = 'taken', text = '' WHERE seq = ?", (row["seq"],))
            self._audit(db, "queue.claim", run.account_id, project_id=run.project_id,
                        context_id=run.context_id, run_id=run.id, result="interjection" if interject else "after_turn")
            return row["item_id"], row["text"]

    def pending_queues(self) -> dict[str, list[dict]]:
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT run_id, seq, item_id, text FROM team_queue_items WHERE state = 'queued' ORDER BY seq",
            ).fetchall()
        queues: dict[str, list[dict]] = {}
        for row in rows:
            text = row["text"]
            queues.setdefault(row["run_id"], []).append({
                "id": row["item_id"], "seq": row["seq"], "text": text[:100] + "..." if len(text) > 100 else text,
                "attachments": [], "attachment_count": 0,
            })
        return queues

    @staticmethod
    def _cancel_queued_messages(db: sqlite3.Connection, run: TeamRun) -> None:
        db.execute("UPDATE team_queue_items SET state = 'cancelled', text = '' WHERE run_id = ? AND state = 'queued'", (run.id,))

    def finish_run(self, run: TeamRun, state: str) -> bool:
        if state not in {"completed", "failed", "stopped", "interrupted"}:
            raise ValueError("A finished run must have a terminal state.")
        with self._write() as db:
            change = db.execute(
                f"UPDATE team_runs SET state = ?, finished_at = unixepoch() WHERE id = ? AND {_ACTIVE_RUN}",
                (state, run.id),
            )
            if change.rowcount:
                self._cancel_queued_messages(db, run)
                self._audit(db, "message.finish", run.account_id, project_id=run.project_id,
                            context_id=run.context_id, run_id=run.id, result=state)
            return change.rowcount == 1

    def recover_runs(self, runtime_id: str) -> int:
        with self._write() as db:
            rows = db.execute(_RUN_SELECT + f" WHERE runtime_id != ? AND {_ACTIVE_RUN}", (runtime_id,)).fetchall()
            for row in rows:
                run = TeamRun.from_row(row)
                db.execute("UPDATE team_runs SET state = 'interrupted', finished_at = unixepoch() WHERE id = ?", (run.id,))
                self._cancel_queued_messages(db, run)
                self._audit(db, "message.recover", "system", project_id=run.project_id,
                            context_id=run.context_id, run_id=run.id, result="interrupted")
            return len(rows)


@lru_cache(maxsize=4)
def _store(path: str) -> TeamStore:
    return TeamStore(Path(path))


def get_store() -> TeamStore:
    return _store(files.get_abs_path("usr", "team", "access.sqlite3"))
