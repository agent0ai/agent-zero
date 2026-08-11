from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import stat
import tarfile
import tempfile
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MAX_FILES = 5_000
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}
MEMORY_NAMES = {
    "memory.md",
}
INSTRUCTION_NAMES = {
    "agents.md",
    "claude.md",
    "identity.md",
    "soul.md",
    "tools.md",
    "user.md",
}
PROJECT_PATH_KEYS = ("cwd", "directory", "workspace")
SENSITIVE_NAMES = {
    ".credentials.json",
    ".env",
    "auth.json",
    "credentials.json",
    "openclaw.json",
    "settings.json",
}
SECRET_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret)\b[\"']?\s*[:=]\s*[\"']?)([^\s\"']+)"
)
BEARER_RE = re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s\"']+)")
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----"
)
DATA_URL_RE = re.compile(r"data:[^;,\s]+;base64,[A-Za-z0-9+/=_-]+")


@dataclass(slots=True)
class Upload:
    name: str
    data: bytes


@dataclass(slots=True)
class Event:
    kind: str
    text: str = ""
    timestamp: float = 0.0
    thoughts: list[str] = field(default_factory=list)
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""


@dataclass(slots=True)
class Conversation:
    source_id: str
    title: str
    events: list[Event]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Asset:
    path: str
    data: bytes


@dataclass(slots=True)
class Project:
    source_id: str
    title: str
    path: str
    conversation_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Bundle:
    source: str
    conversations: list[Conversation] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    memories: list[Asset] = field(default_factory=list)
    instructions: list[Asset] = field(default_factory=list)
    skills: dict[str, list[Asset]] = field(default_factory=dict)
    excluded: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    redactions: int = 0

    @property
    def knowledge(self) -> list[Asset]:
        return [*self.memories, *self.instructions]

    def summary(self) -> dict[str, int]:
        return {
            "chats": len(self.conversations),
            "projects": len(self.projects),
            "messages": sum(len(item.events) for item in self.conversations),
            "memories": len(self.memories),
            "instructions": len(self.instructions),
            "knowledge": len(self.memories) + len(self.instructions),
            "skills": len(self.skills),
            "excluded": len(self.excluded),
            "redactions": self.redactions,
        }


def _safe_name(name: str) -> str:
    value = str(PurePosixPath(name.replace("\\", "/")))
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive path: {name!r}")
    return value.lstrip("./")


def expand_uploads(uploads: Iterable[Upload]) -> list[Upload]:
    result: list[Upload] = []
    total = 0

    def add(name: str, data: bytes) -> None:
        nonlocal total
        clean = _safe_name(name)
        if not clean or clean.endswith("/"):
            return
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"File exceeds the 100 MiB limit: {clean}")
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Expanded upload exceeds the 256 MiB limit")
        result.append(Upload(clean, data))
        if len(result) > MAX_FILES:
            raise ValueError(f"Upload contains more than {MAX_FILES} files")

    for upload in uploads:
        lower = upload.name.lower()
        if lower.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(upload.data)) as archive:
                for member in archive.infolist():
                    mode = member.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        raise ValueError(f"Archive symlinks are not accepted: {member.filename}")
                    if member.is_dir():
                        continue
                    add(member.filename, archive.read(member))
        elif lower.endswith((".tar", ".tar.gz", ".tgz")):
            with tarfile.open(fileobj=io.BytesIO(upload.data), mode="r:*") as archive:
                for member in archive.getmembers():
                    if member.issym() or member.islnk() or member.isdev():
                        raise ValueError(f"Archive links and devices are not accepted: {member.name}")
                    if not member.isfile():
                        continue
                    source = archive.extractfile(member)
                    if source is not None:
                        add(member.name, source.read(MAX_FILE_BYTES + 1))
        else:
            add(upload.name, upload.data)
    return result


def _text(asset: Upload | Asset) -> str:
    return asset.data.decode("utf-8-sig", "replace")


def _redact(value: str) -> tuple[str, int]:
    count = 0

    def secret(match: re.Match[str]) -> str:
        nonlocal count
        if match.group(2).startswith("$"):
            return match.group(0)
        count += 1
        return f"{match.group(1)}[REDACTED]"

    value = SECRET_RE.sub(secret, value)
    value, bearer_count = BEARER_RE.subn(r"\1[REDACTED]", value)
    value, key_count = PRIVATE_KEY_RE.subn("[PRIVATE KEY REDACTED]", value)
    value, data_count = DATA_URL_RE.subn("[EMBEDDED DATA OMITTED]", value)
    return value, count + bearer_count + key_count + data_count


