import asyncio
import concurrent.futures
import importlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import psutil
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentContext
from plugins._browser.helpers import config, interactive_view, runtime


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def idle_core(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime.files, "get_abs_path", lambda *parts: str(tmp_path.joinpath(*parts)))
    monkeypatch.setattr(runtime, "get_browser_config", lambda: {"idle_timeout_minutes": 60})
    monkeypatch.setattr(AgentContext, "get", lambda context_id: None)
    monkeypatch.setattr(runtime, "_save_browser_tabs", lambda tabs: None)
    core = runtime._BrowserRuntimeCore("shared")
    core.context = SimpleNamespace(close=AsyncMock())
    core.playwright = SimpleNamespace(stop=AsyncMock())
    core._last_used = time.monotonic() - 7200
    core._restore_state_loaded = True
    core._restored_context_ids = {"first", "second"}
    core.pages = {
        bid: runtime.BrowserPage(
            id=bid, context_id=owner,
            page=SimpleNamespace(url=f"https://{owner}.test/", close=AsyncMock()),
        )
        for bid, owner in enumerate(("first", "second"), 1)
    }
    core._last_interacted_browser_ids = {"first": 1, "second": 2}
    return core


@pytest.mark.parametrize("value, expected", [(None, 60), (0, 0), (60, 60), (-1, 0), (1500, 1440), ("bad", 60)])
def test_idle_timeout_normalization(value, expected):
    settings = {} if value is None else {"idle_timeout_minutes": value}
    assert config.normalize_browser_config(settings)["idle_timeout_minutes"] == expected


