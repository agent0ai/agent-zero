"""POST /api/plugins/_a0_connector/v1/agent_editor."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class AgentEditor(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from plugins._agent_editor.api.agent_editor import AgentEditor as CoreAgentEditor

        handler = CoreAgentEditor(self.app, self.thread_lock)
        return await handler.process(input, request)