def _timestamp(value: Any, fallback: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        number = float(value)
        return number / 1000 if number > 10_000_000_000 else number
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return fallback or datetime.now(timezone.utc).timestamp()


def _one_line(value: str, limit: int = 92) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        for key in ("text", "content", "user_message"):
            if isinstance(content.get(key), str):
                return content[key]
        return ""
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") not in {"thinking", "reasoning"}:
                value = item.get("text") or item.get("content")
                if isinstance(value, str):
                    parts.append(value)
        return "\n".join(part for part in parts if part)
    return ""


def _tool_blocks(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, list):
        return []
    return [
        item
        for item in content
        if isinstance(item, dict) and item.get("type") in {"tool_use", "toolCall", "tool-call"}
    ]


def _events_from_messages(messages: Iterable[dict[str, Any]]) -> list[Event]:
    events: list[Event] = []
    pending_tools: dict[str, Event] = {}
    for index, message in enumerate(messages):
        role = str(message.get("role") or message.get("type") or "").lower()
        content = message.get("content")
        when = _timestamp(message.get("timestamp") or message.get("created_at"), index + 1)
        if role in {"user", "human"}:
            text = _content_text(content)
            if text:
                events.append(Event("user", text=text, timestamp=when))
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    tool_id = str(block.get("tool_use_id") or "")
                    result = _content_text(block.get("content"))
                    if tool_id in pending_tools:
                        pending_tools[tool_id].tool_result = result
            continue
        if role in {"assistant", "agent", "ai"}:
            text = _content_text(content)
            if text:
                events.append(Event("assistant", text=text, timestamp=when))
            for block in _tool_blocks(content):
                tool_id = str(block.get("id") or block.get("tool_call_id") or "")
                event = Event(
                    "tool",
                    timestamp=when,
                    tool_name=str(block.get("name") or "tool"),
                    tool_args=block.get("input") if isinstance(block.get("input"), dict) else {},
                )
                events.append(event)
                if tool_id:
                    pending_tools[tool_id] = event
            calls = message.get("tool_calls")
            if isinstance(calls, str):
                try:
                    calls = json.loads(calls)
                except json.JSONDecodeError:
                    calls = []
            for call in calls or []:
                if not isinstance(call, dict):
                    continue
                function = call.get("function") if isinstance(call.get("function"), dict) else call
                raw_args = function.get("arguments") or {}
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        raw_args = {"raw_arguments": raw_args}
                event = Event(
                    "tool",
                    timestamp=when,
                    tool_name=str(function.get("name") or "tool"),
                    tool_args=raw_args if isinstance(raw_args, dict) else {"value": raw_args},
                )
                events.append(event)
                tool_id = str(call.get("id") or "")
                if tool_id:
                    pending_tools[tool_id] = event
            continue
        if role in {"tool", "tool_result"}:
            tool_id = str(message.get("tool_call_id") or message.get("id") or "")
            result = _content_text(content)
            if tool_id in pending_tools:
                pending_tools[tool_id].tool_result = result
            else:
                events.append(
                    Event(
                        "tool",
                        timestamp=when,
                        tool_name=str(message.get("tool_name") or message.get("name") or "tool"),
                        tool_result=result,
                    )
                )
    return events


def _conversation(source_id: str, title: str, events: list[Event], **metadata: Any) -> Conversation | None:
    visible = [event for event in events if event.kind == "tool" or event.text.strip()]
    if not visible:
        return None
    first_user = next((event.text for event in visible if event.kind == "user"), source_id)
    return Conversation(source_id, _one_line(title or first_user or source_id), visible, metadata)


def _json_lines(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_no}: {exc.msg}") from exc
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _parse_codex(asset: Upload) -> list[Conversation]:
    rows = _json_lines(_text(asset))
    metadata: dict[str, Any] = {}
    events: list[Event] = []
    pending: dict[str, Event] = {}
    thoughts: list[str] = []
    for index, row in enumerate(rows):
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        if row.get("type") == "session_meta" and not metadata:
            metadata = dict(payload)
            continue
        if row.get("type") == "event_msg":
            event_type = payload.get("type")
            when = _timestamp(row.get("timestamp"), index + 1)
            text = payload.get("message")
            if not isinstance(text, str) or not text.strip():
                continue
            if event_type == "user_message":
                events.append(Event("user", text=text, timestamp=when))
            elif event_type == "agent_message" and payload.get("phase") == "commentary":
                thoughts.append(text)
            elif event_type == "agent_message" and payload.get("phase") == "final_answer":
                events.append(Event("assistant", text=text, timestamp=when, thoughts=thoughts.copy()))
                thoughts.clear()
            continue
        if row.get("type") != "response_item":
            continue
        item_type = payload.get("type")
        call_id = str(payload.get("call_id") or payload.get("id") or "")
        when = _timestamp(row.get("timestamp"), index + 1)
        if item_type in {"function_call", "custom_tool_call"}:
            raw = payload.get("arguments") if item_type == "function_call" else payload.get("input")
            if isinstance(raw, str):
                try:
                    args = json.loads(raw)
                except json.JSONDecodeError:
                    args = {"input": raw}
            else:
                args = raw if isinstance(raw, dict) else {}
            event = Event(
                "tool",
                timestamp=when,
                thoughts=thoughts.copy(),
                tool_name=str(payload.get("name") or "tool"),
                tool_args=args,
            )
            thoughts.clear()
            events.append(event)
            if call_id:
                pending[call_id] = event
        elif item_type in {"function_call_output", "custom_tool_call_output"} and call_id in pending:
            pending[call_id].tool_result = _content_text(payload.get("output")) or str(payload.get("output") or "")
    item = _conversation(
        str(metadata.get("id") or metadata.get("session_id") or Path(asset.name).stem),
        "",
        events,
        cwd=metadata.get("cwd"),
        originator=metadata.get("originator"),
    )
    return [item] if item else []


def _parse_claude(asset: Upload) -> list[Conversation]:
    rows = _json_lines(_text(asset))
    messages: list[dict[str, Any]] = []
    session_id = Path(asset.name).stem
    cwd = ""
    for row in rows:
        if row.get("isSidechain") is True or row.get("type") not in {"user", "assistant"}:
            continue
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        messages.append({**message, "timestamp": row.get("timestamp")})
        session_id = str(row.get("sessionId") or session_id)
        cwd = str(row.get("cwd") or cwd)
    item = _conversation(session_id, "", _events_from_messages(messages), cwd=cwd)
    return [item] if item else []


def _parse_opencode(asset: Upload) -> list[Conversation]:
    try:
        data = json.loads(_text(asset))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        return []
    info = data.get("info") if isinstance(data.get("info"), dict) else {}
    events: list[Event] = []
    for index, wrapper in enumerate(data["messages"]):
        if not isinstance(wrapper, dict):
            continue
        message = wrapper.get("info") if isinstance(wrapper.get("info"), dict) else wrapper
        role = str(message.get("role") or "")
        when = _timestamp((message.get("time") or {}).get("created") if isinstance(message.get("time"), dict) else None, index + 1)
        parts = wrapper.get("parts") if isinstance(wrapper.get("parts"), list) else []
        text = "\n".join(
            str(part.get("text"))
            for part in parts
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text")
        )
        if text and role in {"user", "assistant"}:
            events.append(Event(role, text=text, timestamp=when))
        for part in parts:
            if not isinstance(part, dict) or part.get("type") != "tool":
                continue
            state = part.get("state") if isinstance(part.get("state"), dict) else {}
            args = state.get("input") if isinstance(state.get("input"), dict) else {}
            events.append(
                Event(
                    "tool",
                    timestamp=when,
                    tool_name=str(part.get("tool") or state.get("title") or "tool"),
                    tool_args=args,
                    tool_result=_content_text(state.get("output")),
                )
            )
    item = _conversation(
        str(info.get("id") or Path(asset.name).stem),
        str(info.get("title") or ""),
        events,
        directory=info.get("directory"),
        project_id=info.get("projectID"),
    )
    return [item] if item else []


def _parse_hermes_jsonl(asset: Upload) -> list[Conversation]:
    result: list[Conversation] = []
    for row in _json_lines(_text(asset)):
        messages = row.get("messages")
        if not isinstance(messages, list):
            continue
        item = _conversation(
            str(row.get("id") or row.get("session_id") or uuid.uuid4()),
            str(row.get("title") or ""),
            _events_from_messages(message for message in messages if isinstance(message, dict)),
            source=row.get("source"),
            cwd=row.get("cwd"),
            model=row.get("model"),
        )
        if item:
            result.append(item)
    return result


def _parse_openclaw_jsonl(asset: Upload) -> list[Conversation]:
    rows = _json_lines(_text(asset))
    session_id = Path(asset.name).stem
    title = ""
    workspace = ""
    messages: list[dict[str, Any]] = []
    for row in rows:
        if row.get("type") in {"session", "session_meta"}:
            session_id = str(row.get("id") or row.get("sessionId") or session_id)
            title = str(row.get("title") or title)
            workspace = str(row.get("cwd") or row.get("workspace") or workspace)
            continue
        message = row.get("message") if isinstance(row.get("message"), dict) else None
        if row.get("type") == "message" and message:
            messages.append({**message, "timestamp": row.get("timestamp") or message.get("timestamp")})
        elif row.get("role"):
            messages.append(row)
    item = _conversation(session_id, title, _events_from_messages(messages), workspace=workspace)
    return [item] if item else []


def _sqlite(asset: Upload) -> tuple[sqlite3.Connection, str]:
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    try:
        handle.write(asset.data)
        handle.close()
        connection = sqlite3.connect(f"file:{handle.name}?mode=ro&immutable=1", uri=True)
        connection.row_factory = sqlite3.Row
        return connection, handle.name
    except Exception:
        Path(handle.name).unlink(missing_ok=True)
        raise


def _close_sqlite(connection: sqlite3.Connection, path: str) -> None:
    connection.close()
    Path(path).unlink(missing_ok=True)


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _parse_hermes_db(asset: Upload) -> list[Conversation]:
    connection, path = _sqlite(asset)
    try:
        if not {"sessions", "messages"}.issubset(_tables(connection)):
            return []
        result: list[Conversation] = []
        for session in connection.execute("SELECT * FROM sessions ORDER BY started_at"):
            rows = connection.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp, id", (session["id"],)
            ).fetchall()
            messages = [dict(row) for row in rows]
            item = _conversation(
                str(session["id"]),
                str(session["title"] or "") if "title" in session.keys() else "",
                _events_from_messages(messages),
                source=session["source"] if "source" in session.keys() else None,
                cwd=session["cwd"] if "cwd" in session.keys() else None,
                model=session["model"] if "model" in session.keys() else None,
            )
            if item:
                result.append(item)
        return result
    finally:
        _close_sqlite(connection, path)


