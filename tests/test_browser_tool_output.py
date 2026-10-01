import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from plugins._browser.helpers import runtime as runtime_module
from plugins._browser.helpers.config import normalize_browser_config
from plugins._browser.helpers.runtime import BrowserPage, BrowserRuntime, _BrowserRuntimeCore
from plugins._browser.tools.browser import Browser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_format_result_minifies_tool_json() -> None:
    result = {"browsers": [{"id": "b1", "title": "Example"}]}

    formatted = Browser._format_result("list", result)

    assert "\n" not in formatted
    assert json.loads(formatted) == result


def test_format_result_keeps_content_document_plain() -> None:
    formatted = Browser._format_result("content", {"document": "<html></html>"})

    assert formatted == "<html></html>"


@pytest.mark.asyncio
async def test_evaluate_uses_script_arg(monkeypatch) -> None:
    core = _BrowserRuntimeCore("ctx")
    seen: list[str] = []

    async def fake_evaluate(bid, script):
        seen.append(script)
        return 7

    monkeypatch.setattr(core, "evaluate", fake_evaluate)

    result = await core._dispatch_call({"action": "evaluate", "script": "1+1"})

    assert result == 7
    assert seen == ["1+1"]


@pytest.mark.asyncio
@pytest.mark.parametrize("args", [{"expression": "document.title"}, {}, {"script": " "}, {"script": 42}])
async def test_evaluate_rejects_missing_or_invalid_script(monkeypatch, args) -> None:
    core = _BrowserRuntimeCore("ctx")
    started = AsyncMock()
    monkeypatch.setattr(core, "ensure_started", started)
    with pytest.raises(ValueError, match="non-empty 'script'"):
        await core._dispatch_call({"action": "evaluate", **args})
    result = await core.multi([{"action": "evaluate", **args}])
    assert result == [{"ok": False, "error": "evaluate requires a non-empty 'script' string"}]
    started.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [2, None, False, 0, {"answer": 42}])
async def test_evaluate_preserves_javascript_results(monkeypatch, value) -> None:
    core, page, session = _evaluate_runtime(monkeypatch)
    page.evaluate.return_value = value
    script = "() => " + json.dumps(value)
    result = await core.evaluate(3, script)
    assert result == {"result": value, "state": {"id": 3}}
    page.evaluate.assert_awaited_once_with(script, isolated_context=False)
    session.detach.assert_awaited_once()
    session.send.assert_not_awaited()


def _evaluate_runtime(monkeypatch, timeout=0.1):
    core = _BrowserRuntimeCore("evaluate-test")
    session = SimpleNamespace(send=AsyncMock(), detach=AsyncMock())
    page = SimpleNamespace(
        evaluate=AsyncMock(return_value=2),
        context=SimpleNamespace(new_cdp_session=AsyncMock(return_value=session)),
        reload=AsyncMock(), close=AsyncMock(), is_closed=lambda: False,
    )
    core.pages[3] = BrowserPage(3, page, "evaluate-test")
    monkeypatch.setattr(core, "ensure_started", AsyncMock())
    monkeypatch.setattr(core, "_state", AsyncMock(return_value={"id": 3}))
    monkeypatch.setattr(core, "_persist_browser_tabs", lambda: None)
    monkeypatch.setattr(runtime_module, "get_browser_config", lambda agent=None: {
        "evaluate_timeout_seconds": timeout,
    })
    return core, page, session


def _hang_until_recovery(page):
    started, stopped = asyncio.Event(), asyncio.Event()
    operations = []

    async def evaluate(script, **kwargs):
        if script != "hang":
            return 2
        operations.append(asyncio.current_task())
        started.set()
        # Independently bounded even if the production deadline is removed.
        try:
            await asyncio.wait_for(stopped.wait(), 1)
        except asyncio.TimeoutError:
            raise RuntimeError("Fake backend watchdog expired") from None
        raise RuntimeError("Execution context destroyed")

    async def recover(**kwargs):
        stopped.set()

    page.evaluate.side_effect = evaluate
    page.reload.side_effect = recover
    page.close.side_effect = recover
    return started, stopped, operations


