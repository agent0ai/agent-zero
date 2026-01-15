"""
Gmail Account Remove API Handler
Removes a Gmail account and its credentials
"""
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.gmail_oauth2 import GmailOAuth2Handler
from python.helpers import settings
import os


class GmailAccountRemove(ApiHandler):
    """Remove a Gmail account"""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Remove Gmail account and delete credentials
        
        Input:
            account_name: Name of account to remove
        
        Returns:
            success: True if removal succeeded
        """
        try:
            account_name = input.get("account_name")
            
            if not account_name:
                return Response("account_name is required", 400)
            
            # Remove from settings
            current_settings = settings.get_settings()
            gmail_accounts = current_settings.get("gmail_accounts", {})
            
            if account_name not in gmail_accounts:
                return Response(f"Account '{account_name}' not found", 404)
            
            del gmail_accounts[account_name]
            current_settings["gmail_accounts"] = gmail_accounts
            settings.set_settings(current_settings)
            
            # Delete token file
            handler = GmailOAuth2Handler()
            token_path = handler._get_token_path(account_name)
            if os.path.exists(token_path):
                os.remove(token_path)
            
            return {
                "success": True,
                "account_name": account_name,
                "message": f"Account '{account_name}' removed successfully"
            }
            
        except Exception as e:
            return Response(f"Failed to remove account: {str(e)}", 500)
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
