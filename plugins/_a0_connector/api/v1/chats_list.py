"""POST /api/plugins/_a0_connector/v1/chats_list."""
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


class ChatsList(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext

        contexts: list[dict[str, object]] = []
        for context in AgentContext.all():
            data = context.output()
            project = _project_metadata(context, data)
            contexts.append(
                {
                    "id": context.id,
                    "name": data.get("name") or "",
                    "no": data.get("no", getattr(context, "no", None)),
                    "created_at": data.get("created_at"),
                    "last_message": data.get("last_message"),
                    "running": data.get("running", False),
                    "project": project,
                    "project_name": context.get_data("project") or "",
                    "agent_profile": getattr(context.agent0.config, "profile", "default")
                    if context.agent0
                    else "default",
                }
            )

        return {
            "contexts": contexts,
            "chats": contexts,
        }
