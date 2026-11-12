from helpers.api import ApiHandler, Input, Output, Request
from plugins._pin_to_top.helpers.pins import get_pins


class GetPins(ApiHandler):
    """Return persisted chat, task, and project pins."""

    async def process(self, input: Input, request: Request) -> Output:
        return {"ok": True, "pins": get_pins()}
