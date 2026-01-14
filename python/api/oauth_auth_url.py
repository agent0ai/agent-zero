from python.helpers.api import ApiHandler, Request, Response
from python.helpers import antigravity
from flask import redirect


class OAuthAuthUrl(ApiHandler):
    """Generate OAuth authorization URL for Google login."""
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            auth_url = antigravity.generate_auth_url()
            return {"auth_url": auth_url}
        except ValueError as e:
            return {"error": str(e)}
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
