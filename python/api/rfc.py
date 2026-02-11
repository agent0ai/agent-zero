from python.helpers import runtime
from python.helpers.api import ApiHandler, Request, Response


class RFC(ApiHandler):
    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        result = await runtime.handle_rfc(input)  # type: ignore
        return result
