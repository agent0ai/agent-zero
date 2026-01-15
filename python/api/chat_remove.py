from python.helpers.api import ApiHandler, Input, Output, Request, Response
from agent import AgentContext
from python.helpers import persist_chat


class RemoveChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        context = AgentContext.use(ctxid)
        if context:
            # stop processing any tasks
            context.reset()

        AgentContext.remove(ctxid)
        persist_chat.remove_chat(ctxid)

        # Lazy import to avoid blocking startup with crontab dependency
        try:
            from python.helpers.task_scheduler import TaskScheduler
            scheduler = TaskScheduler.get()
            await scheduler.reload()

            tasks = scheduler.get_tasks_by_context_id(ctxid)
            for task in tasks:
                await scheduler.remove_task_by_uuid(task.uuid)
        except ImportError:
            pass  # Scheduler not available

        return {
            "message": "Context removed.",
        }
