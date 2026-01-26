from python.helpers.api import ApiHandler
from flask import Request, session
import os
import secrets


class GithubOauth(ApiHandler):
    """Initiate GitHub OAuth flow"""

    async def process(self, input: dict, request: Request) -> dict:
        client_id = os.getenv("GITHUB_CLIENT_ID", "")
        redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:55080/github_callback")

        if not client_id:
            return {"success": False, "error": "GitHub client ID not configured. Set GITHUB_CLIENT_ID in .env"}

        # Generate and store state for CSRF protection
        state = secrets.token_urlsafe(32)
        session["github_oauth_state"] = state

        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=repo,user"
            f"&state={state}"
        )

        return {"success": True, "auth_url": auth_url}
