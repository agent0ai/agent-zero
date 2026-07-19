from helpers.api import ApiHandler, Request, Response

from helpers import settings

from typing import Any


class SetSettings(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        frontend = input.get("settings", input)
        browser_timezone = input.get("browser_timezone")
        backend = settings.convert_in(settings.Settings(**frontend))
        backend = settings.set_settings(
            backend,
            browser_timezone=browser_timezone if isinstance(browser_timezone, str) else None,
        )
        out = settings.convert_out(backend)
        return dict(out)
