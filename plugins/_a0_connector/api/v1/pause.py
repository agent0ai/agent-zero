"""POST /api/plugins/_a0_connector/v1/pause."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.ws_runtime import abort_transfers_for_context


class Pause(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext

        context_id = str(input.get("context_id", "")).strip()
        raw_paused = input.get("paused", True)
        if isinstance(raw_paused, str):
            paused = raw_paused.strip().lower() not in {"", "0", "false", "no", "off"}
        else:
            paused = bool(raw_paused)

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

        if paused and not context.is_running():
            return Response(
                response='{"error": "Context is not currently running"}',
                status=409,
                mimetype="application/json",
            )

        context.paused = paused
        if paused:
            await abort_transfers_for_context(
                context_id,
                reason="chat paused during transfer",
            )
        return {
            "ok": True,
            "context_id": context_id,
            "paused": paused,
            "status": "paused" if paused else "running",
            "message": "Agent paused." if paused else "Agent unpaused.",
        }