def _parse_openclaw_db(asset: Upload) -> list[Conversation]:
    connection, path = _sqlite(asset)
    try:
        if not {"session_windows", "transcript_events"}.issubset(_tables(connection)):
            return []
        result: list[Conversation] = []
        for window in connection.execute("SELECT * FROM session_windows ORDER BY created_at"):
            messages: list[dict[str, Any]] = []
            for row in connection.execute(
                "SELECT event_json, created_at FROM transcript_events WHERE session_id = ? ORDER BY seq",
                (window["session_id"],),
            ):
                try:
                    event = json.loads(row["event_json"])
                except (TypeError, json.JSONDecodeError):
                    continue
                message = event.get("message") if isinstance(event.get("message"), dict) else None
                if event.get("type") == "message" and message:
                    messages.append({**message, "timestamp": event.get("timestamp") or row["created_at"]})
                elif event.get("role"):
                    messages.append({**event, "timestamp": event.get("timestamp") or row["created_at"]})
            item = _conversation(
                str(window["session_id"]),
                str(window["display_name"] or "") if "display_name" in window.keys() else "",
                _events_from_messages(messages),
                session_key=window["session_key"],
                channel=window["channel"] if "channel" in window.keys() else None,
                model=window["model"] if "model" in window.keys() else None,
            )
            if item:
                result.append(item)
        return result
    finally:
        _close_sqlite(connection, path)


