from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable

from python.helpers import files


_WRITE_LOCK = threading.RLock()


def _utc_now_iso() -> str:
    # ISO-8601 UTC with millisecond precision, e.g. 2026-03-03T12:34:56.789Z
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def get_audit_log_path() -> str:
    """
    Returns the absolute path to the audit log JSONL file.

    Override with env var: A0_AUDIT_LOG_PATH
    Default: <repo>/logs/audit.jsonl
    """
    override = os.getenv("A0_AUDIT_LOG_PATH")
    if override:
        if os.path.isabs(override):
            return override
        return files.get_abs_path(override)
    return files.get_abs_path("logs", "audit.jsonl")


def _sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def stable_json_dumps(obj: Any) -> str:
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def compute_output_hash(output: Any) -> str:
    """
    Returns a deterministic sha256 hash for the given output payload.
    """
    if output is None:
        payload = b"null"
    elif isinstance(output, (bytes, bytearray)):
        payload = bytes(output)
    elif isinstance(output, str):
        payload = output.encode("utf-8", errors="replace")
    else:
        payload = stable_json_dumps(output).encode("utf-8", errors="replace")
    return f"sha256:{_sha256_hex(payload)}"


_URL_RE = re.compile(r"https?://[^\s\"')]+")


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    urls = _URL_RE.findall(text)
    # Preserve order while deduping
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    agent_role: str
    user_action: str
    sources: list[str]
    output_hash: str
    file_paths_touched: list[str]
    extra: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "timestamp": self.timestamp,
            "agent_role": self.agent_role,
            "user_action": self.user_action,
            "sources": self.sources,
            "output_hash": self.output_hash,
            "file_paths_touched": self.file_paths_touched,
        }
        if self.extra:
            d["extra"] = self.extra
        return d


def append_event(
    event: AuditEvent | dict[str, Any], *, path: str | None = None
) -> dict[str, Any]:
    log_path = path or get_audit_log_path()
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    payload = event.to_dict() if isinstance(event, AuditEvent) else dict(event)
    line = stable_json_dumps(payload) + "\n"

    with _WRITE_LOCK:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)

    return payload


def log_event(
    *,
    agent_role: str,
    user_action: str,
    sources: Iterable[str] | None,
    output: Any,
    file_paths_touched: Iterable[str] | None,
    extra: dict[str, Any] | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    sources_list = [s for s in (sources or []) if s]
    file_paths_list = [p for p in (file_paths_touched or []) if p]
    event = AuditEvent(
        timestamp=_utc_now_iso(),
        agent_role=agent_role,
        user_action=user_action,
        sources=sources_list,
        output_hash=compute_output_hash(output),
        file_paths_touched=file_paths_list,
        extra=extra,
    )
    return append_event(event, path=path)


def log_message_async_intake(
    *,
    request_path: str,
    content_type: str,
    text: str,
    context_id: str,
    message_id: str | None,
    attachment_filenames: list[str],
    path: str | None = None,
) -> dict[str, Any]:
    ingested = {
        "request_path": request_path,
        "context_id": context_id,
        "message_id": message_id,
        "text_len": len(text or ""),
        "text_sha256": _sha256_hex((text or "").encode("utf-8", errors="replace")),
        "attachment_filenames": attachment_filenames,
        "content_type": content_type,
    }
    return log_event(
        agent_role="api",
        user_action="api:/message_async:intake",
        sources=[],
        output=ingested,
        file_paths_touched=attachment_filenames,
        extra={"request_path": request_path},
        path=path,
    )
