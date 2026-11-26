from helpers.api import ApiHandler, Request, Response
from helpers import message_queue as mq
from agent import AgentContext
from helpers.state_monitor_integration import mark_dirty_for_context
from helpers.team_runs import team_queue_response

class MessageQueueRemove(ApiHandler):
    """Remove message(s) from queue."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = input.get("context", "")
        context = AgentContext.get(context_id) if isinstance(context_id, str) else None
        if (response := team_queue_response(context, input, "remove")) is not None:
            return response
        if not context:
            return Response("Context not found", status=404)

        item_id = input.get("item_id")  # None means clear all
        remaining = mq.remove(context, item_id)
        mark_dirty_for_context(context.id, reason="message_queue_remove")

        return {"ok": True, "remaining": remaining}
