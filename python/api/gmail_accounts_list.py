"""
Gmail Accounts List API Handler
Returns list of configured Gmail accounts with status
"""
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.gmail_oauth2 import GmailOAuth2Handler
from python.helpers import settings
import json


class GmailAccountsList(ApiHandler):
    """List all configured Gmail accounts"""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Get list of configured Gmail accounts with authentication status
        
        Returns:
            accounts: List of account objects with name, email, status
        """
        try:
            handler = GmailOAuth2Handler()
            accounts_list = []
            
            # Get accounts from settings
            current_settings = settings.get_settings()
            gmail_accounts = current_settings.get("gmail_accounts", {})
            
            for account_name, account_data in gmail_accounts.items():
                # Get detailed status from OAuth2 handler
                status = handler.get_account_status(account_name)
                
                accounts_list.append({
                    "name": account_name,
                    "email": account_data.get("email", "Unknown"),
                    "authenticated": status.get("authenticated", False),
                    "valid": status.get("valid", False),
                    "expired": status.get("expired", False),
                    "scopes": status.get("scopes", []),
                    "error": status.get("error")
                })
            
            return {
                "success": True,
                "accounts": accounts_list,
                "count": len(accounts_list)
            }
            
        except Exception as e:
            return Response(f"Failed to list Gmail accounts: {str(e)}", 500)
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
