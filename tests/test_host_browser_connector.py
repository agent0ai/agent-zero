from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._a0_connector.helpers import ws_runtime
from plugins._browser.helpers import connector_runtime as connector_runtime_module
from plugins._browser.helpers.connector_runtime import ConnectorBrowserRuntime


def _agent(context_id: str = "ctx-host"):
    return SimpleNamespace(context=SimpleNamespace(id=context_id))


@pytest.fixture
def evaluate_bridge(monkeypatch):
    sid, context_id = "evaluate-sid", "evaluate-context"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    ws_runtime.store_sid_host_browser_metadata(sid, {
        "supported": True, "enabled": True, "status": "ready",
    })
    monkeypatch.setattr(connector_runtime_module, "get_browser_config", lambda agent=None: {
        "evaluate_timeout_seconds": 0.1,
    })
    monkeypatch.setattr(connector_runtime_module, "get_shared_ws_manager", lambda: None)
    runtime = ConnectorBrowserRuntime(context_id, _agent(context_id))
    try:
        yield runtime, sid
    finally:
        ws_runtime.unregister_sid(sid)


def test_host_browser_registration_replaces_or_clears_the_protocol_on_hello():
    from plugins._a0_connector.api.ws_connector import WsConnector

    sid, context_id = "browser-contract-sid", "browser-contract-context"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    handler = WsConnector(None, None)
    try:
        advertisement = {"supported": True, "enabled": True, "status": "ready"}
        for version in (3, None, 3, 2):
            metadata = dict(advertisement)
            if version is not None:
                metadata["contract_version"] = version
            handler._store_remote_tool_metadata({"host_browser": metadata}, sid)
            expected = sid if version == 3 else None
            assert ws_runtime.select_host_browser_candidate_sid(context_id) == expected
            assert ws_runtime.select_host_browser_target_sid(context_id) == expected
    finally:
        ws_runtime.unregister_sid(sid)


@pytest.mark.asyncio
async def test_host_browser_sends_cdp_and_scoped_file_operations(monkeypatch, evaluate_bridge):
    runtime, _ = evaluate_bridge
    sent = []

    async def emit(sid, event, payload, **kwargs):
        sent.append(payload)
        result = {"closed": payload["browser_id"]} if payload["action"] == "close" else {}
        ws_runtime.resolve_pending_browser_op(payload["op_id"], sid=sid, payload={"ok": True, "result": result})

    monkeypatch.setattr(connector_runtime_module, "emit_connector_event", emit)
    await runtime.call("cdp", None, "Browser.getVersion", None, None)
    await runtime.call("multi", [
        {"action": "upload_file", "browser_id": 1, "ref": 2, "path": "note.txt"},
        {"action": "screenshot", "browser_id": 1, "path": "note.png"},
    ])
    assert await runtime.call("close_browser", 1) == {"closed": 1}
    assert [p["action"] for p in sent] == ["cdp", "upload_file", "screenshot", "close"]
    assert sent[0]["cdp_method"] == "Browser.getVersion"
    assert [p["path"] for p in sent[1:3]] == ["note.txt", "note.png"]


@pytest.mark.asyncio
async def test_host_evaluate_deadline_and_multi_results(monkeypatch, evaluate_bridge):
    runtime, sid = evaluate_bridge
    payloads = []

    async def emit(sid, event, payload, **kwargs):
        payloads.append(payload)
        assert payload["evaluate_timeout_seconds"] == 0.1
        response = ({"ok": False, "error": "evaluate timed out after 0.1 seconds"}
                    if payload.get("script") == "hang" else {"ok": True, "result": {"result": 2}})
        ws_runtime.resolve_pending_browser_op(payload["op_id"], sid=sid, payload=response)

    monkeypatch.setattr(connector_runtime_module, "emit_connector_event", emit)
    results = await runtime.call("multi", [
        {"action": "evaluate", "browser_id": 1, "script": "hang", "evaluate_timeout_seconds": 999},
        {"action": "evaluate", "browser_id": 1, "script": "1+1"},
    ])
    assert results[0]["ok"] is False and "0.1 seconds" in results[0]["error"]
    assert results[1] == {"ok": True, "result": {"result": 2}}
    assert not ws_runtime._pending_browser_ops


