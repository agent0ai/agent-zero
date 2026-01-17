from python.helpers.api import ApiHandler, Request, Response
from python.helpers.settings import get_settings


class CoworkFoldersGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        settings = get_settings()
        return {"paths": settings.get("cowork_allowed_paths", [])}
