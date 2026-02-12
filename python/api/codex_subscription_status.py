from python.helpers.api import ApiHandler, Request, Response
from python.helpers import codex_exec


class CodexSubscriptionStatus(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        login = codex_exec.get_codex_login_state()
        status = codex_exec.get_codex_status()
        models = codex_exec.get_cached_codex_models()
        return {"ok": True, "login": login, "status": status, "models": models}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

