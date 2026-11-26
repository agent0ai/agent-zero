from uuid import uuid4

from agent import AgentContext, UserMessage
from helpers import team_access, team_runs
from helpers.api import ApiHandler, Request, Response
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_store import ActiveRunConflict, get_store

class Nudge(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        current = AgentContext.get(ctxid) if isinstance(ctxid, str) else None
        if team_access.is_team_chat(current) or team_access.request_scope() is not None:
            with self.thread_lock:
                scope = team_access.request_chat_scope(current) if current else None
                if not scope or not scope.permits_chat(current) or not team_access.has_chat_history(current):
                    return Response("Chat access denied.", 403)
                store = get_store()
                run = store.active_run(current.id)
                if run:
                    if run.id != input.get("run_id") or run.account_id != scope.account_id or run.kind != "message":
                        return Response("Only the holder of the current run can nudge this chat.", 409)
                    queued = team_runs.team_queue_response(current, {"run_id": run.id, "text": "Continue the current request.", "item_id": uuid4().hex}, "add")
                    if isinstance(queued, Response):
                        return queued
                    delivered = team_runs.team_queue_response(current, {"run_id": run.id, "item_id": queued["item_id"]}, "send")
                    if isinstance(delivered, Response):
                        return delivered
                    current.paused = False
                else:
                    if current.is_running() or input.get("run_id"):
                        return Response("This run is no longer active.", 409)
                    try:
                        run, _ = team_runs.reserve(current, scope.account_id, uuid4().hex, "nudge")
                    except ActiveRunConflict as error:
                        return Response(str(error), 409)
                    except PermissionError:
                        return Response("Chat access denied.", 403)
                    try:
                        with team_runs.authorized_dispatch(run):
                            current.communicate(UserMessage("", system_message=[current.agent0.read_prompt("fw.msg_nudge.md")]))
                    except BaseException:
                        store.finish_run(run, "failed")
                        raise
                mark_dirty_all(reason="shared chat nudged")
                return {"message": "Agent nudged.", "ctxid": current.id}

        context = self.use_context(ctxid)
        context.nudge()

        msg = "Process reset, agent nudged."
        context.log.log(type="info", content=msg)
        
        return {
            "message": msg,
            "ctxid": context.id,
        }
