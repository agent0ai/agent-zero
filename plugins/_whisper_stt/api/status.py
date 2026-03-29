import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._whisper_stt.helpers import migration, runtime


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        migration.ensure_config_seeded()

        package_version = ""
        package_error = ""
        try:
            package_version = importlib.metadata.version("openai-whisper")
        except Exception as e:
            package_error = str(e)

        return {
            "plugin": "_whisper_stt",
            "enabled": runtime.is_globally_enabled(),
            "config": runtime.get_config(),
            "model": {
                "ready": await runtime.is_downloaded(),
                "loading": await runtime.is_downloading(),
                "loaded_model": runtime.get_loaded_model_name(),
            },
            "package": {
                "version": package_version,
                "error": package_error,
            },
        }
