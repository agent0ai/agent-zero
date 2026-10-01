from helpers.api import ApiHandler, Request
from plugins._browser.helpers.config import build_browser_launch_config, get_browser_config
from plugins._browser.helpers.interactive_view import collect_status as collect_interactive_status
from plugins._browser.helpers.playwright import (
    get_playwright_binary,
    get_playwright_cache_dir,
    get_playwright_cache_dirs,
)
from plugins._browser.helpers.runtime import known_context_ids


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        browser_config = get_browser_config()
        launch_config = build_browser_launch_config(browser_config)
        runtime_binary = get_playwright_binary()
        chromium_binary = runtime_binary
        try:
            from plugins._a0_connector.helpers.ws_runtime import all_host_browser_metadata
        except ImportError:
            host_browser = {"connectors": []}
        else:
            host_browser = {"connectors": all_host_browser_metadata()}
        return {
            "plugin": "_browser",
            "playwright": {
                "cache_dir": get_playwright_cache_dir(),
                "cache_dirs": [str(path) for path in get_playwright_cache_dirs()],
                "binary_found": bool(runtime_binary),
                "install_required": not bool(runtime_binary),
                "binary_path": str(runtime_binary) if runtime_binary else "",
                "chromium_binary_path": str(chromium_binary) if chromium_binary else "",
                "launch_mode": launch_config["browser_mode"],
            },
            "extensions": {
                **launch_config["extensions"],
                "launch_mode": launch_config["browser_mode"],
                "requires_full_browser": launch_config["requires_full_browser"],
            },
            "host_browser": host_browser,
            "interactive_view": collect_interactive_status(),
            "contexts": known_context_ids(),
        }
