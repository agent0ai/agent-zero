"""Heartbeat configuration endpoint.

GET: Returns current heartbeat config (enabled, interval, last_run, etc.)
POST: Updates heartbeat settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from python.helpers.api import ApiHandler

if TYPE_CHECKING:
    from flask import Request


class HeartbeatConfig(ApiHandler):
    """Read and update heartbeat daemon configuration."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request):
        from python.helpers.heartbeat import (
            get_heartbeat_config,
            trigger_heartbeat,
            update_heartbeat_config,
        )

        # GET — return current config + running state
        if request.method == "GET" or not input:
            from python.helpers.heartbeat import HeartbeatDaemon

            config = get_heartbeat_config()
            config["running"] = HeartbeatDaemon.get().is_running()
            return config

        # POST with action=trigger — run immediately
        if input.get("action") == "trigger":
            result = trigger_heartbeat()
            return {"status": "triggered", "run": result}

        # POST — update configuration
        allowed_keys = {"enabled", "interval_seconds", "heartbeat_path"}
        updates = {k: v for k, v in input.items() if k in allowed_keys}
        if not updates:
            return {"error": "No valid fields to update"}

        # Validate interval
        if "interval_seconds" in updates:
            interval = int(updates["interval_seconds"])
            if interval < 60:
                return {"error": "interval_seconds must be at least 60"}
            if interval > 86400:
                return {"error": "interval_seconds must be at most 86400 (24h)"}
            updates["interval_seconds"] = interval

        config = update_heartbeat_config(**updates)
        return config
