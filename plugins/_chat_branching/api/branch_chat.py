from datetime import datetime

from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.persist_chat import (
    _serialize_context,
    _deserialize_context,
    save_tmp_chat,
)
from agent import AgentContext


class BranchChat(ApiHandler):
    """Create a new chat branched from an existing chat at a specific log message."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")
        log_no = input.get("log_no")  # LogItem.no from frontend

        if not ctxid:
            return Response("Missing context id", 400)
        if log_no is None:
            return Response("Missing log_no", 400)

        context = AgentContext.get(ctxid)
        if not context:
            return Response("Context not found", 404)

        # Serialize the source context
        data = _serialize_context(context)

        # Remove id so _deserialize_context generates a new one
        del data["id"]

        # Trim log entries: keep only items up to and including log_no.
        # _serialize_log uses log.logs[-LOG_SIZE:], so the serialized "no"
        # values may start above 0 for long chats. We match against the
        # original "no" field that each LogItem.output() emits.
        src_logs = data["log"]["logs"]
        cut_idx = None
        for i, item in enumerate(src_logs):
            if item["no"] == log_no:
                cut_idx = i
                break

        if cut_idx is None:
            # Fallback: log_no might already be a 0-based index within the
            # serialized array (e.g. after a reload where _deserialize_log
            # resets "no" to sequential).  Accept if within bounds.
            if 0 <= log_no < len(src_logs):
                cut_idx = log_no
            else:
                return Response("log_no not found in chat log", 400)

        data["log"]["logs"] = src_logs[: cut_idx + 1]

        # Give the branch a distinguishable name
        src_name = data.get("name") or "Chat"
        data["name"] = f"{src_name} (branch)"
        data["created_at"] = datetime.now().isoformat()

        # Deserialize into a brand-new context (new id, fresh agent config)
        new_context = _deserialize_context(data)

        # Persist immediately
        save_tmp_chat(new_context)

        # Notify all tabs
        from helpers.state_monitor_integration import mark_dirty_all
        mark_dirty_all(reason="plugins.chat_branching.BranchChat")

        return {
            "ok": True,
            "ctxid": new_context.id,
            "message": "Chat branched successfully.",
        }