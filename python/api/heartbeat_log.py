"""Heartbeat execution log endpoint.

Returns the history of heartbeat runs with item-level results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from python.helpers.api import ApiHandler

if TYPE_CHECKING:
    from flask import Request


class HeartbeatLog(ApiHandler):
    """Returns heartbeat execution history."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request):
        from python.helpers.heartbeat import get_heartbeat_log

        limit = int(request.args.get("limit", "50") if request.method == "GET" else input.get("limit", 50))
        limit = max(1, min(limit, MAX_LOG_ENTRIES))
        log = get_heartbeat_log(limit)
        return {"log": log, "count": len(log)}


MAX_LOG_ENTRIES = 200
