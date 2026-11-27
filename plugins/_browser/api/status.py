import asyncio

from helpers.api import ApiHandler, Request
from plugins._browser.helpers.config import CHROMIUM_EXECUTABLE, describe_browser_extensions, get_browser_config
from plugins._browser.helpers.interactive_view import collect_status as collect_interactive_status
from plugins._browser.helpers.sandbox import worker

from plugins._browser.helpers.runtime import known_context_ids, browser_startup_status


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            from plugins._a0_connector.helpers.ws_runtime import all_host_browser_metadata
        except ImportError:
            host_browser = {"connectors": []}
        else:
            host_browser = {"connectors": all_host_browser_metadata()}
        return {
            "plugin": "_browser",
            "startup": await asyncio.to_thread(browser_startup_status, str(input.get('context_id') or '')),
            "chromium": {
                "transport": "cdp-pipe",
                "ready": worker.ready,
                "binary_path": CHROMIUM_EXECUTABLE if worker.ready else "",
            },
            "extensions": describe_browser_extensions(get_browser_config()),
            "host_browser": host_browser,
            "interactive_view": collect_interactive_status(),
            "contexts": known_context_ids(),
        }
