from python.helpers.api import ApiHandler, Request, Response
from python.helpers import codex_exec


class CodexSubscriptionStart(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        login = codex_exec.start_codex_login()
        status = codex_exec.get_codex_status()
        models = codex_exec.get_cached_codex_models()
        return {"ok": True, "login": login, "status": status, "models": models}

