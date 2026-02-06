from python.helpers.api import ApiHandler, Request, Response
from python.helpers.extension import call_extensions


class GetBanners(ApiHandler):
    """
    API endpoint for Welcome Screen banners.
    Add checks as extension scripts in python/extensions/banners/ or usr/extensions/banners/
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        banners = input.get("banners", [])
        frontend_context = input.get("context", {})
        
        # Banners array passed by reference - extensions append directly to it
        await call_extensions("banners", agent=None, banners=banners, frontend_context=frontend_context)
        
        return {"banners": banners}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
