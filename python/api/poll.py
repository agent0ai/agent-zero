from python.helpers.api import ApiHandler, Request, Response
from python.helpers.state_snapshot import build_snapshot


class Poll(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        return await build_snapshot(
            context=input.get("context"),
            log_from=input.get("log_from", 0),
            notifications_from=input.get("notifications_from", 0),
            timezone=input.get("timezone"),
        )
