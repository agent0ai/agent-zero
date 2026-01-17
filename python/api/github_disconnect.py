from python.helpers.api import ApiHandler
from python.api.github_callback import clear_github_auth
from flask import Request


class GithubDisconnect(ApiHandler):
    """Disconnect GitHub integration"""

    async def process(self, input: dict, request: Request) -> dict:
        clear_github_auth()
        return {"success": True, "message": "GitHub disconnected"}
