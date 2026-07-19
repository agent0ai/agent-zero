"""POST /api/plugins/_a0_connector/v1/skills_activate."""
from __future__ import annotations

import json
from typing import Any

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


def _json_error(message: str, status: int) -> Response:
    return Response(
        response=json.dumps({"ok": False, "error": message}),
        status=status,
        mimetype="application/json",
    )


class SkillsActivate(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext
        from helpers import skills
        from helpers.persist_chat import save_tmp_chat

        context_id = str(input.get("context_id", "") or "").strip()
        if not context_id:
            return _json_error("context_id is required", 400)

        context = AgentContext.get(context_id)
        if context is None:
            return _json_error("Context not found", 404)

        entries = skills.normalize_active_skills([input.get("skill")])
        if not entries:
            return _json_error("skill is required", 400)

        skill_entry: dict[str, Any] = dict(entries[0])
        try:
            active_skills = skills.activate_chat_skill(context.get_agent(), skill_entry)
            save_tmp_chat(context)
        except ValueError as exc:
            return _json_error(str(exc), 400)

        return {
            "ok": True,
            "context_id": context.id,
            "skill": skill_entry,
            "active_skills": active_skills,
        }
