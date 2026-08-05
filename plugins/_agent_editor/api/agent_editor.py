from __future__ import annotations

from typing import Any

from agent import AgentContext
from helpers import projects
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
            if action in {"plan_remove_changes", "remove_changes"}:
                profile_id = editor.validate_profile_id(input.get("profile_id"))
                plan = editor.plan_remove_changes(
                    profile_id,
                    context,
                    destructive=bool(input.get("destructive")),
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
                plan = editor.plan_delete_custom(profile_id, context)
                if action == "plan_delete":
                    return {
                        "ok": True,
                        **plan.response(),
                        "impact": editor.delete_impact(profile_id, context),
                    }
                if input.get("confirm") is not True:
                    raise ValueError("Deleting a custom agent requires confirmation.")
                return {"ok": True, **editor.apply_change_plan(plan)}
            raise ValueError(f"Unknown Agent Editor action: {action}")
        except ValueError as exc:
            return Response(status=400, response=str(exc), mimetype="text/plain")


def _context(input: dict[str, Any]) -> Any:
    context_id = str(input.get("context_id") or "").strip()
    if context_id:
        context = AgentContext.get(context_id)
        if not context:
            raise ValueError("Chat context not found.")
        return context
    project_name = str(input.get("project_name") or "").strip()
    if project_name:
        project_name = projects.validate_project_name(project_name)
    return editor._EditorContext(project_name)
