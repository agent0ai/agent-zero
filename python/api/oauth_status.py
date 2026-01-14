from python.helpers.api import ApiHandler, Request, Response
from python.helpers import antigravity


class OAuthStatus(ApiHandler):
    """Get current OAuth authentication status."""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            status = antigravity.get_auth_status()
            return status
        except Exception as e:
            return {"is_authenticated": False, "error": str(e)}
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
