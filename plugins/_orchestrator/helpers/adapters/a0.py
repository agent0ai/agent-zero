from __future__ import annotations

import os
import shutil
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter

# Inside the Agent Zero container, the local WebUI listens on port 80,
# so the default target is the instance running this very plugin.
DEFAULT_HOST = "http://localhost:80"
DEFAULT_DOCKER_A0_BINARY = "/opt/venv/bin/a0"


class AgentZeroAdapter(TerminalAgentAdapter):
    """Delegate tasks to an Agent Zero instance via `a0 headless` one-shot mode.

    Host resolution: adapter config `host` > AGENT_ZERO_HOST env > local
    instance (http://localhost:80 inside the container).
    """

    id = "a0"
    title = "Agent Zero (headless)"
    binary = "a0"
    install_hint = "pip install git+https://github.com/agent0ai/a0-connector.git@development"
    description = "Delegate to this or another Agent Zero instance through a0 headless."

    # --- connection ----------------------------------------------------------

    def resolve_binary(self, config: dict[str, Any] | None = None) -> str:
        binary = super().resolve_binary(config)
        if binary == self.binary and shutil.which(binary) is None:
            bundled = Path(DEFAULT_DOCKER_A0_BINARY)
            if bundled.is_file():
                return str(bundled)
        return binary

    def resolve_host(self, config: dict[str, Any] | None = None) -> str:
        cfg = config or {}
        host = str(cfg.get("host") or "").strip()
        if host:
            return host
        env_host = os.environ.get("AGENT_ZERO_HOST", "").strip()
        return env_host or DEFAULT_HOST

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        host = self.resolve_host(config)
        if _probe(host):
            return {"connected": True, "mode": "external", "auth_path": host}
        return {"connected": False, "mode": "", "auth_path": host}


def _probe(host_url: str) -> bool:
    url = host_url if "://" in host_url else f"http://{host_url}"
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False
