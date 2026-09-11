"""POST /api/plugins/_a0_connector/v1/chat_delete."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.ws_runtime import abort_transfers_for_context


class ChatDelete(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext
        from api.chat_remove import RemoveChat

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

        try:
            await abort_transfers_for_context(
                context_id,
                reason="chat deleted during transfer",
            )
            handler = RemoveChat(self.app, self.thread_lock)
            await handler.process({"context": context_id}, request)
        except Exception as exc:
            return Response(
                response=f'{{"error": "{str(exc)}"}}',
                status=500,
                mimetype="application/json",
            )

        return {"context_id": context_id, "status": "deleted"}
