from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


_ENV_KEYS = {
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "XAI_API_KEY",
}

_SECRET_KEYS = {"access_token", "api_key", "refresh_token", "token"}


class OpenCodeAdapter(TerminalAgentAdapter):
    id = "opencode"
    title = "OpenCode"
    binary = "opencode"
    install_hint = "curl -fsSL https://opencode.ai/install | bash"
    description = "OpenCode CLI in non-interactive run mode."

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        env_var = next((name for name in sorted(_ENV_KEYS) if os.environ.get(name)), "")
        if env_var:
            return {"connected": True, "mode": "env", "auth_path": env_var}

        path = _auth_path()
        try:
            if _auth_store_has_credentials(path):
                return {"connected": True, "mode": "external", "auth_path": str(path)}
        except OSError as exc:
            return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        return {"connected": False, "mode": "", "auth_path": str(path)}


def _auth_path() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME", "").strip()
    root = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return root / "opencode" / "auth.json"


def _auth_store_has_credentials(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return _contains_secret(data)


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
