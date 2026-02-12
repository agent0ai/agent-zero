from python.helpers.api import ApiHandler, Request, Response
from python.helpers import codex_exec


class CodexSubscriptionLogout(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        codex_exec.cancel_codex_login()
        result = codex_exec.logout_codex()
        login = codex_exec.get_codex_login_state()
        models = codex_exec.get_cached_codex_models()
        return {
            "ok": bool(result.get("ok", False)),
            "message": str(result.get("message", "")),
            "login": login,
            "status": result.get("status", codex_exec.get_codex_status()),
            "models": models,
        }

