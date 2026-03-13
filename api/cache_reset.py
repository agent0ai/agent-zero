from helpers.api import ApiHandler, Request, Response
from helpers import cache


class CacheReset(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def requires_loopback(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        areas = input.get("areas", [])

        if not areas:
            cache.clear_all()
        else:
            for area in areas:
                cache.clear(area)

        return {"ok": True}
