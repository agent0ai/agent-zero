from python.helpers.api import ApiHandler, Request, Response

from python.helpers import runtime, settings

class GetSettings(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        set = settings.convert_out(settings.get_settings())
        runtime_info = {"isDevelopment": runtime.is_development()}
        return {"settings": set, "runtime": runtime_info}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
