"""Scoped, plugin-provided controls for connector composer bars."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class ComposerControls(connector_base.ProtectedConnectorApiHandler):
    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        from agent import AgentContext
        from helpers.extension import call_extensions_async

        context_id = str(input.get("context_id") or "").strip()
        if not context_id:
            return Response(status=400, response="Missing context_id")
        context = AgentContext.get(context_id)
        if context is None:
            return Response(status=404, response="Context not found")
        action = input.get("action", "list")
        if action not in ("list", "set"):
            return Response(status=400, response="Unknown composer control action")
        if action == "set":
            if not isinstance(input.get("control_id"), str) or not input["control_id"].strip():
                return Response(status=400, response="Missing control_id")
            if not isinstance(input.get("value"), str) or not isinstance(input.get("custom", False), bool):
                return Response(status=400, response="Invalid control value")

        controls: list[dict] = []
        result: dict = {"response": None}
        await call_extensions_async(
            "connector_controls", agent=context.agent0, action=action,
            input=input, controls=controls, result=result,
        )
        if action == "list":
            return {"ok": True, "controls": controls}
        response = result["response"]
        if isinstance(response, (dict, Response)):
            return response
        return Response(status=404, response="Composer control is unavailable")
