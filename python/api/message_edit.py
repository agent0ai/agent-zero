from python.helpers.api import ApiHandler, Input, Output, Request, Response
from python.helpers import persist_chat, message_queue as mq
from python.helpers.task_scheduler import TaskScheduler
from agent import Agent, AgentContext, UserMessage
import uuid


class MessageEdit(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")
        log_index = input.get("log_index", None)
        new_text = input.get("text", "")

        if log_index is None or not isinstance(log_index, int) or log_index < 0:
            return Response("Invalid log_index", status=400, mimetype="text/plain")

        if not new_text.strip():
            return Response("Message text is required", status=400, mimetype="text/plain")

        # Cancel scheduled tasks (same pattern as chat_reset.py:13)
        TaskScheduler.get().cancel_tasks_by_context(ctxid, terminate_thread=True)

        # Get context — must exist
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return Response("Context not found", status=404, mimetype="text/plain")

        # Validate log_index is within bounds
        if log_index >= len(context.log.logs):
            return Response("log_index out of range", status=400, mimetype="text/plain")

        # Kill running agent task
        context.kill_process()
        context.task = None

        # Truncate log: remove items at index >= log_index
        with context.log._lock:
            context.log.logs = context.log.logs[:log_index]
            context.log.updates = list(range(len(context.log.logs)))
            context.log.guid = str(uuid.uuid4())

        # Reset agent (fresh history) — preserve truncated log
        context.agent0 = Agent(0, context.config, context)
        context.streaming_agent = None
        context.paused = False

        # Clear message queue
        mq.remove(context)

        # Log the edited message and send it
        mq.log_user_message(context, new_text, [])
        context.communicate(UserMessage(new_text, []))

        # Save and notify
        persist_chat.save_tmp_chat(context)
        from python.helpers.state_monitor_integration import mark_dirty_all
        mark_dirty_all(reason="api.message_edit.MessageEdit")

        return {
            "message": "Message edited.",
            "context": context.id,
        }
