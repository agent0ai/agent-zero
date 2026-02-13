from python.helpers.api import ApiHandler, Input, Output, Request, Response
from agent import AgentContext
from python.helpers import persist_chat


class FlowGroupRemove(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        flow_run_id = input.get("flow_run_id", "")
        if not flow_run_id:
            return {"message": "No flow_run_id provided."}

        removed = []
        for ctx in list(AgentContext.all()):
            if ctx.get_output_data("flow_run_id") == flow_run_id:
                ctx.reset()
                AgentContext.remove(ctx.id)
                persist_chat.remove_chat(ctx.id)
                removed.append(ctx.id)

        from python.helpers.state_monitor_integration import mark_dirty_all
        mark_dirty_all(reason="api.flow_group_remove.FlowGroupRemove")

        return {
            "message": f"Removed {len(removed)} context(s).",
            "removed": removed,
        }
