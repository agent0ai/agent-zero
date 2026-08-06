from __future__ import annotations

import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._kokoro_tts.helpers import migration, runtime


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        migration.ensure_migrated()

        cfg = runtime.get_config()
        remote_url = cfg.get("remote_url", "")

        # Local model status (always reported)
        package_version = ""
        package_error = ""
        try:
            package_version = importlib.metadata.version("kokoro")
        except Exception as e:
            package_error = str(e)

        result = {
            "plugin": "_kokoro_tts",
            "enabled": runtime.is_globally_enabled(),
            "config": cfg,
            "model": {
                "ready": await runtime.is_downloaded(),
                "loading": runtime.is_updating_model,
                "version": package_version,
                "error": package_error or None,
            },
            "fallback": "Browser-native speechSynthesis remains the fallback when Kokoro is disabled.",
        }

        # Remote health status (only if configured)
        if remote_url:
            remote_healthy, remote_error = await runtime.is_remote_healthy()
            result["remote"] = {
                "url": remote_url,
                "healthy": remote_healthy,
                "error": remote_error or None,
            }

        return result
