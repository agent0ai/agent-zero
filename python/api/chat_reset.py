from python.helpers.api import ApiHandler, Input, Output, Request, Response


from python.helpers import persist_chat
from python.helpers.task_scheduler import TaskScheduler


class Reset(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        # attempt to stop any scheduler tasks bound to this context
        TaskScheduler.get().cancel_tasks_by_context(ctxid, terminate_thread=True)

        # context instance - get or create
        context = self.use_context(ctxid)
        context.reset()
        persist_chat.save_tmp_chat(context)
        persist_chat.remove_msg_files(ctxid)

        return {
            "message": "Agent restarted.",
        }
