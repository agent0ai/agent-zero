from python.helpers.api import ApiHandler, Request, Response
from python.helpers import antigravity


class OAuthLogout(ApiHandler):
    """Clear OAuth credentials (logout)."""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            antigravity.clear_credentials()
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
