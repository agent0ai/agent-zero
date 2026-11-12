from types import SimpleNamespace
import sys

import pytest

from plugins._browser.helpers.extension_uploads import (
    STORE_KEY, UploadSourceDenied, record_user_attachments, prepare_upload,
)


class Context:
    def __init__(self, identity):
        self.id = identity
        self.data = {}

    def get_data(self, key, recursive=False):
        return self.data.get(key)

    def set_data(self, key, value, recursive=False):
        self.data[key] = value


@pytest.fixture
def source(tmp_path, monkeypatch):
    import helpers
    files = SimpleNamespace(fix_dev_path=lambda value:value)
    monkeypatch.setitem(sys.modules, "helpers.files", files)
    monkeypatch.setattr(helpers, "files", files, raising=False)
    path = tmp_path / "user-file.txt"
    path.write_bytes(b"user-provided content")
    path.chmod(0o600)
    return tmp_path, path


def test_only_frozen_current_chat_attachment_can_be_prepared_and_read(source):
    root, path = source
    context = Context("chat-1")
    with pytest.raises(UploadSourceDenied):
        prepare_upload(context, path=str(path), root=root)
    record_user_attachments(context, [str(path)], root=root)
    upload = prepare_upload(context, path=str(path), root=root)
    assert upload.read() == b"user-provided content"
    assert upload.mime_type == "text/plain"
    assert str(path) not in repr(upload)
    sibling = Context("chat-2")
    sibling.data[STORE_KEY] = context.data[STORE_KEY]
    with pytest.raises(UploadSourceDenied):
        prepare_upload(sibling, path=str(path), root=root)
    with pytest.raises(UploadSourceDenied):
        prepare_upload(context, path=str(path), paths=[str(path)], root=root)


def test_replacement_modification_links_and_foreign_paths_are_denied(source, tmp_path):
    root, path = source
    context = Context("chat-1")
    record_user_attachments(context, [str(path)], root=root)
    upload = prepare_upload(context, path=str(path), root=root)
    path.write_bytes(b"different context changed file")
    with pytest.raises(UploadSourceDenied):
        upload.read()
    link = root / "alias.txt"
    link.symlink_to(path)
    record_user_attachments(context, [str(link)], root=root)
    with pytest.raises(UploadSourceDenied):
        prepare_upload(context, path=str(link), root=root)
    with pytest.raises(UploadSourceDenied):
        prepare_upload(context, path="/etc/passwd", root=root)


def test_corrupt_metadata_and_empty_or_multiple_sources_are_denied(source):
    root, path = source
    context = Context("chat-1")
    record_user_attachments(context, [str(path)], root=root)
    context.data[STORE_KEY][0]["byte_count"] = True
    with pytest.raises(UploadSourceDenied):
        prepare_upload(context, path=str(path), root=root)
    for kwargs in ({}, {"paths":[]}, {"paths":[str(path),str(path)]}, {"paths":"not-a-list"}):
        with pytest.raises(UploadSourceDenied):
            prepare_upload(context, root=root, **kwargs)


def test_runtime_upload_stages_only_recorded_bytes_after_operation_dispatch(source):
    import asyncio
    from dataclasses import replace
    from test_browser_extension_runtime import _fixture, _allow, _authorize
    from plugins._browser.helpers.extension_runtime import ExtensionBrowserRuntime
    from plugins._a0_connector.helpers.browser_bridge_operations import BrowserBridgeOperationBroker

    root, path = source
    context = Context("context-1")
    record_user_attachments(context, [str(path)], root=root)

    async def scenario():
        binding, policy = _fixture()
        _allow(policy)
        payloads, staged = [], []
        def authorize(binding):
            base = _authorize(binding)
            return replace(base, actions=base.actions | {"upload_file"},
                           features=base.features | {"trusted_input_v1", "artifacts_v1"})
        async def sender(_sid, _event, payload, _correlation, _principal):
            payloads.append(payload)
        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=authorize)
        async def upload(operation, ticket, prepared):
            await broker.wait_dispatched(ticket)
            assert len(payloads) == 1
            staged.append(prepared.read())
            payload = payloads[0]
            assert "path" not in payload["args"] and "paths" not in payload["args"]
            assert str(path) not in str(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            broker.settle_operation(principal=operation.principal, connector_sid=operation.connector_sid,
                load_generation_id=operation.load_generation_id, payload={**{key:payload[key] for key in keys},
                "ok":True,"result":{"lease_id":"lease-1","browser_id":"a0t1.load.tab","tab_handle":"a0t1.load.tab",
                "document_epoch":"1","ref":"ref-1","action_class":"external_side_effect"},"receipts":[],"artifacts":[]})
        runtime = ExtensionBrowserRuntime("context-1", "bridge-1", broker=broker, binding_factory=lambda:binding,
            policy_repository=policy, server_instance_id="server-1", target_origin_resolver=lambda *_:"https://example.com",
            action_challenge_ready=lambda _:True, prepare_upload=lambda **kwargs:prepare_upload(context,root=root,**kwargs),
            upload_sender=upload)
        result = await runtime.call("upload_file", "a0t1.load.tab", "ref-1", path=str(path), paths=[])
        assert result["action_class"] == "external_side_effect"
        assert staged == [b"user-provided content"]
    asyncio.run(scenario())
