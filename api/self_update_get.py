from helpers.api import ApiHandler, Request, Response

from helpers import runtime
from helpers import self_update


class SelfUpdateGet(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            info = self_update.get_update_info()
            return {
                "success": True,
                "supported": runtime.is_dockerized(),
                **info,
            }
        except Exception as e:
            return {
                "success": False,
                "supported": runtime.is_dockerized(),
                "error": str(e),
                "pending": self_update.load_pending_update(),
                "last_status": self_update.load_last_status(),
            }
