import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._kokoro_tts.helpers import migration, runtime


def _pkg_version(name: str) -> tuple[str, str]:
    try:
        return importlib.metadata.version(name), ""
    except Exception as e:
        return "", str(e)


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        migration.ensure_migrated()

        cfg = runtime.get_config()
        py_version, py_error = _pkg_version("kokoro")
        onnx_version, onnx_error = _pkg_version("kokoro_onnx")

        return {
            "plugin": "_kokoro_tts",
            "enabled": runtime.is_globally_enabled(),
            "config": cfg,
            "engine": cfg.get("engine", "kokoro_py"),
            "model": {
                "ready": await runtime.is_downloaded(),
                "loading": await runtime.is_downloading(),
            },
            "package": {
                "version": py_version,
                "error": py_error,
            },
            "onnx_package": {
                "version": onnx_version,
                "error": onnx_error,
            },
            "fallback": "Browser-native speechSynthesis remains the fallback when Kokoro is disabled.",
        }
