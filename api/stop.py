from agent import AgentContext
from helpers.api import ApiHandler, Request, Response
from helpers import login, team_access, team_runs
from helpers.api import session
from helpers.team_store import get_store


def stop_context(context: AgentContext) -> dict:
    was_running = context.is_running()

    context.kill_process()
    context.paused = False
    context.log.set_progress("", active=False)

    message = "Agent process stopped."
    context.log.log(type="info", content=message, finished=True)

    return {
        "message": message,
        "context": context.id,
        "stopped": was_running,
    }


class Stop(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        if not isinstance(ctxid, str) or not ctxid.strip():
            return Response(
                '{"error": "context is required"}',
                status=400,
                mimetype="application/json",
            )

        scope = team_access.request_scope()
        if scope is not None or login.team_mode_enabled():
            context = AgentContext.get(ctxid.strip())
        else:
            context = AgentContext.use(ctxid.strip())
        if scope is not None and (context is None or not scope.permits_chat(context)):
            return Response("Chat access denied.", 403)
        if not context:
            return Response(
                '{"error": "Chat context not found"}',
                status=404,
                mimetype="application/json",
            )
        if not team_access.is_team_chat(context):
            return stop_context(context)

        run = get_store().active_run(context.id)
        actor_id = scope.account_id if scope is not None else "admin"
        if scope is not None and run is not None and run.account_id != actor_id:
            return Response("Only the person who started this run can stop it.", 403)
        if scope is None and not login.is_admin_session(session):
            return Response("Chat access denied.", 403)
        if run is None or input.get("run_id") != run.id:
            return Response("This run is no longer active.", 409)
        if run.state != "stopping":
            team_runs.request_stop(run, actor_id)
        return {"message": "Stopping the team run.", "context": context.id, "run_id": run.id, "stopped": False}
