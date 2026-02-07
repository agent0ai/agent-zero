from python.helpers.api import ApiHandler, Request, session


class ApiLogout(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        try:
            session.clear()
        except Exception:
            session.pop("authentication", None)
            session.pop("csrf_token", None)
        return {"ok": True}
