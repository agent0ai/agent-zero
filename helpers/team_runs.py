import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import threading
from typing import TYPE_CHECKING
from uuid import NAMESPACE_OID, uuid4, uuid5

from flask import Response

from helpers import files, message_queue, persist_chat, runtime, team_access
from helpers.print_style import PrintStyle
from helpers.state_monitor_integration import mark_dirty_all
from helpers.team_access import CHAT_PROJECT_ID
from helpers.team_store import ADMIN_ACTOR_ID, TeamRun, get_store

if TYPE_CHECKING:
    from agent import AgentContext


_dispatch_run: ContextVar[TeamRun | None] = ContextVar("team_dispatch_run", default=None)
_executing_run: ContextVar[TeamRun | None] = ContextVar("team_executing_run", default=None)
_running_tasks: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Task]] = {}
_promoted_runs: set[str] = set()
_running_tasks_lock = threading.Lock()
_runtime_lock = None


def recover_on_startup() -> int:
    """Own the team runtime before recovering runs from an exited framework process."""
    import fcntl

    global _runtime_lock
    if _runtime_lock is not None:
        return 0
    store = get_store()
    stream = open(files.get_abs_path("usr", "team", "runtime.lock"), "a+b")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        recovered = store.recover_runs(runtime.get_runtime_id())
    except BaseException:
        stream.close()
        raise
    _runtime_lock = stream
    return recovered


def reserve(context: "AgentContext", account_id: str, request_id: str, text: str, *, kind: str = "message") -> tuple[TeamRun, bool]:
    return get_store().reserve_run(
        context_id=context.id,
        project_id=context.get_data(CHAT_PROJECT_ID),
        account_id=account_id,
        runtime_id=runtime.get_runtime_id(),
        request_id=request_id,
        request_digest=hashlib.sha256(text.encode()).hexdigest(),
        kind=kind,
    )


@contextmanager
def authorized_dispatch(run: TeamRun):
    token = _dispatch_run.set(run)
    try:
        yield
    finally:
        _dispatch_run.reset(token)


def current_dispatch(context: "AgentContext") -> TeamRun:
    run = _dispatch_run.get()
    if run is None or run.context_id != context.id:
        raise PermissionError("Start team conversations through an authorized message request.")
    return run


def executing_scope(context: "AgentContext") -> tuple[TeamRun, team_access.MemberScope]:
    run = _executing_run.get()
    if run is None or run.context_id != context.id:
        raise PermissionError("This operation needs an active team run.")
    active = get_store().active_run(context.id)
    if run.account_id == ADMIN_ACTOR_ID:
        scope = team_access.admin_chat_scope(context)
    else:
        scope = team_access.MemberScope(run.account_id, team_access.assigned_projects(run.account_id))
    if active is None or active.id != run.id or active.state != "running" or not scope.permits_chat(context):
        raise PermissionError("This run no longer has project access.")
    return run, scope


def manage_turn(context: "AgentContext", func):
    run = current_dispatch(context)

    async def wrapped(*args, **kwargs):
        store = get_store()
        state = "failed"
        task = asyncio.current_task()
        execution = _executing_run.set(run)
        try:
            with _running_tasks_lock:
                if task is not None:
                    _running_tasks[run.id] = (asyncio.get_running_loop(), task)
                can_start = store.start_run(run)
            if not can_start:
                state = "stopped"
                return None
            mark_dirty_all(reason="team run started")
            result = await func(*args, **kwargs)
            while result is not None and (item := store.take_queued_message(run, interject=False)):
                message = _logged_queue_message(context, run, item, " (queued)")
                result = await func(args[0], message)
            state = "completed" if result is not None else "failed"
            return result
        except asyncio.CancelledError:
            state = "stopped"
            raise
        finally:
            _executing_run.reset(execution)
            with _running_tasks_lock:
                _running_tasks.pop(run.id, None)
                _promoted_runs.discard(run.id)
            context.paused = False
            if state == "stopped":
                context.log.set_progress("", active=False)
                context.log.log(type="info", content="Agent process stopped.", finished=True)
            try:
                persist_chat.save_tmp_chat(context)
            except Exception as error:
                PrintStyle.warning(f"Unable to persist team chat {context.id}: {error}")
                state = "failed"
            if store.finish_run(run, state):
                mark_dirty_all(reason="team run finished")

    return wrapped


def _logged_queue_message(context: "AgentContext", run: TeamRun, item: tuple[str, str], source: str):
    from agent import UserMessage

    item_id, text = item
    message_id = uuid5(NAMESPACE_OID, f"{run.id}:{item_id}").hex
    message_queue.log_user_message(context, text, [], message_id, source=source, author=run.username)
    persist_chat.save_tmp_chat(context)
    mark_dirty_all(reason="team queued message delivered")
    return UserMessage(text, id=message_id)


def next_interjection(context: "AgentContext"):
    run = _executing_run.get()
    if run is None or run.context_id != context.id:
        return None
    with _running_tasks_lock:
        if run.id not in _promoted_runs:
            return None
        item = get_store().take_queued_message(run, interject=True)
        if item is None:
            _promoted_runs.discard(run.id)
            return None
    return _logged_queue_message(context, run, item, " (interjection)")


def team_queue_response(context: "AgentContext | None", data: dict, action: str) -> dict | Response | None:
    scope = team_access.request_chat_scope(context) if context is not None else team_access.request_scope()
    if scope is None and not team_access.is_team_chat(context):
        return None
    if scope is None or context is None or not scope.permits_chat(context):
        return Response("Chat access denied.", 403)

    store = get_store()
    run = store.active_run(context.id)
    if run is None or data.get("run_id") != run.id:
        return Response("This run is no longer active.", 409)
    if run.account_id != scope.account_id:
        return Response(f"{run.username} is holding this chat.", 409)

    item_id = data.get("item_id")
    if item_id is not None and (not isinstance(item_id, str) or not 0 < len(item_id) <= 128):
        return Response("Invalid queue item ID.", 400)
    try:
        if action == "add":
            text = data.get("text")
            if not isinstance(text, str) or not text.strip() or data.get("attachments"):
                return Response("A nonempty text message is required.", 400)
            item_id = item_id or uuid4().hex
            count = store.add_queued_message(run, item_id, text)
            result = {"ok": True, "item_id": item_id, "queue_length": count}
        elif action == "remove":
            _, count = store.edit_queue(run, item_id=item_id, remove=True)
            result = {"ok": True, "remaining": count}
        else:
            with _running_tasks_lock:
                send_all = data.get("send_all") is True
                count, _ = store.edit_queue(
                    run, item_id=None if send_all else item_id, remove=False, first_only=not send_all and item_id is None,
                )
                if count:
                    _promoted_runs.add(run.id)
            result = {"ok": True, "sent_count": count, "queued_for_interjection": True}
    except ValueError as error:
        return Response(str(error), 409)
    mark_dirty_all(reason="team queue changed")
    return result


def request_stop(run: TeamRun, actor_id: str) -> bool:
    if not get_store().request_stop(run, actor_id):
        return False
    with _running_tasks_lock:
        active = _running_tasks.get(run.id)
    if active:
        loop, task = active
        loop.call_soon_threadsafe(task.cancel)
    mark_dirty_all(reason="team stop requested")
    return True


def public_run(run: TeamRun, viewer_id: str = "") -> dict:
    return {"id": run.id, "holder": run.username, "state": run.state, "mine": run.account_id == viewer_id, "kind": run.kind}
