from helpers.api import ApiHandler, Input, Output, Request, Response
from plugins._pin_to_top.helpers.pins import toggle_pin


class TogglePin(ApiHandler):
    """Toggle one chat, task, or project pin."""

    async def process(self, input: Input, request: Request) -> Output:
        try:
            if input.get("item_id") is None:
                raise ValueError("item_id is required")
            pinned, timestamp = toggle_pin(
                str(input.get("kind", "")),
                str(input.get("item_id", "")),
            )
        except ValueError as error:
            return Response(str(error), 400)

        return {
            "ok": True,
            "pinned": pinned,
            "timestamp": timestamp,
        }
