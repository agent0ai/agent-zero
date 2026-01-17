from python.helpers import master_orchestrator
from python.helpers.api import ApiHandler, Request, Response


class WorkflowGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return {"runs": [], "saved_runs": [], "active_run_id": None}

        store = master_orchestrator.ensure_store(context)
        return {
            "runs": store.get("runs", []),
            "saved_runs": store.get("saved_runs", []),
            "active_run_id": store.get("active_run_id"),
        }
