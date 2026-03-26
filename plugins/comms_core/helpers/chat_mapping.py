"""
Persistent mapping between platform chat IDs and A0 context IDs.

Storage: usr/plugins/{platform}/chat_map.json
Thread-safe for concurrent access from async handlers.
"""

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from python.helpers import files


@dataclass
class ChatMapEntry:
    context_id: str
    platform_user_id: str = ""
    created_at: str = ""
    last_active: str = ""


class ChatMapping:
    def __init__(self, platform: str):
        self._platform = platform
        self._lock = threading.RLock()
        self._map: dict[str, ChatMapEntry] = {}
        self._path = Path(
            files.get_abs_path(f"usr/plugins/{platform}/chat_map.json")
        )

    def __len__(self) -> int:
        with self._lock:
            return len(self._map)

    def get_context_id(self, platform_chat_id: str) -> Optional[str]:
        with self._lock:
            entry = self._map.get(platform_chat_id)
            return entry.context_id if entry else None

    def set(
        self,
        platform_chat_id: str,
        context_id: str,
        platform_user_id: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            existing = self._map.get(platform_chat_id)
            self._map[platform_chat_id] = ChatMapEntry(
                context_id=context_id,
                platform_user_id=platform_user_id
                or (existing.platform_user_id if existing else ""),
                created_at=existing.created_at if existing else now,
                last_active=now,
            )

    def remove(self, platform_chat_id: str) -> None:
        with self._lock:
            self._map.pop(platform_chat_id, None)

    async def load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                with self._lock:
                    self._map = {k: ChatMapEntry(**v) for k, v in raw.items()}
            except Exception:
                pass

    async def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = {k: v.__dict__ for k, v in self._map.items()}
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
