from python.helpers.api import ApiHandler, Request, Response

from python.helpers import settings


class GetSettings(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        backend = settings.get_settings()
        out = settings.convert_out(backend)
        return dict(out)

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
