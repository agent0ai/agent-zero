from python.helpers.api import ApiHandler, Request, Response
from python.helpers.providers import get_providers


class ModelGroupsProviders(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        chat_providers = get_providers("chat")
        embed_providers = get_providers("embedding")
        
        return {
            "ok": True,
            "chat_providers": chat_providers,
            "embed_providers": embed_providers,
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]