@pytest.mark.asyncio
@pytest.mark.parametrize("caller_cancel", [False, True])
@pytest.mark.parametrize("confirmed", [False, True])
async def test_host_evaluate_transport_cancellation_requires_ack(
    monkeypatch, evaluate_bridge, caller_cancel, confirmed,
):
    runtime, sid = evaluate_bridge
    started = asyncio.Event()
    payloads = []
    monkeypatch.setattr(connector_runtime_module, "EVALUATE_CANCEL_TIMEOUT_SECONDS", 0.05)

    async def emit(sid, event, payload, **kwargs):
        payloads.append(payload)
        if payload["action"] == "evaluate":
            started.set()
            return
        assert payload["action"] == "cancel_evaluate"
        assert payload["target_op_id"] == payloads[0]["op_id"]
        ws_runtime.resolve_pending_browser_op(payload["op_id"], sid=sid, payload={
            "ok": True, "result": {"cancelled": confirmed},
        })

    monkeypatch.setattr(connector_runtime_module, "emit_connector_event", emit)
    before = asyncio.all_tasks()
    task = asyncio.create_task(runtime.call("evaluate", 1, "hang"))
    await asyncio.wait_for(started.wait(), 1)
    if caller_cancel:
        task.cancel()
    error_type = asyncio.CancelledError if caller_cancel and confirmed else RuntimeError
    with pytest.raises(error_type) as error:
        await asyncio.wait_for(task, 1)
    if not confirmed:
        assert "cancellation could not be confirmed" in str(error.value)
    elif not caller_cancel:
        assert "host cancellation confirmed" in str(error.value)
    assert len(payloads) == 2
    assert not ws_runtime._pending_browser_ops
    assert not (asyncio.all_tasks() - before)


@pytest.mark.asyncio
@pytest.mark.parametrize("script", [None, "", " ", 42])
async def test_host_evaluate_invalid_script_is_rejected_before_prepare(monkeypatch, evaluate_bridge, script):
    runtime, _ = evaluate_bridge
    emitted = AsyncMock()
    monkeypatch.setattr(connector_runtime_module, "emit_connector_event", emitted)
    with pytest.raises(ValueError, match="non-empty 'script'"):
        await runtime.call("evaluate", 1, script)
    emitted.assert_not_awaited()


@pytest.mark.asyncio
async def test_host_evaluate_disconnect_clears_pending_operation(monkeypatch, evaluate_bridge):
    runtime, sid = evaluate_bridge

    async def emit(sid, event, payload, **kwargs):
        ws_runtime.fail_pending_browser_ops_for_sid(sid, error="connector disconnected")

    monkeypatch.setattr(connector_runtime_module, "emit_connector_event", emit)
    with pytest.raises(RuntimeError, match="disconnected"):
        await runtime.call("evaluate", 1, "hang")
    assert not ws_runtime._pending_browser_ops


def test_host_required_runtime_error_is_repairable(monkeypatch):
    from plugins._browser.helpers import selector as browser_selector

    monkeypatch.setattr(
        browser_selector,
        "get_browser_config",
        lambda agent=None: {"runtime_backend": "host_required"},
    )

    with pytest.raises(browser_selector.RepairableException, match="Bring Your Own Browser") as exc_info:
        asyncio.run(browser_selector.get_tool_runtime(_agent("ctx-host-required-missing")))

    message = str(exc_info.value)
    assert "Internal Docker browser" in message
    assert "/browser container" in message


def test_host_browser_metadata_selection_is_context_scoped():
    sid = "sid-host-browser"
    context_id = "ctx-host-browser"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    try:
        ws_runtime.store_sid_host_browser_metadata(
            sid,
            {
                "supported": True,
                "enabled": True,
                "status": "ready",
                "browser_family": "chrome",
                "profile_label": "Default",
                "content_helper_sha256": "abc123",
                "features": ["open", "content"],
            },
        )

        assert ws_runtime.select_host_browser_target_sid(context_id) == sid
        rows = ws_runtime.host_browser_metadata_for_context(context_id)
        assert rows[0]["browser_family"] == "chrome"
        assert rows[0]["enabled"] is True
        assert rows[0]["content_helper_sha256"] == "abc123"
    finally:
        ws_runtime.unregister_sid(sid)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,selection", [
    ("agent", "chrome-cdp"),
    ("existing", "ws://localhost:9222/devtools/browser/CaseSensitive"),
])
async def test_connector_uses_configured_host_profile_for_single_and_batch_calls(monkeypatch, evaluate_bridge, mode, selection):
    runtime, _ = evaluate_bridge
    monkeypatch.setattr(connector_runtime_module, "get_browser_config", lambda agent: {
        "host_browser_profile_mode": mode, "host_browser_selection": selection,
    })
    send = AsyncMock(return_value={})
    monkeypatch.setattr(runtime, "_send_browser_op", send)
    await runtime.call("list")
    await runtime.call("multi", [{"action": "list", "profile_mode": "other", "browser_selection": "other"}])
    assert send.await_count == 2
    for call in send.await_args_list:
        payload = call.args[1]
        assert (payload["profile_mode"], payload["browser_selection"]) == (mode, selection)


