import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._kokoro_tts.helpers import migration, runtime


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        migration.ensure_migrated()

        package_version = ""
        package_error = ""
        try:
            package_version = importlib.metadata.version("kokoro")
        except Exception as e:
            package_error = str(e)

        return {
            "plugin": "_kokoro_tts",
            "enabled": runtime.is_globally_enabled(),
            "config": runtime.get_config(),
            "model": {
                "ready": await runtime.is_downloaded(),
                "loading": await runtime.is_downloading(),
            },
            "package": {
                "version": package_version,
                "error": package_error,
            },
            "fallback": "Browser-native speechSynthesis remains the fallback when Kokoro is disabled.",
        }
