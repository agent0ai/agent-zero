from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.flow_engine import FlowEngine


class FlowStatus(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        run_id = input.get("run_id", "")
        if not run_id:
            return {"ok": False, "error": "Missing required field: run_id"}

        run = FlowEngine.get_run(run_id)
        if not run:
            return {"ok": False, "error": f"Run not found: {run_id}"}

        status = run.to_status()
        status["ok"] = True
        return status