def _is_sqlite(asset: Upload) -> bool:
    return asset.data.startswith(b"SQLite format 3\x00")


def _discover_assets(files: list[Upload], bundle: Bundle) -> None:
    skill_roots: dict[str, str] = {}
    for item in files:
        path = PurePosixPath(item.name)
        if path.name.lower() == "skill.md":
            key = str(path.parent)
            skill_roots[key] = re.sub(r"[^a-z0-9_-]+", "_", path.parent.name.lower()).strip("_") or "skill"
    for item in files:
        path = PurePosixPath(item.name)
        suffix = path.suffix.lower()
        sensitive = path.name.lower() in SENSITIVE_NAMES or suffix in {".key", ".pem"}
        for root, slug in skill_roots.items():
            root_path = PurePosixPath(root)
            try:
                relative = path.relative_to(root_path)
            except ValueError:
                continue
            if sensitive:
                bundle.excluded.append(f"{item.name}: credentials are never imported")
            else:
                bundle.skills.setdefault(slug, []).append(Asset(str(relative), item.data))
            break
        else:
            lower_parts = {part.lower() for part in path.parts}
            if suffix == ".md" and path.name.lower() in INSTRUCTION_NAMES:
                bundle.instructions.append(Asset(item.name, item.data))
            elif suffix == ".md" and (
                path.name.lower() in MEMORY_NAMES or "memory" in lower_parts or "memories" in lower_parts
            ):
                bundle.memories.append(Asset(item.name, item.data))
            elif sensitive:
                bundle.excluded.append(f"{item.name}: settings or credentials are never imported")


