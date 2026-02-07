from python.helpers.api import ApiHandler
from python.api.github_callback import get_github_auth
from flask import Request


class GithubUser(ApiHandler):
    """Get current GitHub user info and connection status"""

    async def process(self, input: dict, request: Request) -> dict:
        auth_data = get_github_auth()

        if not auth_data:
            return {"connected": False, "user": None}

        access_token = auth_data.get("access_token")
        user = auth_data.get("user")

        return {
            "connected": bool(access_token and user),
            "user": user,
        }