def test_host_browser_candidate_selection_allows_disabled_supported_cli():
    sid = "sid-host-browser-disabled"
    context_id = "ctx-host-browser-disabled"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    try:
        ws_runtime.store_sid_host_browser_metadata(
            sid,
            {
                "supported": True,
                "enabled": False,
                "status": "disabled",
                "browser_family": "chrome-a0",
                "profile_label": "Default",
                "features": ["ensure", "open"],
            },
        )

        assert ws_runtime.select_host_browser_target_sid(context_id) is None
        assert ws_runtime.select_host_browser_candidate_sid(context_id) == sid
    finally:
        ws_runtime.unregister_sid(sid)


def test_host_browser_candidate_selection_allows_preparable_cli():
    sid = "sid-host-browser-preparable"
    context_id = "ctx-host-browser-preparable"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    try:
        ws_runtime.store_sid_host_browser_metadata(
            sid,
            {
                "supported": False,
                "can_prepare": True,
                "enabled": False,
                "status": "unsupported",
                "browser_family": "chrome-a0",
                "profile_label": "Default",
                "features": ["ensure", "open"],
                "support_reason": "The selected profile requires preparation.",
            },
        )

        assert ws_runtime.select_host_browser_target_sid(context_id) is None
        assert ws_runtime.select_host_browser_candidate_sid(context_id) == sid
        rows = ws_runtime.host_browser_metadata_for_context(context_id)
        assert rows[0]["can_prepare"] is True
    finally:
        ws_runtime.unregister_sid(sid)


def test_host_browser_metadata_requires_explicit_preparation_capability():
    sid = "sid-host-browser-not-preparable"
    context_id = "ctx-host-browser-not-preparable"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    try:
        ws_runtime.store_sid_host_browser_metadata(
            sid,
            {
                "supported": False,
                "enabled": False,
                "status": "unsupported",
                "browser_family": "chrome-a0",
                "profile_label": "Default",
                "features": ["ensure", "open"],
                "support_reason": "Enable remote debugging.",
            },
        )

        rows = ws_runtime.host_browser_metadata_for_context(context_id)
        assert rows[0]["can_prepare"] is False
        assert ws_runtime.select_host_browser_candidate_sid(context_id) is None
    finally:
        ws_runtime.unregister_sid(sid)


def test_pending_browser_op_resolves_and_disconnect_fails():
    async def run() -> None:
        sid = "sid-browser-pending"
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, object]] = loop.create_future()
        ws_runtime.store_pending_browser_op(
            "op-browser",
            sid=sid,
            future=future,
            loop=loop,
            context_id="ctx",
        )

        assert ws_runtime.resolve_pending_browser_op(
            "op-browser",
            sid=sid,
            payload={"op_id": "op-browser", "ok": True, "result": {"id": 1}},
        )
        assert await future == {"op_id": "op-browser", "ok": True, "result": {"id": 1}}

        future2: asyncio.Future[dict[str, object]] = loop.create_future()
        ws_runtime.store_pending_browser_op(
            "op-browser-2",
            sid=sid,
            future=future2,
            loop=loop,
            context_id="ctx",
        )
        ws_runtime.fail_pending_browser_ops_for_sid(sid, error="gone")
        assert await future2 == {"op_id": "op-browser-2", "ok": False, "error": "gone"}

    asyncio.run(run())


def test_host_browser_setup_api_dispatches_to_connected_cli(monkeypatch):
    from plugins._browser.api import host_browser_setup

    async def run() -> None:
        sid = "sid-browser-setup"
        emitted: list[dict[str, object]] = []

        class FakeWsManager:
            async def emit_to(self, namespace, target_sid, event, payload, handler_id=""):
                del namespace, event, handler_id
                assert target_sid == sid
                emitted.append(dict(payload))
                ws_runtime.resolve_pending_browser_op(
                    payload["op_id"],
                    sid=target_sid,
                    payload={
                        "op_id": payload["op_id"],
                        "ok": True,
                        "result": {"url": "chrome://inspect/#remote-debugging"},
                    },
                )

        monkeypatch.setattr(host_browser_setup, "get_shared_ws_manager", lambda: FakeWsManager())
        ws_runtime.register_sid(sid)
        try:
            ws_runtime.store_sid_host_browser_metadata(
                sid,
                {
                    "supported": True,
                    "enabled": False,
                    "status": "disabled",
                    "features": ["open_remote_debugging"],
                },
            )
            result = await host_browser_setup.HostBrowserSetup(None, None).process(
                {"browser_family": "chrome"},
                SimpleNamespace(),
            )

            assert result["ok"] is True
            assert emitted[0]["action"] == "open_remote_debugging"
            assert emitted[0]["browser_family"] == "chrome"
        finally:
            ws_runtime.unregister_sid(sid)

    asyncio.run(run())