@pytest.mark.asyncio
async def test_evaluate_timeout_recovers_and_multi_continues(monkeypatch):
    core, page, session = _evaluate_runtime(monkeypatch)
    _, stopped, operations = _hang_until_recovery(page)
    pending_before = asyncio.all_tasks()
    result = await asyncio.wait_for(core.multi([
        {"action": "evaluate", "browser_id": 3, "script": "hang"},
        {"action": "evaluate", "browser_id": 3, "script": "1+1"},
    ]), 2)
    assert result == [
        {"ok": False, "error": "evaluate timed out after 0.1 seconds; affected tab reloaded to cancel pending JavaScript"},
        {"ok": True, "result": {"result": 2, "state": {"id": 3}}},
    ]
    session.send.assert_awaited_once_with("Runtime.terminateExecution")
    assert stopped.is_set() and all(task.done() for task in operations)
    assert not core.pages[3].evaluate_lock.locked()
    assert not (asyncio.all_tasks() - pending_before)
    assert session.detach.await_count == 2
    page.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_evaluate_timeout_is_non_breaking_tool_error(monkeypatch):
    from plugins._browser.tools import browser as tool_module

    core, page, _ = _evaluate_runtime(monkeypatch)
    _hang_until_recovery(page)
    tool = object.__new__(Browser)
    tool.agent = SimpleNamespace(context=SimpleNamespace(id="evaluate-test"))
    tool.method = ""
    monkeypatch.setattr(tool_module, "activate_browser_model", lambda agent: None)
    monkeypatch.setattr(tool_module, "get_runtime", AsyncMock(return_value=SimpleNamespace(
        call=None,
    )))

    async def call(method, *args, **kwargs):
        return await getattr(core, method)(*args, **kwargs)

    tool_module.get_runtime.return_value.call = call
    result = await asyncio.wait_for(tool.execute(action="evaluate", browser_id=3, script="hang"), 2)
    assert result.break_loop is False
    assert result.message == "Browser evaluate failed: evaluate timed out after 0.1 seconds; affected tab reloaded to cancel pending JavaScript"


@pytest.mark.asyncio
@pytest.mark.parametrize("caller_cancel", [False, True])
async def test_confirmed_evaluate_interruption_preserves_page(monkeypatch, caller_cancel):
    core, page, session = _evaluate_runtime(monkeypatch)
    started, stopped, operations = _hang_until_recovery(page)
    session.send.side_effect = lambda method: stopped.set()
    task = asyncio.create_task(core.evaluate(3, "hang"))
    await asyncio.wait_for(started.wait(), 1)
    if caller_cancel:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if caller_cancel else TimeoutError) as error:
        await asyncio.wait_for(task, 2)
    if not caller_cancel:
        assert str(error.value) == "evaluate timed out after 0.1 seconds"
    page.reload.assert_not_awaited()
    page.close.assert_not_awaited()
    session.detach.assert_awaited_once()
    assert core.pages[3].page is page
    assert all(operation.done() and not operation.cancelled() for operation in operations)
    assert (await core.evaluate(3, "1+1"))["result"] == 2


@pytest.mark.asyncio
async def test_evaluate_stuck_recovery_is_bounded(monkeypatch):
    core, page, session = _evaluate_runtime(monkeypatch)
    _hang_until_recovery(page)
    monkeypatch.setattr(runtime_module, "EVALUATE_RECOVERY_TIMEOUT_SECONDS", 0.03)
    monkeypatch.setattr(runtime_module, "EVALUATE_TERMINATION_GRACE_SECONDS", 0.005)

    async def stuck_reload(**kwargs):
        await asyncio.sleep(1)

    page.reload.side_effect = stuck_reload
    with pytest.raises(TimeoutError, match="0.1 seconds"):
        await asyncio.wait_for(core.evaluate(3, "hang"), 0.5)
    page.close.assert_awaited_once()
    session.detach.assert_awaited_once()


@pytest.mark.asyncio
async def test_provider_wait_timeout_is_not_proof_of_javascript_cancellation(monkeypatch):
    core, page, session = _evaluate_runtime(monkeypatch)
    page.evaluate.side_effect = asyncio.TimeoutError
    with pytest.raises(TimeoutError, match="reloaded to cancel pending JavaScript"):
        await core.evaluate(3, "hang")
    session.send.assert_awaited_once_with("Runtime.terminateExecution")
    page.reload.assert_awaited_once()


