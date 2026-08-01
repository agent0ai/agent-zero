"""Regression tests for code_execution_remote CLI reconnect behavior.

Root cause: when the Agent Zero container restarts, the server-side /ws
registry is wiped and the a0 CLI must reconnect. While no CLI is connected,
code_execution_remote used to return a soft tool result, so the main agent
kept retrying with fresh session numbers instead of waiting for the
automatic reconnect and then handing control back to the user.
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from plugins._a0_connector.helpers import ws_runtime
from plugins._a0_connector.tools import code_execution_remote
from plugins._a0_connector.tools.code_execution_remote import CodeExecutionRemote


def _make_tool(args: dict) -> CodeExecutionRemote:
    context_id = f"ctx-{uuid.uuid4().hex[:8]}"
    agent = SimpleNamespace(context=SimpleNamespace(id=context_id))
    return CodeExecutionRemote(agent, "code_execution_remote", None, args, "", None)


@pytest.fixture(autouse=True)
def _fast_reconnect_grace(monkeypatch):
    monkeypatch.setattr(code_execution_remote, "NO_CLI_RECONNECT_GRACE_SECONDS", 0.4)
    monkeypatch.setattr(code_execution_remote, "NO_CLI_RECONNECT_POLL_SECONDS", 0.05)


@pytest.fixture
def registered_sid():
    sid = f"sid-{uuid.uuid4().hex[:8]}"
    yield sid
    ws_runtime.unregister_sid(sid)


@pytest.mark.asyncio
async def test_no_cli_waits_for_reconnect_then_breaks_loop_with_guidance() -> None:
    tool = _make_tool({"runtime": "terminal", "code": "echo hi", "session": 0})

    started = time.monotonic()
    response = await tool.execute()
    elapsed = time.monotonic() - started

    assert elapsed >= code_execution_remote.NO_CLI_RECONNECT_GRACE_SECONDS
    assert response.break_loop is True
    message = response.message.lower()
    assert "no cli client connected" in message
    assert "reconnect" in message


@pytest.mark.asyncio
async def test_cli_reconnect_during_grace_proceeds_with_execution(
    monkeypatch, registered_sid
) -> None:
    sid = registered_sid
    tool = _make_tool({"runtime": "terminal", "code": "echo hi", "session": 0})
    context_id = tool.agent.context.id

    class _FakeWsManager:
        async def emit_to(self, namespace, target_sid, event, payload, handler_id=None):
            assert target_sid == sid
            ws_runtime.resolve_pending_exec_op(
                payload["op_id"],
                sid=target_sid,
                payload={"ok": True, "result": {"output": "reconnected-output"}},
            )

    monkeypatch.setattr(
        code_execution_remote, "get_shared_ws_manager", lambda: _FakeWsManager()
    )
    monkeypatch.setattr(
        code_execution_remote, "build_exec_config", lambda **kwargs: {}
    )

    async def _register_later() -> None:
        await asyncio.sleep(0.2)
        ws_runtime.register_sid(sid)
        ws_runtime.subscribe_sid_to_context(sid, context_id)
        ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
        ws_runtime.store_sid_remote_file_metadata(
            sid, {"enabled": True, "write_enabled": True}
        )

    registration = asyncio.create_task(_register_later())
    try:
        response = await tool.execute()
    finally:
        await registration

    assert response.break_loop is False
    assert "reconnected-output" in response.message


@pytest.mark.asyncio
async def test_connected_cli_with_exec_disabled_does_not_wait_and_breaks_loop(
    registered_sid,
) -> None:
    sid = registered_sid
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": False})

    tool = _make_tool({"runtime": "output", "session": 0})

    started = time.monotonic()
    response = await tool.execute()
    elapsed = time.monotonic() - started

    assert elapsed < code_execution_remote.NO_CLI_RECONNECT_GRACE_SECONDS
    assert response.break_loop is True
    assert "F4" in response.message


@pytest.mark.asyncio
async def test_connected_cli_write_blocked_does_not_wait_and_breaks_loop(
    registered_sid,
) -> None:
    sid = registered_sid
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
    ws_runtime.store_sid_remote_file_metadata(
        sid, {"enabled": True, "write_enabled": False}
    )

    tool = _make_tool({"runtime": "terminal", "code": "echo hi", "session": 0})

    started = time.monotonic()
    response = await tool.execute()
    elapsed = time.monotonic() - started

    assert elapsed < code_execution_remote.NO_CLI_RECONNECT_GRACE_SECONDS
    assert response.break_loop is True
    assert "F3" in response.message
