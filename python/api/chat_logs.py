from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output, Request, Response


class ChatLogs(ApiHandler):
    """Read-only endpoint to fetch log items for any context by ID.

    Used by split-screen comparison to load messages from two contexts
    without switching the active context.
    """

    async def process(self, input: Input, request: Request) -> Output:
        context_id = input.get("context_id", "")
        log_from = input.get("log_from", 0)

        if not context_id:
            return {"success": False, "error": "context_id is required"}

        context = AgentContext.get(context_id)
        if not context:
            return {"success": False, "error": "Context not found"}

        logs = context.log.output(start=log_from)
        log_version = len(context.log.updates)

        # Include fork_info if present
        fork_info = None
        if hasattr(context, "data") and isinstance(context.data, dict):
            fork_info = context.data.get("fork_info")

        return {
            "success": True,
            "logs": logs,
            "log_version": log_version,
            "log_guid": context.log.guid,
            "fork_info": fork_info,
        }
