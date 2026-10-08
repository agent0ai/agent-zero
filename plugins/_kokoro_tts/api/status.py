import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._kokoro_tts.helpers import migration, runtime


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        migration.ensure_migrated()
        config = runtime.get_config()
        engine = "paradee" if config["voice"] == "paradee" else "kokoro"
        package_name = "onnxruntime" if engine == "paradee" else "kokoro"

        package_version = ""
        package_error = ""
        try:
            package_version = importlib.metadata.version(package_name)
        except Exception as e:
            package_error = str(e)

        return {
            "plugin": "_kokoro_tts",
            "enabled": runtime.is_globally_enabled(),
            "config": config,
            "engine": engine,
            "model": {
                "ready": await runtime.is_downloaded(config),
                "loading": await runtime.is_downloading(config),
            },
            "package": {
                "name": package_name,
                "version": package_version,
                "error": package_error,
            },
            "fallback": "Browser-native speechSynthesis remains the fallback when local TTS is disabled.",
        }
