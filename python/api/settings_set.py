from python.helpers.api import ApiHandler, Request, Response

from python.helpers import settings

from typing import Any


class SetSettings(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        new_set = settings.convert_in(input)
        settings.set_settings(new_set)
        effective = settings.get_effective_settings()
        set_out = settings.convert_out(effective)
        return {"settings": set_out}
