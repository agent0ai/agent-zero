from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


_SECRET_KEYS = {"access_token", "api_key", "id_token", "refresh_token", "token"}


class GrokBuildAdapter(TerminalAgentAdapter):
    id = "grok"
    title = "Grok Build"
    binary = "grok"
    install_hint = "curl -fsSL https://x.ai/cli/install.sh | bash"
    description = "xAI Grok Build CLI in headless single-prompt mode."

    def _home(self) -> Path:
        configured = os.environ.get("GROK_HOME", "").strip()
        return Path(configured).expanduser() if configured else Path.home() / ".grok"

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        env_var = next(
            (name for name in ("XAI_API_KEY", "API_KEY_XAI") if os.environ.get(name)),
            "",
        )
        if env_var:
            return {"connected": True, "mode": "env", "auth_path": env_var}

        home = self._home()
        for path in (home / "config.toml", home / "auth.json"):
            try:
                if _file_has_secret(path):
                    return {"connected": True, "mode": "external", "auth_path": str(path)}
            except OSError as exc:
                return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        auth_dir = home / "auth"
        try:
            if auth_dir.is_dir():
                for path in auth_dir.iterdir():
                    if path.is_file() and _file_has_secret(path):
                        return {
                            "connected": True,
                            "mode": "external",
                            "auth_path": str(auth_dir),
                        }
        except OSError as exc:
            return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        return {"connected": False, "mode": "", "auth_path": str(home)}


def _file_has_secret(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix == ".toml":
        return _toml_has_secret(text)
    try:
        return _contains_secret(json.loads(text))
    except ValueError:
        return _text_has_secret(text)


def _toml_has_secret(text: str) -> bool:
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key == "api_key" and value:
            return True
        if key == "env_key" and value and os.environ.get(value):
            return True
    return False


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
