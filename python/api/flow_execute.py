from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.flow_engine import FlowEngine
from python.helpers.print_style import PrintStyle


class FlowExecute(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        flow = input.get("flow")
        if not flow or not isinstance(flow, dict):
            return {"ok": False, "error": "Missing required field: flow"}

        user_prompt = input.get("user_prompt", "")

        try:
            # Run the flow in a background thread so the API returns immediately
            run = FlowEngine.start_background(flow, user_prompt)
            return {"ok": True, "run_id": run.id}
        except Exception as e:
            PrintStyle.error(f"Failed to start flow execution: {e}")
            return {"ok": False, "error": str(e)}
