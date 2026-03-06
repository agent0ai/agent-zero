"""Gateway status endpoint.

Returns connection status, message counts, and health for all
registered messaging channels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from python.helpers.api import ApiHandler

if TYPE_CHECKING:
    from flask import Request
from python.helpers.gateway import Gateway


class GatewayStatus(ApiHandler):
    """Returns status of all registered messaging channels."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request):
        gateway = Gateway.get()

        # Optional: filter to a single channel
        channel = request.args.get("channel", "") or input.get("channel", "")

        if channel:
            status = gateway.get_channel_status(channel)
            if status is None:
                return {"error": f"Unknown channel: {channel}"}
            return {"channels": [status]}

        return {"channels": gateway.get_all_status()}
