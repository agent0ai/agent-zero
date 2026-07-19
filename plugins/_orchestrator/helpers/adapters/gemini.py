from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


_API_KEY_ENV_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


class GeminiCliAdapter(TerminalAgentAdapter):
    id = "gemini"
    title = "Gemini CLI"
    binary = "gemini"
    install_hint = "npm install -g @google/gemini-cli"
    description = "Google Gemini CLI in headless single-prompt mode."

    def _home(self) -> Path:
        configured = os.environ.get("GEMINI_CLI_HOME", "").strip()
        root = Path(configured).expanduser() if configured else Path.home()
        return root / ".gemini"

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        env_var = next((name for name in _API_KEY_ENV_VARS if os.environ.get(name)), "")
        if env_var:
            return {"connected": True, "mode": "env", "auth_path": env_var}

        credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if credentials and _nonempty_file(Path(credentials).expanduser()):
            return {
                "connected": True,
                "mode": "env",
                "auth_path": "GOOGLE_APPLICATION_CREDENTIALS",
            }

        home = self._home()
        for path in (home / "gemini-credentials.json", home / "oauth_creds.json"):
            if _nonempty_file(path):
                return {"connected": True, "mode": "external", "auth_path": str(path)}

        if _env_file_has_key(home / ".env"):
            return {"connected": True, "mode": "external", "auth_path": str(home / ".env")}

        adc = _adc_path()
        if _nonempty_file(adc):
            return {"connected": True, "mode": "external", "auth_path": str(adc)}

        return {"connected": False, "mode": "", "auth_path": str(home)}


def _adc_path() -> Path:
    configured = os.environ.get("CLOUDSDK_CONFIG", "").strip()
    root = Path(configured).expanduser() if configured else Path.home() / ".config" / "gcloud"
    return root / "application_default_credentials.json"


def _nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _env_file_has_key(path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return False
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        if key.strip() in _API_KEY_ENV_VARS and value.strip().strip("'\""):
            return True
    return False
