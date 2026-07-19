from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from helpers import files


class TerminalAgentAdapter(ABC):
    """Contract every terminal coding agent status adapter must implement."""

    id: str = ""
    title: str = ""
    binary: str = ""
    install_hint: str = ""
    description: str = ""

    # --- environment -----------------------------------------------------

    def data_dir(self) -> Path:
        """Plugin-owned private directory for this adapter (auth, state)."""
        path = Path(
            files.get_abs_path("usr", "plugins", "_orchestrator", "data", self.id)
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve_binary(self, config: dict[str, Any] | None = None) -> str:
        cfg = config if isinstance(config, dict) else {}
        configured = str(cfg.get("binary") or "").strip()
        return configured or self.binary

    def is_installed(self, config: dict[str, Any] | None = None) -> bool:
        binary = self.resolve_binary(config)
        if not binary:
            return False
        if os.path.isabs(binary):
            return Path(binary).is_file() and os.access(binary, os.X_OK)
        return shutil.which(binary) is not None

    # --- authentication ----------------------------------------------------

    @abstractmethod
    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return {connected: bool, mode: 'plugin'|'external'|'', auth_path: str}."""

    def supports_device_login(self) -> bool:
        return False

    def start_device_login(self) -> dict[str, Any]:
        raise NotImplementedError(f"{self.id} does not support device login.")

    def poll_device_login(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(f"{self.id} does not support device login.")

    def can_disconnect(self, config: dict[str, Any] | None = None) -> bool:
        return False

    def disconnect(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(f"{self.id} does not support disconnect.")