def _discover_projects(bundle: Bundle) -> None:
    by_path: dict[str, Project] = {}
    for conversation in bundle.conversations:
        project_path = next(
            (
                str(conversation.metadata.get(key) or "").strip()
                for key in PROJECT_PATH_KEYS
                if str(conversation.metadata.get(key) or "").strip()
            ),
            "",
        )
        if not project_path or project_path in {".", "/", "\\"}:
            continue
        normalized = project_path.replace("\\", "/").rstrip("/")
        title = PurePosixPath(normalized).name or "Imported project"
        source_id = hashlib.sha256(f"{bundle.source}:{project_path}".encode()).hexdigest()[:12]
        project = by_path.setdefault(source_id, Project(source_id, title, project_path))
        project.conversation_ids.append(conversation.source_id)
    bundle.projects = list(by_path.values())


def parse_bundle(source: str, uploads: Iterable[Upload]) -> Bundle:
    if source not in {"openclaw", "hermes", "opencode", "claude", "codex"}:
        raise ValueError("Choose one of the five supported source harnesses")
    files = expand_uploads(uploads)
    bundle = Bundle(source)
    _discover_assets(files, bundle)
    seen: set[str] = set()
    for asset in files:
        lower = asset.name.lower()
        conversations: list[Conversation] = []
        try:
            if _is_sqlite(asset):
                conversations = _parse_hermes_db(asset) if source == "hermes" else _parse_openclaw_db(asset) if source == "openclaw" else []
            elif source == "codex" and lower.endswith(".jsonl"):
                conversations = _parse_codex(asset)
            elif source == "claude" and lower.endswith(".jsonl") and "/history.jsonl" not in f"/{lower}":
                conversations = _parse_claude(asset)
            elif source == "opencode" and lower.endswith(".json"):
                conversations = _parse_opencode(asset)
            elif source == "hermes" and lower.endswith(".jsonl"):
                conversations = _parse_hermes_jsonl(asset)
            elif source == "openclaw" and lower.endswith(".jsonl"):
                conversations = _parse_openclaw_jsonl(asset)
        except (ValueError, sqlite3.DatabaseError) as exc:
            bundle.warnings.append(f"{asset.name}: {exc}")
            continue
        for conversation in conversations:
            identity = f"{source}:{conversation.source_id}"
            if identity not in seen:
                seen.add(identity)
                bundle.conversations.append(conversation)

    _discover_projects(bundle)

    for conversation in bundle.conversations:
        for event in conversation.events:
            event.text, count = _redact(event.text)
            bundle.redactions += count
            event.tool_result, count = _redact(event.tool_result)
            bundle.redactions += count
            raw_args, count = _redact(json.dumps(event.tool_args, ensure_ascii=False))
            bundle.redactions += count
            try:
                event.tool_args = json.loads(raw_args)
            except json.JSONDecodeError:
                event.tool_args = {"redacted": raw_args}
    for asset in bundle.knowledge:
        text, count = _redact(_text(asset))
        bundle.redactions += count
        asset.data = text.encode()
    for assets in bundle.skills.values():
        for asset in assets:
            if PurePosixPath(asset.path).suffix.lower() in TEXT_SUFFIXES:
                text, count = _redact(_text(asset))
                bundle.redactions += count
                asset.data = text.encode()
    if not bundle.conversations and not bundle.knowledge and not bundle.skills:
        bundle.warnings.append("No supported chats, memories, instructions, or skills were found in this upload")
    return bundle


