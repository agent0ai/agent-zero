from agent import AgentContext
from helpers.api import ApiHandler, Request, Response
from helpers import team_access, team_projects
from helpers.state_monitor_integration import mark_dirty_for_context
from helpers.team_store import ADMIN_ACTOR_ID, get_store


class Pause(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        paused = input.get("paused", False)
        ctxid = input.get("context", "")
        if not isinstance(paused, bool) or not isinstance(ctxid, str):
            return Response("Invalid pause request.", 400)

        with self.thread_lock:
            context = AgentContext.get(ctxid) if ctxid else None
            if team_access.is_team_chat(context) or team_access.request_scope() is not None:
                scope = team_access.request_chat_scope(context) if context else None
                if scope is None or not scope.permits_chat(context):
                    return Response("Chat access denied.", 403)
                run = get_store().active_run(context.id)
                if run is None or run.id != input.get("run_id") or run.state not in {"starting", "running"}:
                    return Response("This run is no longer active.", 409)
                if scope.account_id not in {run.account_id, ADMIN_ACTOR_ID}:
                    return Response("Only the run holder can pause this chat.", 403)
                action = "message.pause" if paused else "message.resume"
                with team_projects.activity(action, scope.account_id, run.project_id, context_id=context.id):
                    context.paused = paused
            else:
                context = self.use_context(ctxid)
                context.paused = paused

        mark_dirty_for_context(context.id, reason="api.pause.Pause")
        return {"message": "Agent paused." if paused else "Agent unpaused.", "pause": paused}
