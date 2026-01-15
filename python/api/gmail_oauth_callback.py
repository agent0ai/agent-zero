"""
Gmail OAuth2 Callback API Handler
Handles OAuth2 callback and exchanges code for tokens
"""
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.gmail_oauth2 import GmailOAuth2Handler
from python.helpers import settings
from flask import session, redirect
from datetime import datetime
import json


class GmailOauthCallback(ApiHandler):
    """Handle Gmail OAuth2 callback"""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Process OAuth2 callback and save credentials
        
        Input (from query params):
            code: Authorization code from Google
            state: CSRF token
        
        Returns:
            success: True if authentication succeeded
            account_name: Name of authenticated account
            email: Email address of authenticated account
        """
        try:
            # Get parameters from query string
            code = request.args.get('code')
            state = request.args.get('state')
            error = request.args.get('error')
            
            if error:
                return Response(f"OAuth2 error: {error}", 400)
            
            if not code or not state:
                return Response("Missing code or state parameter", 400)
            
            # Verify CSRF token
            saved_state = session.get('gmail_oauth_state')
            if not saved_state or saved_state != state:
                return Response("Invalid state token (CSRF protection)", 403)
            
            # Get saved session data
            account_name = session.get('gmail_oauth_account')
            credentials_json = session.get('gmail_oauth_credentials')
            
            if not account_name or not credentials_json:
                return Response("Session expired or invalid", 400)
            
            # Initialize OAuth2 handler
            handler = GmailOAuth2Handler()
            
            # Exchange code for credentials
            email = handler.complete_authorization(
                account_name=account_name,
                credentials_json=credentials_json,
                authorization_code=code,
                state=state
            )
            
            # Update settings with new account
            current_settings = settings.get_settings()
            gmail_accounts = current_settings.get("gmail_accounts", {})
            
            # Create GmailAccountInfo entry
            gmail_accounts[account_name] = {
                "email": email,
                "authenticated": True,
                "scopes": handler.SCOPES,
                "added_date": datetime.utcnow().isoformat() + "Z"
            }
            
            current_settings["gmail_accounts"] = gmail_accounts
            settings.set_settings(current_settings)
            
            # Clear session data
            session.pop('gmail_oauth_state', None)
            session.pop('gmail_oauth_account', None)
            session.pop('gmail_oauth_credentials', None)
            
            # Return success page or redirect
            return {
                "success": True,
                "account_name": account_name,
                "email": email,
                "message": "Gmail account authenticated successfully! You can close this window."
            }
            
        except Exception as e:
            return Response(f"Failed to complete OAuth2 flow: {str(e)}", 500)
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
    
    @classmethod
    def requires_csrf(cls) -> bool:
        # OAuth2 callback uses state parameter for CSRF protection
        return False