def _iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def build_a0_chat(conversation: Conversation, source: str) -> dict[str, Any]:
    events = conversation.events
    if not events:
        raise ValueError("Conversation contains no importable events")
    messages: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    sequence = 0
    last_timestamp = 0.0

    def message(ai: bool, content: Any, when: float, kind: str) -> dict[str, Any]:
        nonlocal sequence
        sequence += 1
        item = {
            "_cls": "Message",
            "id": str(uuid.uuid4()),
            "ai": ai,
            "content": content,
            "metadata": {"imported_from": source, "source_event": kind, "source_timestamp": _iso(when)},
            "sequence": sequence,
            "summary": "",
            "tokens": 0,
        }
        messages.append(item)
        return item

    def log(kind: str, item: dict[str, Any], heading: str, content: str, kvps: dict[str, Any], when: float) -> None:
        nonlocal last_timestamp
        last_timestamp = max(when, last_timestamp + 0.000001)
        logs.append(
            {
                "no": len(logs),
                "id": item["id"],
                "type": kind,
                "heading": heading,
                "content": content,
                "kvps": kvps,
                "timestamp": last_timestamp,
                "agentno": 0,
            }
        )

    for index, event in enumerate(events):
        when = event.timestamp or index + 1.0
        if event.kind == "user":
            item = message(False, {"user_message": event.text}, when, "user")
            log("user", item, "", event.text, {"attachments": []}, when)
        elif event.kind == "assistant":
            envelope = {
                "thoughts": event.thoughts or [f"Imported public response from {source}."],
                "headline": _one_line(event.text),
                "tool_name": "response",
                "tool_args": {"text": event.text},
            }
            raw = json.dumps(envelope, ensure_ascii=False)
            item = message(True, raw, when, "assistant")
            log("agent", item, envelope["headline"], raw, envelope, when)
            log("response", item, "icon://chat Responding", event.text, {"finished": True}, when + 0.000001)
        elif event.kind == "tool":
            name = event.tool_name or "tool"
            envelope = {
                "thoughts": event.thoughts or [f"Imported historical {source} tool activity."],
                "headline": f"Using imported {name} record",
                "tool_name": name,
                "tool_args": event.tool_args,
            }
            raw = json.dumps(envelope, ensure_ascii=False)
            call = message(True, raw, when, "tool_call")
            log("agent", call, envelope["headline"], raw, envelope, when)
            result_text = event.tool_result or "No retained tool result was available."
            result = message(
                False,
                {"tool_name": name, "tool_result": result_text, "file": ""},
                when + 0.000001,
                "tool_result",
            )
            log(
                "tool",
                result,
                f"icon://construction Using tool '{name}'",
                result_text,
                {**event.tool_args, "_tool_name": name},
                when + 0.000001,
            )

    history = {
        "_cls": "History",
        "counter": sequence,
        "bulks": [],
        "topics": [],
        "current": {"_cls": "Topic", "summary": "", "messages": messages},
    }
    first = min((event.timestamp for event in events if event.timestamp), default=1.0)
    last = max((event.timestamp for event in events if event.timestamp), default=first)
    chat_id = hashlib.sha256(f"{source}:{conversation.source_id}".encode()).hexdigest()[:8]
    return {
        "id": chat_id,
        "name": conversation.title,
        "created_at": _iso(first),
        "type": "user",
        "last_message": _iso(last),
        "agents": [
            {
                "number": 0,
                "agent_profile": "default",
                "data": {},
                "history": json.dumps(history, ensure_ascii=False),
            }
        ],
        "streaming_agent": 0,
        "agent_profile": "default",
        "log": {"guid": str(uuid.uuid4()), "logs": logs, "progress": "", "progress_no": 0},
        "data": {
            "_migrate_agents": {
                "format_version": 1,
                "source": source,
                "source_id": conversation.source_id,
                "source_metadata": conversation.metadata,
                "hidden_reasoning_included": False,
                "historical_tools_are_replayable": False,
            }
        },
        "output_data": {},
    }


def preview(bundle: Bundle) -> dict[str, Any]:
    return {
        "ok": True,
        "source": bundle.source,
        "summary": bundle.summary(),
        "chats": [
            {
                "id": item.source_id,
                "title": item.title,
                "messages": len(item.events),
                "metadata": item.metadata,
            }
            for item in bundle.conversations[:200]
        ],
        "projects": [
            {
                "id": item.source_id,
                "title": item.title,
                "path": item.path,
                "chats": len(item.conversation_ids),
            }
            for item in bundle.projects[:200]
        ],
        "memories": [item.path for item in bundle.memories[:200]],
        "instructions": [item.path for item in bundle.instructions[:200]],
        "knowledge": [item.path for item in bundle.knowledge[:200]],
        "skills": sorted(bundle.skills)[:200],
        "excluded": bundle.excluded[:200],
        "warnings": bundle.warnings[:200],
    }
