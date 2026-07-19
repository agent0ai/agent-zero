from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter


class ClaudeCodeAdapter(TerminalAgentAdapter):
    id = "claude"
    title = "Claude Code"
    binary = "claude"
    install_hint = "npm install -g @anthropic-ai/claude-code"
    description = "Anthropic Claude Code CLI in non-interactive print mode."

    def _credentials_path(self) -> Path:
        config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
        root = Path(config_dir).expanduser() if config_dir else Path.home() / ".claude"
        return root / ".credentials.json"

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return {
                "connected": True,
                "mode": "env",
                "auth_path": "ANTHROPIC_API_KEY",
            }
        credentials = self._credentials_path()
        try:
            if credentials.is_file() and credentials.stat().st_size > 0:
                return {
                    "connected": True,
                    "mode": "external",
                    "auth_path": str(credentials),
                }
        except OSError as exc:
            return {
                "connected": False,
                "mode": "",
                "auth_path": "",
                "error": str(exc),
            }
        if not self.is_installed(config):
            return {"connected": False, "mode": "", "auth_path": ""}
        return {"connected": False, "mode": "", "auth_path": ""}

    def can_disconnect(self, config: dict[str, Any] | None = None) -> bool:
        return not os.environ.get("ANTHROPIC_API_KEY") and self._credentials_path().is_file()

    def disconnect(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return {
                "removed": False,
                "message": "ANTHROPIC_API_KEY is set in the environment.",
            }
        path = self._credentials_path()
        if path.exists():
            path.unlink()
            return {"removed": True, "mode": "external"}
        return {"removed": False, "message": "No Claude Code credentials found."}
