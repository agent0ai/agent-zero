from __future__ import annotations

from typing import Any

from plugins._a0_connector.helpers import ws_runtime


REMOTE_TOOL_PROMPTS: dict[str, str] = {
    "code_execution_remote": "agent.system.tool.code_execution_remote.md",
    "computer_use_remote": "agent.system.tool.computer_use_remote.md",
    "text_editor_remote": "agent.system.tool.text_editor_remote.md",
}


def remote_tool_prompt_availability(context_id: str) -> dict[str, bool]:
    """Return which connector remote tools should be advertised in prompts."""
    candidates = ws_runtime.remote_tool_sids_for_context(context_id)
    return {
        "code_execution_remote": any(
            _remote_exec_prompt_available(sid) for sid in candidates
        ),
        "computer_use_remote": any(
            _computer_use_prompt_available(sid) for sid in candidates
        ),
        "text_editor_remote": any(
            _remote_file_prompt_available(sid) for sid in candidates
        ),
    }


def should_include_remote_tool_prompt(agent: Any, tool_name: str) -> bool:
    if tool_name not in REMOTE_TOOL_PROMPTS:
        return True

    context = getattr(agent, "context", None)
    context_id = str(getattr(context, "id", "") or "").strip()
    if not context_id:
        return False

    return bool(remote_tool_prompt_availability(context_id).get(tool_name))


def _remote_file_prompt_available(sid: str) -> bool:
    metadata = ws_runtime.remote_file_metadata_for_sid(sid) or {}
    return bool(metadata.get("enabled"))


def _remote_exec_prompt_available(sid: str) -> bool:
    metadata = ws_runtime.remote_exec_metadata_for_sid(sid) or {}
    return bool(metadata.get("enabled"))


def _computer_use_prompt_available(sid: str) -> bool:
    metadata = ws_runtime.computer_use_metadata_for_sid(sid) or {}
    status = str(metadata.get("status", "") or "").strip().lower()
    return bool(
        metadata.get("supported")
        and metadata.get("enabled")
        and status != "rearm required"
    )
