from helpers.api import ApiHandler, Request, Response

from helpers.state_snapshot import build_snapshot
from helpers.team_access import request_scope


class Poll(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        scope = request_scope()
        return await build_snapshot(
            context=input.get("context"),
            log_from=input.get("log_from", 0),
            notifications_from=input.get("notifications_from", 0),
            timezone=input.get("timezone"),
            **({"member_scope": scope} if scope is not None else {}),
        )
