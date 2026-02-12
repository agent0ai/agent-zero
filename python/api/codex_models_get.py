from python.helpers.api import ApiHandler, Request, Response
from python.helpers import codex_exec


class CodexModelsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        force_refresh = bool(input.get("force_refresh", False))
        models = codex_exec.get_codex_models(force_refresh=force_refresh)
        status = codex_exec.get_codex_status()
        return {"ok": True, "models": models, "status": status}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

