"""POST /api/plugins/_a0_connector/v1/launcher_gateway_status."""
from __future__ import annotations

from helpers.api import Request, Response

import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.ws_runtime import launcher_gateway_status


class LauncherGatewayStatus(connector_base.ProtectedConnectorApiHandler):
    """Return the current Launcher-owned host gateway state."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        return launcher_gateway_status()
