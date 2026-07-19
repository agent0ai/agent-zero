import json
from datetime import datetime

from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.persist_chat import (
    _serialize_context,
    _deserialize_context,
    save_tmp_chat,
)
from agent import AgentContext


def _trim_history_json(history_json: str, kept_ids: set[str], after_cut_ids: set[str]) -> str:
    """Trim a serialized history JSON to keep only messages that appear
    before the branch cut point.

    *kept_ids*: IDs of log items up to and including the cut point.
    *after_cut_ids*: IDs of log items after the cut point.

    Walk messages in order.  A message is kept while the running state
    is "keep".  The state flips to "drop" the first time we encounter
    a message whose id is in *after_cut_ids*.  Messages whose id does
    not appear in any log set (unpaired) inherit the current state.
    Summarized topics/bulks are always preserved.
    """
    if not history_json:
        return history_json

    hist = json.loads(history_json)
    keep = True  # running state

    def filter_messages(messages: list[dict]) -> list[dict]:
        nonlocal keep
        result = []
        for msg in messages:
            mid = msg.get("id", "")
            if mid and mid in after_cut_ids:
                keep = False
            elif mid and mid in kept_ids:
                keep = True
            # else: unpaired – inherit current state
            if keep:
                result.append(msg)
        return result

    # Bulks are already summarized old history – always keep
    # Topics: keep summarized ones; filter unsummarized
    trimmed_topics = []
    for topic in hist.get("topics", []):
        if topic.get("summary"):
            trimmed_topics.append(topic)
            continue
        msgs = filter_messages(topic.get("messages", []))
        if msgs:
            topic["messages"] = msgs
            trimmed_topics.append(topic)
        if not keep:
            break
    hist["topics"] = trimmed_topics

    # Current topic
    current = hist.get("current", {})
    if not current.get("summary") and keep:
        current["messages"] = filter_messages(current.get("messages", []))
    elif not keep:
        current["messages"] = []
    hist["current"] = current

    # Recount
    total = sum(
        len(t.get("messages", [])) for t in hist["topics"] if not t.get("summary")
    ) + len(hist.get("current", {}).get("messages", []))
    hist["counter"] = total

    return json.dumps(hist, ensure_ascii=False)


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
        src_logs = data["log"]["logs"]
        cut_idx = None
        for i, item in enumerate(src_logs):
            if item["no"] == log_no:
                cut_idx = i
                break

        if cut_idx is None:
            if 0 <= log_no < len(src_logs):
                cut_idx = log_no
            else:
                return Response("log_no not found in chat log", 400)

        kept_logs = src_logs[: cut_idx + 1]
        after_logs = src_logs[cut_idx + 1 :]
        data["log"]["logs"] = kept_logs

        # Build ID sets for history trimming
        kept_ids = {item["id"] for item in kept_logs if item.get("id")}
        after_cut_ids = {item["id"] for item in after_logs if item.get("id")}

        # Trim each agent's history using ID matching
        for ag in data.get("agents", []):
            ag["history"] = _trim_history_json(
                ag.get("history", ""), kept_ids, after_cut_ids
            )

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