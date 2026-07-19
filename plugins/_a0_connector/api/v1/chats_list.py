"""POST /api/plugins/_a0_connector/v1/chats_list."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class ChatsList(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext

        contexts: list[dict[str, object]] = []
        for context in AgentContext.all():
            data = context.output()
            contexts.append(
                {
                    "id": context.id,
                    "name": data.get("name") or context.name or context.id,
                    "created_at": data.get("created_at"),
                    "last_message": data.get("last_message"),
                    "running": data.get("running", False),
                    "agent_profile": getattr(context.agent0.config, "profile", "default")
                    if context.agent0
                    else "default",
                }
            )

        return {
            "contexts": contexts,
            "chats": contexts,
        }
