from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.flow_engine import FlowEngine


class FlowStop(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        run_id = input.get("run_id", "")
        if not run_id:
            return {"ok": False, "error": "Missing required field: run_id"}

        cancelled = FlowEngine.cancel_run(run_id)
        if cancelled:
            return {"ok": True, "message": f"Run {run_id} cancellation requested"}
        else:
            run = FlowEngine.get_run(run_id)
            if not run:
                return {"ok": False, "error": f"Run not found: {run_id}"}
            return {"ok": False, "error": "Run is not currently executing"}
