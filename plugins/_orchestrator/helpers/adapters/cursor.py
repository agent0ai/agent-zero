from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


_SECRET_KEYS = {"access_token", "api_key", "id_token", "refresh_token", "token"}
_AUTH_FILES = (
    "auth.json",
    "credentials.json",
    "token.json",
    "agent/auth.json",
    "agent/credentials.json",
    "agent/token.json",
)


class CursorCliAdapter(TerminalAgentAdapter):
    id = "cursor"
    title = "Cursor CLI"
    binary = "agent"
    install_hint = "curl https://cursor.com/install -fsS | bash"
    description = "Cursor Agent CLI in headless print mode."

    def _home(self) -> Path:
        configured = os.environ.get("CURSOR_HOME", "").strip()
        return Path(configured).expanduser() if configured else Path.home() / ".cursor"

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        env_var = next(
            (name for name in ("CURSOR_API_KEY", "API_KEY_CURSOR") if os.environ.get(name)),
            "",
        )
        if env_var:
            return {"connected": True, "mode": "env", "auth_path": env_var}

        home = self._home()
        for relative in _AUTH_FILES:
            path = home / relative
            try:
                if _file_has_secret(path):
                    return {"connected": True, "mode": "external", "auth_path": str(path)}
            except OSError as exc:
                return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        return {"connected": False, "mode": "", "auth_path": str(home)}


def _file_has_secret(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        return _contains_secret(json.loads(text))
    except ValueError:
        return _text_has_secret(text)


def _text_has_secret(text: str) -> bool:
    return any(f'"{key}"' in text or f"{key} =" in text for key in _SECRET_KEYS)


def _contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in _SECRET_KEYS and isinstance(item, str) and item.strip():
                return True
            if _contains_secret(item):
                return True
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return False
