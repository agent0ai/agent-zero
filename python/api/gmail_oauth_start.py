"""
Gmail OAuth2 Start Flow API Handler
Initiates OAuth2 authentication for Gmail API access
"""
import secrets

from flask import session

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.gmail_oauth2 import GmailOAuth2Handler


class GmailOauthStart(ApiHandler):
    """Start Gmail OAuth2 authentication flow"""

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Initiate OAuth2 flow and return authorization URL

        Input:
            account_name: Name for this Gmail account
            credentials_json: Path to credentials.json or JSON content

        Returns:
            auth_url: URL to redirect user to for authorization
            state: CSRF protection token
        """
        try:
            account_name = input.get("account_name")
            credentials_json = input.get("credentials_json")

            if not account_name:
                return Response("account_name is required", 400)

            if not credentials_json:
                return Response("credentials_json is required", 400)

            # Generate CSRF state token
            state = secrets.token_urlsafe(32)
            session['gmail_oauth_state'] = state
            session['gmail_oauth_account'] = account_name
            session['gmail_oauth_credentials'] = credentials_json

            # Initialize OAuth2 handler
            handler = GmailOAuth2Handler()

            # Get authorization URL (we'll need to modify gmail_oauth2.py to support this)
            auth_url = handler.get_authorization_url(
                credentials_json=credentials_json,
                state=state
            )

            return {
                "success": True,
                "authorization_url": auth_url,
                "auth_url": auth_url,
                "state": state,
                "message": "Open the authorization_url in a popup window to authorize"
            }

        except Exception as e:
            return Response(f"Failed to start OAuth2 flow: {e!s}", 500)

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
