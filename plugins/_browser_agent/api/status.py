import importlib.metadata

from helpers.api import ApiHandler, Request, Response
from plugins._browser_agent.helpers.playwright import (
    get_playwright_binary,
    get_playwright_cache_dir,
)
from plugins._model_config.helpers.model_config import get_chat_model_config


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        cfg = get_chat_model_config()
        binary = get_playwright_binary()

        browser_use_ok = False
        browser_use_error = ""
        browser_use_version = ""
        try:
            import browser_use  # noqa: F401

            browser_use_ok = True
            browser_use_version = importlib.metadata.version("browser-use")
        except Exception as e:
            browser_use_error = str(e)

        return {
            "plugin": "_browser_agent",
            "model_source": "Main Model via _model_config",
            "model": {
                "provider": cfg.get("provider", ""),
                "name": cfg.get("name", ""),
                "vision": bool(cfg.get("vision", False)),
            },
            "playwright": {
                "cache_dir": get_playwright_cache_dir(),
                "binary_found": bool(binary),
                "binary_path": str(binary) if binary else "",
            },
            "browser_use": {
                "import_ok": browser_use_ok,
                "version": browser_use_version,
                "error": browser_use_error,
            },
        }
