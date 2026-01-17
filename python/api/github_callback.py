from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle
from python.helpers import files
from flask import Request, Response, session, redirect
import os
import json
import httpx
import urllib.parse

GITHUB_AUTH_FILE = files.get_abs_path("tmp/github_auth.json")


def save_github_auth(data: dict):
    """Save GitHub auth data to file"""
    content = json.dumps(data, indent=2)
    files.write_file(GITHUB_AUTH_FILE, content)


def get_github_auth() -> dict | None:
    """Load GitHub auth data from file"""
    if os.path.exists(GITHUB_AUTH_FILE):
        content = files.read_file(GITHUB_AUTH_FILE)
        return json.loads(content)
    return None


def clear_github_auth():
    """Remove GitHub auth file"""
    if os.path.exists(GITHUB_AUTH_FILE):
        os.remove(GITHUB_AUTH_FILE)


class GithubCallback(ApiHandler):
    """Handle GitHub OAuth callback"""

    @staticmethod
    def requires_csrf() -> bool:
        return False  # OAuth callback comes from GitHub, not our frontend

    @staticmethod
    def get_methods() -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> Response:
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        # Handle user denial
        if error:
            return redirect(f"/?github_error={error}")

        if not code:
            return redirect("/?github_error=no_code")

        # Validate state for CSRF protection
        stored_state = session.pop("github_oauth_state", None)
        if not state or state != stored_state:
            return redirect("/?github_error=invalid_state")

        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")

        if not client_id or not client_secret:
            return redirect("/?github_error=not_configured")

        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for access token
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                    },
                    headers={"Accept": "application/json"},
                )

                if token_response.status_code != 200:
                    return redirect("/?github_error=token_exchange_failed")

                token_data = token_response.json()

                if "error" in token_data:
                    error_desc = token_data.get("error_description", token_data["error"])
                    return redirect(f"/?github_error={error_desc}")

                access_token = token_data.get("access_token")
                if not access_token:
                    return redirect("/?github_error=no_access_token")

                # Fetch user info
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )

                if user_response.status_code != 200:
                    return redirect("/?github_error=user_fetch_failed")

                user_data = user_response.json()

                # Store in separate auth file (not main settings)
                save_github_auth({
                    "access_token": access_token,
                    "user": {
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "avatar_url": user_data.get("avatar_url"),
                        "html_url": user_data.get("html_url"),
                    },
                })

                return redirect("/?github_connected=true")

        except Exception as e:
            PrintStyle.error(f"GitHub OAuth callback error: {e}")
            error_msg = urllib.parse.quote(str(e)[:100])
            return redirect(f"/?github_error={error_msg}")
