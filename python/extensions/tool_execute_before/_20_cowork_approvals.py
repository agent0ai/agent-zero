from __future__ import annotations

import uuid
from typing import Any

from agent import UserMessage
from python.helpers import cowork
from python.helpers.extension import Extension
from python.helpers.secrets import get_secrets_manager
from python.helpers.settings import get_settings

DEFAULT_IMPACTFUL_TOOLS = {
    "code_execution_tool",
    "email",
    "email_advanced",
    "memory_delete",
    "memory_forget",
    "memory_save",
    "scheduler",
    "browser_agent",
}


def _mask_value(secrets_mgr, value: Any) -> Any:
    if isinstance(value, str):
        return secrets_mgr.mask_values(value)
    if isinstance(value, list):
        return [_mask_value(secrets_mgr, item) for item in value]
    if isinstance(value, dict):
        return {k: _mask_value(secrets_mgr, v) for k, v in value.items()}
    return value


def _mask_args(agent, args: dict[str, Any]) -> dict[str, Any]:
    secrets_mgr = get_secrets_manager(agent.context)
    return {k: _mask_value(secrets_mgr, v) for k, v in (args or {}).items()}


def _is_impactful(tool_name: str, tool_args: dict[str, Any]) -> bool:
    if tool_name == "code_execution_tool":
        runtime = str(tool_args.get("runtime", "")).lower().strip()
        return runtime in {"terminal", "python", "nodejs"}
    return tool_name in DEFAULT_IMPACTFUL_TOOLS


def _parse_tool_list(raw_value: str) -> set[str]:
    if not raw_value:
        return set()
    items: list[str] = []
    for line in raw_value.replace(",", "\n").splitlines():
        cleaned = line.strip()
        if cleaned:
            items.append(cleaned)
    return set(items)


class CoworkApprovals(Extension):
    async def execute(self, tool_args: dict[str, Any] | None = None, tool_name: str = "", **kwargs):
        settings = get_settings()
        if not settings.get("cowork_enabled"):
            return

        tool_args = tool_args or {}
        allowed_paths = settings.get("cowork_allowed_paths", [])
        require_approvals = bool(settings.get("cowork_require_approvals", True))
        configured_tools = _parse_tool_list(settings.get("cowork_impactful_tools", ""))
        impactful_tools = configured_tools or DEFAULT_IMPACTFUL_TOOLS

        reason = ""
        blocked_paths: list[str] = []
        if allowed_paths:
            for path in cowork.extract_paths(tool_args):
                if path and not cowork.is_path_allowed(path, allowed_paths):
                    blocked_paths.append(path)
            if blocked_paths:
                reason = "Path outside allowed folders"

        if not reason and require_approvals:
            if tool_name in impactful_tools and _is_impactful(tool_name, tool_args):
                reason = "Impactful action"

        if not reason:
            return

        fingerprint = cowork.build_action_fingerprint(tool_name, tool_args)
        approvals = cowork.get_approvals(self.agent.context)

        approved = cowork.find_matching_approval(approvals, fingerprint, self.agent.number)
        if approved:
            cowork.mark_consumed(approved, consumed_by=self.agent.agent_name)
            return

        denied = cowork.find_approval_by_status(approvals, fingerprint, self.agent.number, "denied")
        if denied:
            await self._intervene(
                f"Cowork approval denied for {tool_name}. Update approvals to proceed."
            )
            return

        pending = cowork.find_approval_by_status(approvals, fingerprint, self.agent.number, "pending")
        if pending:
            await self._intervene(
                f"Cowork approval pending for {tool_name}. Approve in settings to proceed."
            )
            return

        summary_args = cowork.summarize_args(tool_args)
        safe_args = _mask_args(self.agent, summary_args)
        approval = {
            "id": str(uuid.uuid4()),
            "status": "pending",
            "created_at": cowork._now_iso(),
            "resolved_at": None,
            "resolved_by": None,
            "agent_number": self.agent.number,
            "agent_name": self.agent.agent_name,
            "inherit": True,
            "tool_name": tool_name,
            "tool_args": safe_args,
            "paths": blocked_paths,
            "reason": reason,
            "fingerprint": fingerprint,
            "consumed": False,
        }
        cowork.add_approval(self.agent.context, approval)

        await self._intervene(
            f"Cowork approval required for {tool_name}. Open Settings → Cowork to approve."
        )

    async def _intervene(self, message: str):
        self.agent.intervention = UserMessage(message=message, attachments=[], system_message=[])
        await self.agent.handle_intervention()
