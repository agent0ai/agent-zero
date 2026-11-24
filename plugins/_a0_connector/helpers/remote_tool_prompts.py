from __future__ import annotations

from plugins._a0_connector.helpers import ws_runtime


def remote_tool_prompt_availability(context_id: str) -> dict[str, bool]:
    """Return which connector remote tools should be advertised in prompts."""
    candidates = ws_runtime.remote_tool_sids_for_context(context_id)
    return {
        "code_execution_remote": any(
            _remote_exec_prompt_available(sid) for sid in candidates
        ),
        "input_remote": any(
            _remote_exec_prompt_available(sid) for sid in candidates
        ),
        "text_editor_remote": any(
            _remote_file_prompt_available(sid) for sid in candidates
        ),
    }


def _remote_file_prompt_available(sid: str) -> bool:
    metadata = ws_runtime.remote_file_metadata_for_sid(sid) or {}
    return bool(metadata.get("enabled"))


def _remote_exec_prompt_available(sid: str) -> bool:
    metadata = ws_runtime.remote_exec_metadata_for_sid(sid) or {}
    return bool(metadata.get("enabled"))
