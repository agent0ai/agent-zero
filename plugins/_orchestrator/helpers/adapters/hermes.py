from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


_AUTH_ENV_VARS = {
    "ALIBABA_CODING_PLAN_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_TOKEN",
    "ARCEEAI_API_KEY",
    "AZURE_FOUNDRY_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "COPILOT_GITHUB_TOKEN",
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "GEMINI_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GLM_API_KEY",
    "GMI_API_KEY",
    "GOOGLE_API_KEY",
    "HF_TOKEN",
    "KILOCODE_API_KEY",
    "KIMI_API_KEY",
    "KIMI_CODING_API_KEY",
    "MINIMAX_API_KEY",
    "NVIDIA_API_KEY",
    "NOVITA_API_KEY",
    "OLLAMA_API_KEY",
    "OPENAI_API_KEY",
    "OPENCODE_GO_API_KEY",
    "OPENCODE_ZEN_API_KEY",
    "OPENROUTER_API_KEY",
    "STEPFUN_API_KEY",
    "TOKENHUB_API_KEY",
    "XAI_API_KEY",
    "ZAI_API_KEY",
}

_SECRET_KEYS = {
    "access_token",
    "agent_key",
    "api_key",
    "id_token",
    "refresh_token",
    "runtime_api_key",
    "token",
}


class HermesAgentAdapter(TerminalAgentAdapter):
    id = "hermes"
    title = "Hermes Agent"
    binary = "hermes"
    install_hint = "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
    description = "Nous Research Hermes Agent CLI in quiet headless chat mode."

    def _home(self) -> Path:
        configured = os.environ.get("HERMES_HOME", "").strip()
        return Path(configured).expanduser() if configured else Path.home() / ".hermes"

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        env_var = next((name for name in sorted(_AUTH_ENV_VARS) if os.environ.get(name)), "")
        if env_var:
            return {"connected": True, "mode": "env", "auth_path": env_var}

        home = self._home()
        env_path = home / ".env"
        try:
            if _env_file_has_key(env_path):
                return {"connected": True, "mode": "external", "auth_path": str(env_path)}
        except OSError as exc:
            return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        auth_path = home / "auth.json"
        try:
            if _auth_store_has_credentials(auth_path):
                return {"connected": True, "mode": "external", "auth_path": str(auth_path)}
        except OSError as exc:
            return {"connected": False, "mode": "", "auth_path": "", "error": str(exc)}

        return {"connected": False, "mode": "", "auth_path": ""}


def _env_file_has_key(path: Path) -> bool:
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        if key.strip() in _AUTH_ENV_VARS and value.strip().strip("'\""):
            return True
    return False


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
            if str(key) in _SECRET_KEYS and isinstance(item, str) and len(item.strip()) > 3:
                return True
            if _contains_secret(item):
                return True
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return False
