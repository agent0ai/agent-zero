from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_demo_requests_path() -> Path:
    env_path = os.getenv("AGENT_JUMBO_DEMO_REQUESTS_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _repo_root() / "tmp" / "demo_requests.jsonl"


def create_demo_request(payload: dict[str, Any]) -> dict[str, Any]:
    path = get_demo_requests_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    record: dict[str, Any] = {
        "id": f"dr_{uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    record.update(payload)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_demo_requests(limit: int = 25) -> list[dict[str, Any]]:
    path = get_demo_requests_path()
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
                if isinstance(value, dict):
                    rows.append(value)
            except json.JSONDecodeError:
                continue

    return list(reversed(rows[-max(limit, 1) :]))
