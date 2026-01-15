from python.helpers.api import ApiHandler, Request, Response
from python.helpers import master_orchestrator, observability_adapters


class WorkflowSave(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        label = input.get("label") or None
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return {"ok": False, "error": "Context not found"}

        saved = master_orchestrator.save_active_run(context, label=label)
        if not saved:
            return {"ok": False, "error": "No active workflow"}

        observability_adapters.dispatch_workflow_snapshot(context, saved)
        return {"ok": True, "saved": saved}
