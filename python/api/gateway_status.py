"""Gateway status endpoint.

Returns connection status, message counts, and health for all
registered messaging channels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from python.helpers import gateway
from python.helpers.api import ApiHandler
from python.helpers.channel_factory import ChannelFactory

if TYPE_CHECKING:
    from flask import Request


class GatewayStatus(ApiHandler):
    """Returns status of all registered messaging channels."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request):
        # Optional: filter to a single channel
        channel = request.args.get("channel", "") or input.get("channel", "")
        available = ChannelFactory.available()
        stats = gateway.stats()

        if channel:
            if channel not in available:
                return {"error": f"Unknown channel: {channel}"}
            return {"channels": [{"name": channel, "registered": True}], "gateway": stats}

        return {
            "channels": [{"name": name, "registered": True} for name in available],
            "gateway": stats,
        }
