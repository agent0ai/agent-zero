"""API handler for chat compaction."""
from uuid import uuid4

from helpers import team_access, team_projects, team_runs
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_store import ActiveRunConflict, get_store
from agent import AgentContext
from plugins._model_config.helpers.model_config import get_preset_by_name
from plugins._chat_compaction.helpers.compactor import (
    MIN_COMPACTION_TOKENS,
    get_compaction_stats,
    run_compaction,
)


class CompactChat(ApiHandler):
    """Compact the current chat history into a summarized message."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")
        action = input.get("action", "compact")

        if not isinstance(ctxid, str) or not ctxid:
            return Response("Missing context id", 400)

        context = AgentContext.get(ctxid)
        member = team_access.request_scope()
        scope = team_access.request_chat_scope(context) if context else member
        if (member is not None or team_access.is_team_chat(context)) and (
            not context or scope is None or not team_access.can_send(scope, context)
        ):
            return Response("Chat access denied.", 403)
        if not context:
            return Response("Context not found", 404)

        if context.is_running():
            return Response("Cannot compact while agent is running", 409)

        revision = (context.log.guid, len(context.log.updates))
        visible_count = len(context.log.logs)
        if visible_count <= 1:
            return Response("Not enough messages to compact", 400)

        # Gate both stats and compact — no point opening the modal for tiny chats
        stats = await get_compaction_stats(context)
        if stats["token_count"] < MIN_COMPACTION_TOKENS:
            return {
                "ok": False,
                "message": f"Not enough content to compact (minimum {MIN_COMPACTION_TOKENS:,} tokens)",
            }

        if action == "stats":
            return {"ok": True, "stats": stats}

        elif action == "compact":
            use_chat_model = input.get("use_chat_model", True)
            preset_name = input.get("preset_name") or None
            if not isinstance(use_chat_model, bool) or (
                preset_name is not None and (not isinstance(preset_name, str) or not get_preset_by_name(preset_name))
            ):
                return Response("Select a configured model preset.", 400)

            with self.thread_lock:
                if context.is_running() or revision != (context.log.guid, len(context.log.updates)):
                    return Response("The conversation changed. Reopen compaction to refresh it.", 409)
                current_scope = team_access.request_chat_scope(context)
                if team_access.is_team_chat(context):
                    if current_scope is None or not team_access.can_send(current_scope, context):
                        return Response("Chat access denied.", 403)
                    try:
                        run, _ = team_runs.reserve(context, current_scope.account_id, uuid4().hex, "compact", kind="compact")
                    except PermissionError:
                        return Response("Chat access denied.", 403)
                    except ActiveRunConflict as error:
                        return Response(str(error), 409)
                    try:
                        with team_runs.authorized_dispatch(run):
                            context.run_task(_run_compaction_task, context, use_chat_model, preset_name, run)
                    except BaseException:
                        get_store().finish_run(run, "failed")
                        raise
                    mark_dirty_all(reason="project chat compaction started")
                else:
                    context.run_task(_run_compaction_task, context, use_chat_model, preset_name)

            return {"ok": True, "message": "Compaction started"}

        else:
            return Response(f"Unknown action: {action}", 400)


async def _run_compaction_task(context, use_chat_model: bool, preset_name: str | None, run=None):
    """Wrapper to run compaction and handle errors."""
    try:
        if run is None:
            await run_compaction(context, use_chat_model, preset_name)
        else:
            with team_projects.activity("chat.compact", run.account_id, run.project_id, context_id=context.id):
                await run_compaction(context, use_chat_model, preset_name)
        return True
    except Exception as e:
        context.log.log(
            type="error",
            heading="Compaction Failed",
            content=str(e),
        )
        mark_dirty_all(reason="plugins._chat_compaction.compact_chat_error")
