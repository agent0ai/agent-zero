from python.helpers.api import ApiHandler, Request, Response

from python.helpers.dotenv import get_dotenv_value
from python.helpers.snapshot import build_snapshot


class Poll(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        timezone = input.get("timezone", get_dotenv_value("DEFAULT_USER_TIMEZONE", "UTC"))
        return await build_snapshot(
            context=input.get("context"),
            log_from=input.get("log_from", 0),
            notifications_from=input.get("notifications_from", 0),
            timezone=timezone,
        )
