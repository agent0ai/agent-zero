from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agent import AgentContext
from helpers import persist_chat, team_access, team_projects
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.state_monitor_integration import mark_dirty_all
from helpers.task_scheduler import TaskScheduler
from helpers.team_store import get_store


class Reset(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")
        current = AgentContext.get(ctxid) if isinstance(ctxid, str) and ctxid else None
        if team_access.is_team_chat(current) or team_access.request_scope() is not None:
            with self.thread_lock:
                scope = team_access.request_chat_scope(current) if current else None
                if not scope or not scope.permits_chat(current) or not team_access.has_chat_history(current):
                    return Response("Chat access denied.", 403)
                if current.is_running() or get_store().active_run(current.id):
                    return Response("Wait for the current run before clearing history.", 409)
                project_id = current.get_data(team_access.CHAT_PROJECT_ID)
                with team_projects.activity("chat.clear", scope.account_id, project_id, context_id=current.id):
                    filename = f"pre-clear-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}.json"
                    backup = Path(persist_chat.get_chat_folder_path(current.id)) / "backups" / filename
                    persist_chat._write_atomic(str(backup), persist_chat.export_json_chat(current))
                    current.set_data(team_access.CHAT_STARTED, True)
                    current.reset()
                    persist_chat.save_tmp_chat(current)
                mark_dirty_all(reason="shared chat cleared")
                return {"message": "Agent restarted."}

        # attempt to stop any scheduler tasks bound to this context
        TaskScheduler.get().cancel_tasks_by_context(ctxid, terminate_thread=True)

        # context instance - get or create
        context = self.use_context(ctxid)
        context.reset()
        persist_chat.save_tmp_chat(context)
        persist_chat.remove_msg_files(ctxid)

        # Reset updates context metadata (log guid/version) and must refresh other tabs' lists.
        mark_dirty_all(reason="api.chat_reset.Reset")

        return {
            "message": "Agent restarted.",
        }
