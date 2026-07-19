"""POST /api/plugins/_a0_connector/v1/chat_get."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


def _project_metadata(context, data: dict[str, object]) -> object:
    from helpers import projects

    project_key = getattr(projects, "CONTEXT_DATA_KEY_PROJECT", "project")
    return (
        data.get(project_key)
        or context.get_output_data(project_key)
        or context.get_data(project_key)
    )


class ChatGet(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext
        from plugins._a0_connector.helpers.event_bridge import (
            get_context_log_entries,
        )

        context_id = str(input.get("context_id", "")).strip()
        if not context_id:
            return Response(
                response='{"error": "context_id is required"}',
                status=400,
                mimetype="application/json",
            )

        context = AgentContext.get(context_id)
        if context is None:
            return Response(
                response='{"error": "Context not found"}',
                status=404,
                mimetype="application/json",
            )

        context_data = context.output()
        events, last_sequence = get_context_log_entries(context_id)
        project = _project_metadata(context, context_data)

        return {
            "context_id": context.id,
            "id": context.id,
            "name": context_data.get("name") or "",
            "no": context_data.get("no", getattr(context, "no", None)),
            "created_at": context_data.get("created_at"),
            "last_message": context_data.get("last_message"),
            "running": context_data.get("running", False),
            "project": project,
            "project_name": context.get_data("project") or "",
            "agent_profile": getattr(context.agent0.config, "profile", "default")
            if context.agent0
            else "default",
            "log_entries": len(events),
            "last_sequence": last_sequence,
        }
