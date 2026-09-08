import base64
import hashlib
import io
import uuid

import pytest

from helpers import file_connections
from plugins._a0_connector.helpers import file_browser, ws_runtime as runtime


def test_host_discovery_permissions_and_disconnect(monkeypatch):
    metadata = {"enabled": True, "write_enabled": False, "file_browser": True, "root_path": "/host"}
    monkeypatch.setattr(runtime, "remote_tool_sids_for_context", lambda context: ["cli", "launcher"])
    monkeypatch.setattr(runtime, "remote_file_metadata_for_sid", lambda sid: metadata)
    monkeypatch.setattr(runtime, "launcher_gateway_metadata_for_sid", lambda sid: {"id": "gateway"} if sid == "launcher" else None)
    provider = file_browser.Provider()
    monkeypatch.setattr(file_connections, "providers", lambda: {provider.id: provider})
    items = list(provider.connections().values())
    assert items[0]["name"] == "A0 CLI — /host"
    assert items[1]["name"] == "A0 Launcher — /host"
    assert items[0]["id"] != items[1]["id"]
    assert items[0]["permissions"]["browse"] and not items[0]["permissions"]["edit"]
    assert "_sid" not in file_connections.listing_config()["connections"][0]
    with pytest.raises(ValueError, match="managed"):
        file_connections.save_connection({"provider": "host"})
    with pytest.raises(ValueError, match="host application"):
        file_connections.remove_connection("host", items[0]["id"])
    fs = file_browser.HostFiles(items[0])
    with pytest.raises(PermissionError):
        fs.write("sample", io.BytesIO(b"hello"))
    metadata["root_path"] = "/changed"
    with pytest.raises(ValueError, match="disconnected or changed"):
        fs.list("")
    metadata["enabled"] = False
    assert provider.connections() == {}


def test_host_requests_use_matching_socket_and_cleanup(monkeypatch):
    item = {"id": "test", "_sid": "cli", "root_path": "/host", "status": "",
            "permissions": {"browse": True, "download": True, "upload": True}}
    monkeypatch.setattr(file_browser.Provider, "connections", lambda self: {"test": item})
    class Manager:
        async def emit_to(self, namespace, sid, event, payload, **kwargs):
            assert sid == "cli" and payload["root_path"] == "/host"
            assert payload["op"] == "files_read_http"
            from types import SimpleNamespace
            file_browser.receive_upload(payload["transfer_token"], SimpleNamespace(stream=io.BytesIO(b"\0test")))
            result = {"ok": True, "result": {"revision": hashlib.sha256(b"\0test").hexdigest()}}
            assert not runtime.resolve_pending_file_op(payload["op_id"], sid="other", payload=result)
            assert runtime.resolve_pending_file_op(payload["op_id"], sid=sid, payload=result)
    monkeypatch.setattr(file_browser, "get_shared_ws_manager", Manager)
    output = io.BytesIO()
    assert file_browser.HostFiles(item).read("sample", output, 100) == hashlib.sha256(b"\0test").hexdigest()
    assert output.getvalue() == b"\0test"
    assert not runtime._pending_file_ops
    assert not file_browser.INCOMING
    with pytest.raises(ValueError, match="expired"):
        file_browser.receive_upload("expired", None)


def test_http_transfer_requires_session_auth_and_csrf():
    from plugins._a0_connector.api.file_browser_transfer import FileBrowserTransfer
    assert FileBrowserTransfer.requires_auth()
    assert FileBrowserTransfer.requires_csrf()


def test_failed_receipt_cleans_slot_and_partial_file(tmp_path, monkeypatch):
    from types import SimpleNamespace
    item = {"id": "receipt", "permissions": {"download": True}}
    monkeypatch.setattr(file_browser.Provider, "connections", lambda self: {"receipt": item})
    monkeypatch.setattr(file_browser.files, "get_abs_path", lambda *args: str(tmp_path))
    def receive(self, op, path, **data):
        assert op == "read_http"
        return file_browser.receive_upload(data["transfer_token"], SimpleNamespace(stream=io.BytesIO(b"oversized")))
    monkeypatch.setattr(file_browser.HostFiles, "call", receive)
    with pytest.raises(ValueError, match="size limit"):
        file_browser.HostFiles(item).read("sample", io.BytesIO(), 2)
    assert not file_browser.INCOMING
    assert not list(tmp_path.iterdir())


def test_launcher_ambiguity_and_scope_ack_preserve_host_boundary():
    first, second = uuid.uuid4().hex, uuid.uuid4().hex
    def gateway(identity, writable=True):
        return {"version": 1, "kind": "launcher", "id": identity, "host_label": "Host",
                "state": "connected", "master_enabled": True,
                "scopes": {"files": True, "file_write": writable}}
    try:
        runtime.register_sid(first)
        runtime.store_sid_launcher_gateway_metadata(first, gateway(first))
        runtime.store_sid_remote_file_metadata(first, {"enabled": True, "write_enabled": True,
                                                       "file_browser": 1, "root_path": "/bounded"})
        item = next(iter(file_browser.Provider().connections().values()))
        assert item["permissions"]["edit"]
        runtime.resolve_pending_gateway_control("no-pending", sid=first,
                                                payload={"gateway": gateway(first, False)})
        metadata = runtime.remote_file_metadata_for_sid(first)
        assert metadata["file_browser"] and metadata["root_path"] == "/bounded"
        assert not next(iter(file_browser.Provider().connections().values()))["permissions"]["edit"]
        runtime.register_sid(second)
        runtime.store_sid_launcher_gateway_metadata(second, gateway(second))
        runtime.store_sid_remote_file_metadata(second, {"enabled": True, "file_browser": 1, "root_path": "/other"})
        assert file_browser.Provider().connections() == {}
    finally:
        for sid in (first, second):
            runtime.unregister_sid(sid)
            runtime.clear_sid_launcher_gateway_metadata(sid)
            runtime.clear_sid_remote_file_metadata(sid)


def test_context_stop_releases_transfer_before_scheduling_notice(monkeypatch):
    from helpers import defer
    from types import SimpleNamespace
    transfer = SimpleNamespace(context_id="ctx", cancel_reason="", abort_sent=False,
                               transfer_id="out", kind="connector_file_op", op_id="op", sid="sid")
    monkeypatch.setattr(runtime, "_outgoing_transfers", {"out": transfer})
    notices = []
    class Task:
        def __init__(self, **kwargs): pass
        def start_task(self, fn, transfers, reason):
            assert not runtime._outgoing_transfers
            assert transfer.abort_sent
            notices.extend(transfers)
    monkeypatch.setattr(defer, "DeferredTask", Task)
    runtime.cancel_context_transfers("ctx")
    assert notices == [transfer]
