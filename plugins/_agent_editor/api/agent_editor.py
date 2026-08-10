from __future__ import annotations

from pathlib import Path
from typing import Any

from agent import AgentContext
from helpers import projects, subagents
from helpers.api import ApiHandler, Request, Response
from plugins._agent_editor.helpers import editor


class AgentEditor(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = str(input.get("action") or "list").strip().lower()
            context = _context(input)

            if action == "list":
                return {"ok": True, "profiles": editor.list_profiles(context)}
            if action == "load":
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                return {
                    "ok": True,
                    "state": editor.build_editor_state(profile_id, context),
                }
            if action in {"plan", "save"}:
                patch = input.get("patch")
                plan = editor.build_change_plan(patch, context)
                if action == "plan":
                    return {"ok": True, **plan.response()}
                receipt = editor.apply_change_plan(plan)
                profile_id = editor.validate_profile_id(patch.get("profile_id"))
                return {
                    "ok": True,
                    **receipt,
                    "effective_profile": editor.build_profile_state(profile_id, context),
                }
            if action == "set_enabled":
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                enabled = input.get("enabled")
                if not isinstance(enabled, bool):
                    raise ValueError("Agent availability must be true or false.")
                if not enabled:
                    _reject_running_profile(profile_id, context, "Disable")
                receipt = editor.set_profile_enabled(profile_id, enabled, context)
                return {
                    "ok": True,
                    **receipt,
                    **_active_profile(input),
                }
            if action == "duplicate":
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                plan, title = editor.plan_duplicate_profile(profile_id, context)
                receipt = editor.apply_change_plan(plan)
                return {
                    "ok": True,
                    **receipt,
                    "profile_id": plan.profile_id,
                    "title": title,
                    "profiles": editor.list_profiles(context),
                }
            if action in {"plan_remove_changes", "remove_changes"}:
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                destructive = input.get("destructive", False)
                if not isinstance(destructive, bool):
                    raise ValueError("Destructive removal must be true or false.")
                if (
                    action == "remove_changes"
                    and destructive
                    and input.get("confirm") is not True
                ):
                    raise ValueError(
                        "Deleting all profile customizations requires confirmation."
                    )
                plan = editor.plan_remove_changes(
                    profile_id,
                    context,
                    destructive=destructive,
                )
                if action == "plan_remove_changes":
                    return {"ok": True, **plan.response()}
                return {"ok": True, **editor.apply_change_plan(plan)}
            if action == "delete_impact":
                return {
                    "ok": True,
                    "impact": editor.delete_impact(input.get("profile_id"), context),
                }
            if action in {"plan_delete", "delete"}:
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                if action == "delete":
                    if input.get("confirm") is not True:
                        raise ValueError(
                            "Deleting a custom agent requires confirmation."
                        )
                    _reject_running_profile(profile_id, context, "Delete")
                plan = editor.plan_delete_custom(profile_id, context)
                if action == "plan_delete":
                    return {
                        "ok": True,
                        **plan.response(),
                        "impact": editor.delete_impact(profile_id, context),
                    }
                receipt = editor.apply_change_plan(plan)
                project_name = editor._context_project_name(context)
                projects.reconcile_agent_profiles(
                    project_name or None, all_scopes=not project_name
                )
                return {"ok": True, **receipt}
            raise ValueError(f"Unknown Agent Editor action: {action}")
        except ValueError as exc:
            return Response(status=400, response=str(exc), mimetype="text/plain")


def _context(input: dict[str, Any]) -> Any:
    context_id = str(input.get("context_id") or "").strip()
    if context_id:
        context = AgentContext.get(context_id)
        if not context:
            raise ValueError("Chat context not found.")
        _validate_project_scope(projects.get_context_project_name(context))
        return context
    project_name = _validate_project_scope(input.get("project_name"))
    return editor._EditorContext(project_name)


def _validate_project_scope(project_name: Any) -> str:
    value = str(project_name or "").strip()
    if not value:
        return ""
    value = projects.validate_project_name(value)
    if not Path(projects.get_project_folder(value)).is_dir():
        raise ValueError("Project not found.")
    return value


def _reject_running_profile(profile_id: str, context: Any, action: str) -> None:
    project_name = editor._context_project_name(context)
    for live_context in AgentContext.all():
        if (
            getattr(live_context.config, "profile", "") == profile_id
            and live_context.is_running()
            and (
                not project_name
                or projects.get_context_project_name(live_context) == project_name
            )
        ):
            raise ValueError(
                f"This agent is running. {action} it after the run finishes."
            )


def _active_profile(input: dict[str, Any]) -> dict[str, str]:
    context_id = str(input.get("active_context_id") or "").strip()
    context = AgentContext.get(context_id) if context_id else None
    if not context:
        return {}
    profile_id = str(getattr(context.config, "profile", "") or "")
    profiles = subagents.get_available_agents_dict(
        projects.get_context_project_name(context)
    )
    profile = profiles.get(profile_id)
    return {
        "active_profile": profile_id,
        "active_profile_label": profile.title if profile else profile_id,
    }
