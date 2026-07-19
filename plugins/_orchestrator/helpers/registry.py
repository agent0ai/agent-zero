from __future__ import annotations

from typing import Any

from plugins._orchestrator.helpers.adapters.a0 import AgentZeroAdapter
from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter
from plugins._orchestrator.helpers.adapters.claude import ClaudeCodeAdapter
from plugins._orchestrator.helpers.adapters.codex import CodexAdapter
from plugins._orchestrator.helpers.adapters.cursor import CursorCliAdapter
from plugins._orchestrator.helpers.adapters.gemini import GeminiCliAdapter
from plugins._orchestrator.helpers.adapters.grok import GrokBuildAdapter
from plugins._orchestrator.helpers.adapters.hermes import HermesAgentAdapter
from plugins._orchestrator.helpers.adapters.opencode import OpenCodeAdapter

# Register new terminal agent adapters here.
_ADAPTERS: dict[str, TerminalAgentAdapter] = {
    adapter.id: adapter
    for adapter in (
        AgentZeroAdapter(),
        CodexAdapter(),
        ClaudeCodeAdapter(),
        CursorCliAdapter(),
        GeminiCliAdapter(),
        GrokBuildAdapter(),
        HermesAgentAdapter(),
        OpenCodeAdapter(),
    )
}


def get_adapter(agent_id: str) -> TerminalAgentAdapter:
    adapter = _ADAPTERS.get(str(agent_id or "").strip().lower())
    if adapter is None:
        known = ", ".join(sorted(_ADAPTERS))
        raise ValueError(f"Unknown terminal agent '{agent_id}'. Available: {known}")
    return adapter


def list_adapters() -> list[TerminalAgentAdapter]:
    return list(_ADAPTERS.values())


def adapter_config(agent_id: str, plugin_config: dict[str, Any] | None) -> dict[str, Any]:
    source = plugin_config if isinstance(plugin_config, dict) else {}
    raw = source.get(agent_id)
    return raw if isinstance(raw, dict) else {}
