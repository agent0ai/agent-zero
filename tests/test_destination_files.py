from types import SimpleNamespace

import pytest

from helpers import destination_files
from plugins._a0_connector.helpers import file_browser, ws_runtime
from plugins._code_execution.helpers.destinations import ExecutionDestination
from plugins._text_editor.tools import text_editor


@pytest.mark.asyncio
async def test_host_binary_files_use_the_connected_folder_and_independent_transfer_grants(monkeypatch):
    agent = SimpleNamespace(context=SimpleNamespace(id="chat"))
    sid = "file-destination-connector"
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, "chat")
    ws_runtime.store_sid_remote_file_metadata(
        sid, {"enabled": True, "root_path": "/chosen", "file_browser": 1, "write_enabled": False},
    )
    try:
        def read(backend, path, stream, limit):
            assert backend.item["_sid"] == sid
            assert (path, limit) == ("repo/file", 10)
            stream.write(b"\x00\xff")

        monkeypatch.setattr(file_browser.HostFiles, "read", read)
        assert await destination_files.read(agent, "host", "/chosen/repo/file", limit=10) == b"\x00\xff"
        with pytest.raises(PermissionError, match="outside"):
            await destination_files.read(agent, "host", "/other/file", limit=10)
        with pytest.raises(PermissionError, match="transfer access"):
            await destination_files.write(agent, "host", "repo/file", b"X", limit=10)
    finally:
        ws_runtime.unregister_sid(sid)


@pytest.mark.asyncio
async def test_editor_sandbox_patch_is_scoped_and_rejects_stale_content(monkeypatch):
    contents = {"one": b"Original\n", "two": b"Another\n"}

    async def resolve(_agent, name):
        return ExecutionDestination(name, "sandbox", name, "", target=name)

    async def read(_agent, name, path, *, limit):
        assert path == "/workspace/note.txt"
        return contents[name]

    async def write(_agent, name, path, content, *, limit, expected=None):
        import hashlib

        assert path == "/workspace/note.txt"
        assert expected == hashlib.sha256(contents[name]).hexdigest()
        contents[name] = content
        return hashlib.sha256(content).hexdigest()

    async def no_extensions(*args, **kwargs):
        pass

    agent = SimpleNamespace(
        data={},
        read_prompt=lambda name, **args: f"{name} {args}",
    )
    monkeypatch.setattr(destination_files, "resolve", resolve)
    monkeypatch.setattr(destination_files, "read", read)
    monkeypatch.setattr(destination_files, "write", write)
    monkeypatch.setattr(text_editor, "call_extensions_async", no_extensions)
    monkeypatch.setattr(text_editor, "_get_config", lambda _: {
        "max_line_tokens": 500, "default_line_count": 100, "max_total_read_tokens": 4000,
    })

    async def edit(action, destination, **kwargs):
        args = {"action": action, "destination": destination, "path": "/workspace/note.txt", **kwargs}
        return await text_editor.TextEditor(agent, "text_editor", None, args, "", None).execute(**args)

    assert "Original" in (await edit("read", "one")).message
    edits = [{"from": 1, "to": 1, "content": "Changed"}]
    assert "patch_need_read" in (await edit("patch", "two", edits=edits)).message
    assert "patched" in (await edit("patch", "one", edits=edits)).message
    assert contents["one"] == b"Changed\n"
    contents["one"] = b"External change\n"
    assert "patch_stale_read" in (await edit("patch", "one", edits=edits)).message
    assert contents["one"] == b"External change\n"


@pytest.mark.asyncio
async def test_browser_prepares_upload_from_the_selected_filesystem(monkeypatch):
    import base64

    from plugins._browser.tools.browser import Browser

    async def read(agent, destination, path, *, limit):
        assert (destination, path) == ("analysis", "/workspace/artifact.png")
        return b"\x00\xff"

    monkeypatch.setattr(destination_files, "read", read)
    browser = Browser(SimpleNamespace(), "browser", None, {}, "", None)
    prepared = await browser._prepare_upload(object(), "analysis", "/workspace/artifact.png", None)
    assert prepared["paths"] == ["/workspace/artifact.png"]
    assert prepared["files"] == [{
        "name": "artifact.png", "mimeType": "image/png", "buffer": base64.b64encode(b"\x00\xff").decode(),
    }]


@pytest.mark.asyncio
async def test_destination_documents_index_the_selected_bytes(monkeypatch):
    from plugins._document_query.helpers import document_query

    async def read(agent, destination, path, *, limit):
        assert (destination, path, limit) == ("host", "notes.md", 128)
        return b"remote content"

    async def intervene():
        pass

    async def exists(uri):
        return False

    async def parse(document, timeout):
        assert document.local_path is None
        assert document.content == b"remote content"
        return document.text()

    monkeypatch.setattr(destination_files, "read", read)
    helper = object.__new__(document_query.DocumentQueryHelper)
    helper.agent = SimpleNamespace(context=SimpleNamespace(id="chat"), handle_intervention=intervene)
    helper.config = {"max_remote_bytes": 128}
    helper.destination = "host"
    helper._destination_uris = {}
    helper.progress_callback = lambda _message: None
    helper.store = SimpleNamespace(document_exists=exists, normalize_uri=lambda value: value)
    helper._parse_document = parse

    assert await helper.document_get_content("notes.md") == "remote content"
    assert helper._destination_uris["notes.md"].startswith("destination-file://chat/host/")