@pytest.mark.asyncio
async def test_evaluate_caller_cancellation_recovers_before_return(monkeypatch):
    core, page, session = _evaluate_runtime(monkeypatch)
    started, stopped, operations = _hang_until_recovery(page)
    task = asyncio.create_task(core.evaluate(3, "hang"))
    await asyncio.wait_for(started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)
    assert stopped.is_set() and all(task.done() for task in operations)
    session.send.assert_awaited_once_with("Runtime.terminateExecution")
    session.detach.assert_awaited_once()
    assert not core.pages[3].evaluate_lock.locked()
    assert (await core.evaluate(3, "1+1"))["result"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("closed", [False, True])
async def test_evaluate_javascript_or_closed_page_error_is_preserved(monkeypatch, closed):
    core, page, session = _evaluate_runtime(monkeypatch)
    page.is_closed = lambda: closed
    page.evaluate.side_effect = RuntimeError("page closed" if closed else "script error")
    with pytest.raises(RuntimeError, match="page closed" if closed else "script error"):
        await core.evaluate(3, "1+1")
    page.reload.assert_not_awaited()
    session.send.assert_not_awaited()
    session.detach.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("close_fails", [False, True])
async def test_evaluate_recovery_failure_closes_only_affected_page(monkeypatch, close_fails):
    core, page, session = _evaluate_runtime(monkeypatch)
    _, _, operations = _hang_until_recovery(page)
    unrelated = BrowserPage(4, SimpleNamespace(), "other-chat")
    core.pages[4] = unrelated
    page.reload.side_effect = RuntimeError("reload failed")
    if close_fails:
        page.close.side_effect = RuntimeError("close failed")
    with pytest.raises(TimeoutError, match="evaluate timed out after 0.1 seconds") as error:
        await asyncio.wait_for(core.evaluate(3, "hang"), 2)
    assert ("recovery failed" in str(error.value)) is close_fails
    assert (3 in core.pages) is close_fails
    assert core.pages[4] is unrelated
    page.close.assert_awaited_once_with(run_before_unload=False)
    assert all(task.done() for task in operations)
    session.detach.assert_awaited_once()


@pytest.mark.parametrize("value", [0, -1, True, None, "", "bad", "nan", "inf", float("nan"), float("inf"), 0.09, 60.1])
def test_evaluate_timeout_rejects_invalid_settings(value):
    with pytest.raises(ValueError, match="between 0.1 and 60 seconds"):
        normalize_browser_config({"evaluate_timeout_seconds": value})


def test_evaluate_timeout_defaults_and_numeric_strings():
    assert normalize_browser_config({})["evaluate_timeout_seconds"] == 30
    assert normalize_browser_config({"evaluate_timeout_seconds": "0.1"})["evaluate_timeout_seconds"] == 0.1
    assert normalize_browser_config({"evaluate_timeout_seconds": 60})["evaluate_timeout_seconds"] == 60


@pytest.mark.asyncio
async def test_browser_worker_propagates_cancellation_and_waits_for_cleanup(monkeypatch):
    runtime = BrowserRuntime("evaluate-worker-test")
    loop = asyncio.get_running_loop()
    started = loop.create_future()
    cleaned = []

    async def work():
        loop.call_soon_threadsafe(started.set_result, None)
        try:
            await asyncio.sleep(1)
        finally:
            await asyncio.sleep(0.01)
            cleaned.append(True)

    monkeypatch.setattr(runtime._core, "evaluate", work)
    try:
        task = asyncio.create_task(runtime.call("evaluate"))
        await asyncio.wait_for(started, 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 2)
        assert cleaned == [True]

        async def pending():
            return len([task for task in asyncio.all_tasks() if task is not asyncio.current_task()])

        monkeypatch.setattr(runtime._core, "state", pending)
        assert await runtime.call("state") == 0
    finally:
        runtime._worker.kill(terminate_thread=True)


def test_webui_beautifier_formats_objects_and_arrays() -> None:
    source = (
        PROJECT_ROOT
        / "plugins"
        / "_browser"
        / "extensions"
        / "webui"
        / "get_tool_message_handler"
        / "browser-tool-handler.js"
    ).read_text(encoding="utf-8")
    start = source.index("function beautifyJsonForDisplay")
    end = source.index("\n}", start) + 2
    object_literal = json.dumps({"browsers": [{"id": 1}]})
    array_literal = json.dumps([{"id": 1}, {"id": 2}])
    script = (
        source[start:end]
        + "\nconst pretty = beautifyJsonForDisplay(" + json.dumps(object_literal) + ");\n"
        + "if (!pretty.includes('\\n')) throw new Error('object JSON was not beautified');\n"
        + "if (pretty !== " + json.dumps(json.dumps({"browsers": [{"id": 1}]}, indent=2)) + ") throw new Error('object JSON content changed');\n"
        + "const arrayPretty = beautifyJsonForDisplay(" + json.dumps(array_literal) + ");\n"
        + "if (!arrayPretty.includes('\\n')) throw new Error('array JSON was not beautified');\n"
        + "if (JSON.parse(arrayPretty).length !== 2) throw new Error('array content changed');\n"
        + "const padded = beautifyJsonForDisplay('  ' + " + json.dumps(json.dumps({"a": 1})) + "  );\n"
        + "if (padded !== " + json.dumps('{\n  "a": 1\n}') + ") throw new Error('padded JSON was not trimmed');\n"
        + "if (beautifyJsonForDisplay('plain document') !== 'plain document') throw new Error('plain text changed');\n"
        + "if (beautifyJsonForDisplay('{broken') !== '{broken') throw new Error('invalid JSON changed');\n"
    )

    subprocess.run(["node", "--input-type=module", "-e", script], check=True, text=True)