def test_connector_runtime_normalizes_host_navigation_payloads(monkeypatch):
    import plugins._browser.helpers.connector_runtime as connector_runtime_module

    monkeypatch.setattr(
        connector_runtime_module,
        "get_browser_config",
        lambda agent=None: {"host_browser_profile_mode": "existing"},
    )
    runtime = ConnectorBrowserRuntime("ctx-host", _agent("ctx-host"))

    open_payload = runtime._payload_for_call("open", "localhost:3000")
    empty_open_payload = runtime._payload_for_call("open", "")
    navigate_payload = runtime._payload_for_call("navigate", 7, "novinky.cz")
    multi_payload = runtime._payload_for_call(
        "multi",
        [
            {"action": "open", "url": "example.com"},
            {"action": "navigate", "browser_id": 1, "url": "127.0.0.1:8000/path"},
            {"action": "click", "browser_id": 1, "x": 12, "y": 34},
            {"action": "type", "browser_id": 1, "text": "agent-zero.ai"},
            {"action": "key_chord", "browser_id": 1, "keys": "CTRL+A"},
            {
                "action": "multi",
                "calls": [{"action": "open", "url": "nested.example"}],
            },
            {"action": "content", "browser_id": 1},
        ],
    )

    assert open_payload["url"] == "http://localhost:3000/"
    assert empty_open_payload["url"] == ""
    assert navigate_payload["url"] == "https://novinky.cz/"
    assert multi_payload["calls"][0]["url"] == "https://example.com/"
    assert multi_payload["calls"][1]["url"] == "http://127.0.0.1:8000/path"
    assert multi_payload["calls"][2] == {
        "action": "mouse",
        "browser_id": 1,
        "x": 12,
        "y": 34,
        "event_type": "click",
        "button": "left",
    }
    assert multi_payload["calls"][3] == {
        "action": "keyboard",
        "browser_id": 1,
        "text": "agent-zero.ai",
        "key": "",
    }
    assert multi_payload["calls"][4]["keys"] == ["Control", "A"]
    assert multi_payload["calls"][5]["calls"][0]["url"] == "https://nested.example/"
    assert multi_payload["calls"][6] == {"action": "content", "browser_id": 1}
    assert runtime._payload_for_call("key_chord", 1, "CTRL+A")["keys"] == ["Control", "A"]


def test_connector_runtime_adds_remote_debugging_help_to_cdp_errors():
    runtime = ConnectorBrowserRuntime("ctx-host", _agent("ctx-host"))

    message = runtime._host_browser_error_message(
        "Cannot connect to the host browser remote-debugging endpoint "
        "ws://127.0.0.1:9222/devtools/browser/test. Original error: refused"
    )

    assert "chrome://inspect/#remote-debugging" in message
    assert "opera://inspect/#remote-debugging" in message
    assert "Allow remote debugging for this browser instance" in message
    assert "/browser host on" in message
    assert "Internal Docker browser" in message
    assert "/browser container" in message
    already_helpful = (
        "Open chrome://inspect/#remote-debugging and enable "
        '"Allow remote debugging for this browser instance".'
    )
    already_helpful_message = runtime._host_browser_error_message(already_helpful)
    assert already_helpful in already_helpful_message
    assert "/browser container" in already_helpful_message


def test_connector_runtime_adds_docker_recovery_to_host_errors():
    runtime = ConnectorBrowserRuntime("ctx-host", _agent("ctx-host"))

    message = runtime._host_browser_error_message("Host browser operation failed")

    assert "Internal Docker browser" in message
    assert "/browser container" in message