@pytest.mark.anyio
@pytest.mark.parametrize("busy", ["running", "paused", "call", "download", "recent_chat", "recent_browser", "disabled"])
async def test_idle_cleanup_preserves_active_work(idle_core, monkeypatch, busy):
    core = idle_core
    context = SimpleNamespace(
        output_data={}, data={},
        is_running=lambda: busy in {"running", "paused"},
        paused=busy == "paused",
        last_message=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    monkeypatch.setattr(AgentContext, "get", lambda context_id: context if context_id == "second" else None)
    if busy == "call":
        core._active_calls = 1
    elif busy == "download":
        core._downloads.add(object())
    elif busy == "recent_chat":
        context.last_message = datetime.now(timezone.utc)
    elif busy == "recent_browser":
        core._last_used = time.monotonic()
    elif busy == "disabled":
        monkeypatch.setattr(runtime, "get_browser_config", lambda: {"idle_timeout_minutes": 0})

    assert await core.suspend() is False
    core.context.close.assert_not_awaited()
    assert len(core.pages) == 2


@pytest.mark.anyio
async def test_running_chat_gets_full_grace_period_after_finishing(idle_core, monkeypatch):
    context = SimpleNamespace(
        output_data={}, data={},
        is_running=lambda: True, paused=False,
        last_message=datetime.now(timezone.utc) - timedelta(hours=4),
    )
    monkeypatch.setattr(AgentContext, "get", lambda _: context)
    assert await idle_core.suspend() is False
    context.is_running = lambda: False
    assert await idle_core.suspend() is False
    idle_core._last_used -= 3601
    assert await idle_core.suspend() is True


@pytest.mark.anyio
@pytest.mark.parametrize("parent_key", ["parent_context_id", "_parallel_parent_context_id"])
async def test_running_parent_protects_subordinate_tabs(idle_core, monkeypatch, parent_key):
    child = SimpleNamespace(
        output_data={"parent_context_id": "parent"} if parent_key == "parent_context_id" else {},
        data={"_parallel_parent_context_id": "parent"} if parent_key == "_parallel_parent_context_id" else {},
        is_running=lambda: False, paused=False,
        last_message=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    parent = SimpleNamespace(
        output_data={}, data={}, is_running=lambda: True, paused=False,
        last_message=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    contexts = {"first": child, "parent": parent}
    monkeypatch.setattr(AgentContext, "get", contexts.get)
    assert await idle_core.suspend() is False
    idle_core.context.close.assert_not_awaited()


@pytest.mark.anyio
async def test_suspend_preserves_tabs_and_profile_without_restarting_on_poll(idle_core, monkeypatch):
    core = idle_core
    saved = []
    monkeypatch.setattr(runtime, "_save_browser_tabs", lambda tabs: saved.append(tabs))
    core.profile_dir.mkdir(parents=True)
    cookies = core.profile_dir / "Cookies"
    cookies.write_bytes(b"saved sign-in")
    core.interactive_view.state_dir.mkdir(parents=True)
    context, driver = core.context, core.playwright

    assert await core.suspend() is True
    context.close.assert_awaited_once()
    driver.stop.assert_awaited_once()
    assert cookies.read_bytes() == b"saved sign-in"
    assert saved[-1] == [
        {"context_id": "first", "url": "https://first.test/", "active": True},
        {"context_id": "second", "url": "https://second.test/", "active": True},
    ]
    assert not core.interactive_view.state_dir.exists()
    assert core.context is None and core.playwright is None and not core.pages
    start = AsyncMock(side_effect=AssertionError("Passive polling restarted Chromium"))
    monkeypatch.setattr(core, "ensure_started", start)
    assert (await core.list(restore=False))["browsers"] == []
    assert (await core.list_all(restore=False))["browsers"] == []
    start.assert_not_awaited()


@pytest.mark.anyio
async def test_failed_recovery_save_leaves_browser_open(idle_core, monkeypatch):
    def fail(tabs):
        raise OSError("disk full")

    monkeypatch.setattr(runtime, "_save_browser_tabs", fail)
    with pytest.raises(OSError, match="disk full"):
        await idle_core.suspend()
    idle_core.context.close.assert_not_awaited()
    assert not idle_core._closing and len(idle_core.pages) == 2


@pytest.mark.anyio
async def test_manual_stop_ignores_timeout_but_respects_active_chat(idle_core, monkeypatch):
    core = idle_core
    core._last_used = time.monotonic()
    context = SimpleNamespace(output_data={}, data={}, is_running=lambda: True, paused=False)
    monkeypatch.setattr(AgentContext, "get", lambda _: context)
    assert await core.suspend(if_idle=False) is False
    context.paused = True
    assert await core.suspend(if_idle=False) is True


@pytest.mark.anyio
async def test_worker_tracks_calls_and_serializes_suspend_with_next_use(idle_core, monkeypatch):
    worker = runtime.BrowserRuntime("lifecycle-test")
    monkeypatch.setattr(worker, "_core", idle_core)
    started = concurrent.futures.Future()
    finish = concurrent.futures.Future()

    async def work():
        started.set_result(True)
        await asyncio.wrap_future(finish)

    monkeypatch.setattr(idle_core, "work", work, raising=False)
    try:
        task = asyncio.create_task(worker.call("work"))
        await asyncio.wrap_future(started)
        assert await worker.call("suspend", if_idle=False) is False
        finish.set_result(True)
        await task
        assert idle_core._active_calls == 0
        assert time.monotonic() - idle_core._last_used < 2

        before = idle_core._last_used
        monkeypatch.setattr(idle_core, "list", AsyncMock(return_value={}))
        await worker.call("list", restore=False, touch=False)
        assert idle_core._last_used == before
        await worker.call("list", restore=False)
        assert idle_core._last_used > before

        stopping = concurrent.futures.Future()
        stopped = concurrent.futures.Future()
        events = []

        async def close(**kwargs):
            if not stopping.done():
                stopping.set_result(True)
                await asyncio.wrap_future(stopped)
            events.append("closed")

        async def next_use():
            events.append("used")

        monkeypatch.setattr(idle_core, "close", close)
        monkeypatch.setattr(idle_core, "work", next_use)
        suspension = asyncio.create_task(worker.call("suspend", if_idle=False))
        await asyncio.wrap_future(stopping)
        next_call = asyncio.create_task(worker.call("work"))
        stopped.set_result(True)
        assert await suspension is True
        await next_call
        assert events == ["closed", "used"]
    finally:
        await worker.close()


@pytest.mark.anyio
async def test_stop_api_reports_busy(monkeypatch):
    module = importlib.import_module("plugins._browser.api.stop")
    stop = AsyncMock(return_value=False)
    monkeypatch.setattr(module, "suspend_runtime", stop)
    result = await module.Stop.process(None, {}, None)
    assert result["ok"] is False and "busy" in result["error"]
    stop.assert_awaited_once_with(if_idle=False)


@pytest.mark.parametrize("args, kwargs, stops", [
    (("_browser", False), {}, True),
    ((), {"plugin_name": "_browser", "enabled": False}, True),
    (("_browser", False, "project"), {}, False),
    (("_browser", False, "", "profile"), {}, False),
    (("_browser", True), {}, False),
    (("_other", False), {}, False),
])
def test_global_disable_closes_browser_before_extensions_disappear(monkeypatch, args, kwargs, stops):
    module = importlib.import_module(
        "plugins._browser.extensions.python._functions.helpers.plugins.toggle_plugin.start._10_stop_browser"
    )
    calls = []
    monkeypatch.setattr(module, "close_all_runtimes_sync", lambda: calls.append(True))
    module.StopBrowserOnDisable(agent=None).execute({"args": args, "kwargs": kwargs})
    assert bool(calls) is stops


def test_stale_display_cleanup_preserves_live_recent_and_foreign_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(interactive_view.files, "get_abs_path", lambda *parts: str(tmp_path))
    paths = [tmp_path / f"browser-{i:032x}" for i in range(5)]
    for path in paths:
        path.mkdir()
    stale, referenced, owned, reused_pid, recent = paths
    identity = {"pid": os.getpid(), "started": psutil.Process().create_time()}
    (owned / "owner.json").write_text(json.dumps(identity))
    (reused_pid / "owner.json").write_text(json.dumps({**identity, "started": identity["started"] - 100}))
    for path in paths[:-1]:
        os.utime(path, (time.time() - 90000, time.time() - 90000))
    foreign = tmp_path / "keep"
    foreign.mkdir()
    link = tmp_path / f"browser-{'f' * 32}"
    link.symlink_to(foreign)
    monkeypatch.setattr(psutil, "process_iter", lambda: [SimpleNamespace(cmdline=lambda: [f"--socket-dir={referenced}/sockets"])])

    interactive_view.cleanup_stale_displays()
    assert not stale.exists() and not reused_pid.exists()
    assert all(path.exists() for path in (referenced, owned, recent, foreign, link))


def test_stale_display_cleanup_skips_unknown_process_ownership(monkeypatch, tmp_path):
    monkeypatch.setattr(interactive_view.files, "get_abs_path", lambda *parts: str(tmp_path))
    stale = tmp_path / f"browser-{'a' * 32}"
    stale.mkdir()
    os.utime(stale, (time.time() - 90000, time.time() - 90000))

    def denied():
        raise psutil.AccessDenied(123)

    monkeypatch.setattr(psutil, "process_iter", lambda: [SimpleNamespace(cmdline=denied)])
    interactive_view.cleanup_stale_displays()
    assert stale.exists()
