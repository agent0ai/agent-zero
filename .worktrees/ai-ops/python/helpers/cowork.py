from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from python.helpers import files

if TYPE_CHECKING:
    from collections.abc import Iterable

APPROVALS_KEY = "cowork_approvals"

PATH_KEYS = {
    "path",
    "paths",
    "file",
    "files",
    "file_path",
    "file_paths",
    "directory",
    "folder",
    "output_dir",
    "output_path",
    "input_path",
    "target_path",
    "source_path",
    "folder_path",
    "project_path",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _json_fingerprint(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_action_fingerprint(tool_name: str, tool_args: dict[str, Any]) -> str:
    return _json_fingerprint(
        {
            "tool_name": tool_name,
            "tool_args": tool_args,
        }
    )


def summarize_args(tool_args: dict[str, Any], max_len: int = 240) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in (tool_args or {}).items():
        if isinstance(value, str) and len(value) > max_len:
            summary[key] = value[:max_len] + "...(truncated)"
        else:
            summary[key] = value
    return summary


def resolve_path(path: str) -> str:
    if not path:
        return ""
    if path.startswith("/a0"):
        return os.path.realpath(files.fix_dev_path(path))
    if os.path.isabs(path):
        return os.path.realpath(path)
    return os.path.realpath(files.get_abs_path(path))


def is_path_allowed(path: str, allowed_roots: Iterable[str]) -> bool:
    resolved = resolve_path(path)
    for root in allowed_roots:
        root_resolved = resolve_path(root)
        try:
            if os.path.commonpath([resolved, root_resolved]) == root_resolved:
                return True
        except ValueError:
            continue
    return False


def extract_paths(tool_args: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key, value in (tool_args or {}).items():
        if key not in PATH_KEYS:
            continue
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    paths.append(item)
    return paths


def get_approvals(context) -> list[dict[str, Any]]:
    return context.data.get(APPROVALS_KEY, [])


def add_approval(context, approval: dict[str, Any]) -> dict[str, Any]:
    approvals = get_approvals(context)
    approvals.append(approval)
    context.data[APPROVALS_KEY] = approvals
    return approval


def update_approval(context, approval_id: str, status: str, resolved_by: str | None = None) -> dict[str, Any] | None:
    approvals = get_approvals(context)
    for approval in approvals:
        if approval.get("id") == approval_id:
            approval["status"] = status
            approval["resolved_at"] = _now_iso()
            if resolved_by:
                approval["resolved_by"] = resolved_by
            return approval
    return None


def mark_consumed(approval: dict[str, Any], consumed_by: str | None = None) -> dict[str, Any]:
    approval["consumed"] = True
    approval["consumed_at"] = _now_iso()
    if consumed_by:
        approval["consumed_by"] = consumed_by
    return approval


def _matches_agent(approval: dict[str, Any], agent_number: int) -> bool:
    approved_agent = approval.get("agent_number")
    if approved_agent is None:
        return True
    if approval.get("inherit"):
        return approved_agent <= agent_number
    return approved_agent == agent_number


def find_matching_approval(
    approvals: list[dict[str, Any]],
    fingerprint: str,
    agent_number: int,
) -> dict[str, Any] | None:
    for approval in approvals:
        if approval.get("fingerprint") != fingerprint:
            continue
        if approval.get("status") != "approved":
            continue
        if approval.get("consumed"):
            continue
        if _matches_agent(approval, agent_number):
            return approval
    return None


def find_approval_by_status(
    approvals: list[dict[str, Any]],
    fingerprint: str,
    agent_number: int,
    status: str,
) -> dict[str, Any] | None:
    for approval in approvals:
        if approval.get("fingerprint") != fingerprint:
            continue
        if approval.get("status") != status:
            continue
        if approval.get("consumed"):
            continue
        if _matches_agent(approval, agent_number):
            return approval
    return None