def test_host_browser_artifacts_become_chat_scoped_files(monkeypatch, tmp_path):
    def fake_get_abs_path(*parts):
        return str(tmp_path.joinpath(*parts))

    def fake_normalize_a0_path(path):
        return "/a0/" + str(Path(path).relative_to(tmp_path)).replace("\\", "/")

    monkeypatch.setattr(connector_runtime_module.chat_media.files, "get_abs_path", fake_get_abs_path)
    monkeypatch.setattr(connector_runtime_module.chat_media.files, "normalize_a0_path", fake_normalize_a0_path)
    runtime = ConnectorBrowserRuntime("ctx-host", _agent("ctx-host"))

    result = runtime._materialize_artifact(
        [
            {
                "ok": True,
                "result": {
                    "browser_id": 1,
                    "artifact": {
                        "filename": "shot.jpg",
                        "mime": "image/jpeg",
                        "encoding": "base64",
                        "data": "ZmFrZQ==",
                    },
                },
            }
        ]
    )

    inner = result[0]["result"]
    assert "artifact" not in inner
    assert Path(inner["path"]).read_bytes() == b"fake"
    assert inner["a0_path"].startswith("/a0/usr/chats/ctx-host/screenshots/browser/shot-")
    assert inner["context_id"] == "ctx-host"
    assert inner["ephemeral"] is False
    assert inner["chat_scoped"] is True
    assert inner["vision_load"]["tool_args"]["paths"] == [inner["a0_path"]]


def test_host_browser_artifact_materialization_rejects_oversized_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(connector_runtime_module, "MAX_ARTIFACT_SIZE_BYTES", 2)
    runtime = ConnectorBrowserRuntime("ctx-host", _agent("ctx-host"))

    with pytest.raises(RuntimeError, match="too large"):
        runtime._materialize_artifact(
            {
                "artifact": {
                    "filename": "shot.jpg",
                    "mime": "image/jpeg",
                    "encoding": "base64",
                    "data": "ZmFrZQ==",
                },
            }
        )

    assert not list(tmp_path.rglob("shot.jpg"))


def test_connector_runtime_ensures_preparable_host_browser_before_action(monkeypatch):
    async def run() -> None:
        import plugins._browser.helpers.connector_runtime as connector_runtime_module

        sid = "sid-host-browser-ensure"
        context_id = "ctx-host-browser-ensure"
        emitted: list[dict[str, object]] = []

        class FakeWsManager:
            async def emit_to(
                self,
                namespace,
                target_sid,
                event,
                payload,
                handler_id="",
                **kwargs,
            ):
                del namespace, event, handler_id, kwargs
                emitted.append(dict(payload))
                assert target_sid == sid
                if payload["action"] == "ensure":
                    ws_runtime.store_sid_host_browser_metadata(
                        sid,
                        {
                            "supported": True,
                            "enabled": True,
                            "status": "active",
                            "browser_family": "chrome-a0",
                            "profile_label": "Default",
                            "features": ["ensure", "open"],
                        },
                    )
                    response = {"op_id": payload["op_id"], "ok": True, "result": {"status": "active"}}
                else:
                    response = {
                        "op_id": payload["op_id"],
                        "ok": True,
                        "result": {"id": 1, "state": {"runtime": "host"}},
                    }
                ws_runtime.resolve_pending_browser_op(payload["op_id"], sid=target_sid, payload=response)

        monkeypatch.setattr(connector_runtime_module, "get_shared_ws_manager", lambda: FakeWsManager())
        monkeypatch.setattr(
            connector_runtime_module,
            "get_browser_config",
            lambda agent=None: {},
        )
        ws_runtime.register_sid(sid)
        ws_runtime.subscribe_sid_to_context(sid, context_id)
        try:
            ws_runtime.store_sid_host_browser_metadata(
                sid,
                {
                    "supported": False,
                    "can_prepare": True,
                    "enabled": False,
                    "status": "unsupported",
                    "browser_family": "chrome-a0",
                    "profile_label": "Default",
                    "features": ["ensure", "open"],
                    "support_reason": "The selected profile requires preparation.",
                },
            )
            runtime = ConnectorBrowserRuntime(context_id, _agent(context_id))

            result = await runtime._dispatch(
                {"op_id": "op-open", "context_id": context_id, "action": "open", "url": "https://example.com"}
            )

            assert result == {"id": 1, "state": {"runtime": "host"}}
            assert [payload["action"] for payload in emitted] == ["ensure", "open"]
            assert [payload["profile_mode"] for payload in emitted] == ["existing", "existing"]
            assert "__spaceBrowserDomHelper__" in emitted[0]["dom_helper"]["source"]
            assert "captureDocument" in emitted[0]["dom_helper"]["required_apis"]
            assert emitted[0]["dom_helper"]["sha256"]
            assert "__spaceBrowserPageContent__" in emitted[0]["content_helper"]["source"]
            assert "capture" in emitted[0]["content_helper"]["required_apis"]
            assert emitted[0]["content_helper"]["sha256"]
        finally:
            ws_runtime.unregister_sid(sid)

    asyncio.run(run())
