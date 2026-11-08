"""First-party local operations must work without the former sibling runtime."""
import asyncio
import base64
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import zipfile

import pytest
from werkzeug.datastructures import FileStorage

from helpers import extension, files, job_loop, rfc, rfc_exchange, rfc_files, runtime
from helpers.file_browser import FileBrowser


@pytest.fixture(autouse=True)
def local_development(monkeypatch, tmp_path):
    def unavailable(*args, **kwargs):
        raise AssertionError("Sibling-container dispatch is unavailable")

    monkeypatch.setattr(runtime, "is_development", lambda: True)
    monkeypatch.setattr(runtime, "is_dockerized", lambda: False)
    monkeypatch.setattr(runtime, "call_development_function", unavailable)
    monkeypatch.setattr(runtime, "call_development_function_sync", unavailable)
    monkeypatch.setattr(rfc, "call_rfc", unavailable)
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    for name in ("max_file_bytes", "max_text_bytes", "max_extract_bytes", "max_archive_entries"):
        monkeypatch.setattr(FileBrowser, name, classmethod(lambda cls: 10000))


def test_sync_files_keep_contracts_and_original_errors(monkeypatch, tmp_path):
    monkeypatch.setattr(rfc_files, "get_abs_path", lambda *parts: str(tmp_path.joinpath(*parts)))
    def no_thread(*args, **kwargs):
        raise AssertionError("Synchronous files must not create dispatcher threads")
    monkeypatch.setattr(runtime.threading, "Thread", no_thread)
    assert rfc_files.make_directories("folder")
    assert rfc_files.write_file_binary("folder/binary", b"\x00\xffcontent")
    assert rfc_files.read_file_bin("folder/binary") == b"\x00\xffcontent"
    encoded = base64.b64encode(b"other").decode()
    assert rfc_files.write_file_base64("folder/other", encoded)
    assert rfc_files.read_file_base64("folder/other") == encoded
    assert rfc_files.path_exists("folder") and rfc_files.folder_exists("folder")
    assert rfc_files.file_exists("folder/binary")
    assert rfc_files.get_subdirectories(".", include="fold*", exclude="other") == ["folder"]
    assert len(rfc_files.list_directory("folder")) == 2
    assert rfc_files.find_file_in_dirs("binary", [str(tmp_path / "folder")]).endswith("folder/binary")
    assert rfc_files.move_file("folder/other", "folder/moved")
    with zipfile.ZipFile(io.BytesIO(rfc_files.read_directory_as_zip("folder"))) as archive:
        assert archive.read("binary") == b"\x00\xffcontent"
    archive_path = Path(rfc_files.zip_directory("folder"))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.read("folder/moved") == b"other"
    finally:
        archive_path.unlink()
    assert rfc_files.delete_file("folder/moved")
    with pytest.raises(FileNotFoundError, match="File not found"):
        rfc_files.read_file_bin("missing")
    with pytest.raises(FileNotFoundError, match="File not found"):
        rfc_files.delete_file("missing")
    assert rfc_files.delete_directory("folder")


@pytest.mark.parametrize("password", ["fixture-password", None])
def test_credentials_are_read_locally_without_crypto_roundtrip(monkeypatch, password):
    monkeypatch.setattr(rfc_exchange.dotenv, "get_dotenv_value", lambda key: password)
    def no_crypto(*args, **kwargs):
        raise AssertionError("Local credentials need no exchange encryption")
    monkeypatch.setattr(rfc_exchange.crypto, "_generate_private_key", no_crypto)
    assert asyncio.run(rfc_exchange.get_root_password()) == (password or "")


def test_async_credential_error_propagates_unchanged(monkeypatch):
    error = OSError("fixture credential read failed")
    def fail():
        raise error
    monkeypatch.setattr(rfc_exchange, "_get_root_password", fail)
    with pytest.raises(OSError) as caught:
        asyncio.run(rfc_exchange.get_root_password())
    assert caught.value is error


@pytest.mark.parametrize("pause_age, ticks", [(None, 1), (1, 0), (121, 1)])
def test_development_job_loop_runs_and_preserves_explicit_pause(monkeypatch, pause_age, ticks):
    monkeypatch.setattr(job_loop, "keep_running", pause_age is None)
    monkeypatch.setattr(job_loop, "pause_time", 0 if pause_age is None else 1000 - pause_age)
    monkeypatch.setattr(job_loop.time, "time", lambda: 1000)
    tick = AsyncMock()
    monkeypatch.setattr(job_loop, "scheduler_tick", tick)
    async def stop(_delay):
        raise asyncio.CancelledError
    monkeypatch.setattr(job_loop.asyncio, "sleep", stop)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(job_loop.run_loop())
    assert tick.await_count == ticks
    assert job_loop.keep_running is bool(ticks)


def test_scheduler_tick_keeps_extension_order_and_error_propagation(monkeypatch):
    calls = []
    async def tick():
        calls.append("tick")
    async def extensions(name):
        calls.append(name)
    monkeypatch.setattr(job_loop.TaskScheduler, "get", lambda: SimpleNamespace(tick=tick))
    monkeypatch.setattr(extension, "call_extensions_async", extensions)
    asyncio.run(job_loop.scheduler_tick())
    assert calls == ["tick", "job_loop"]
    failure = AsyncMock(side_effect=ValueError("tick failed"))
    monkeypatch.setattr(job_loop.TaskScheduler, "get", lambda: SimpleNamespace(tick=failure))
    with pytest.raises(ValueError, match="tick failed"):
        asyncio.run(job_loop.scheduler_tick())
    assert calls == ["tick", "job_loop"]


@pytest.mark.parametrize("project", [False, True])
@pytest.mark.parametrize("development", [False, True])
def test_code_execution_creates_local_workdir(monkeypatch, tmp_path, project, development):
    from plugins._code_execution.tools import code_execution_tool as code
    tool = code.CodeExecution.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(context=SimpleNamespace())
    monkeypatch.setattr(code.projects, "get_context_project_name", lambda _: "project" if project else None)
    monkeypatch.setattr(code.projects, "get_project_folder", lambda _: str(tmp_path / "project"))
    monkeypatch.setattr(runtime, "is_development", lambda: development)
    workdir = "/a0/usr/workdir" if development else str(tmp_path / "usr/workdir")
    monkeypatch.setattr(code.settings, "get_settings", lambda: {"workdir_path": workdir})
    target = tmp_path / ("project" if project else "usr/workdir")
    assert asyncio.run(tool.ensure_cwd()) == str(target)
    assert target.is_dir()


def test_promptinclude_scans_local_project_and_configured_workdir(monkeypatch, tmp_path):
    from plugins._promptinclude.extensions.python.system_prompt import _16_promptinclude as prompt
    workdir = tmp_path / "usr/workdir"
    workdir.mkdir(parents=True)
    (workdir / "rules.promptinclude.md").write_text("Use local files")
    class Agent:
        context = SimpleNamespace()
        def read_prompt(self, name, **kwargs):
            return kwargs.get("includes", kwargs.get("content", ""))
    monkeypatch.setattr(prompt.plugins, "get_plugin_config", lambda *a, **kw: {})
    monkeypatch.setattr(prompt.projects, "get_context_project_name", lambda _: None)
    monkeypatch.setattr(prompt, "get_settings_for_prompt", lambda: {"workdir_path": "/a0/usr/workdir"})
    system_prompt = []
    asyncio.run(prompt.PromptInclude(Agent()).execute(system_prompt=system_prompt))
    assert system_prompt == ["Use local files"]
    monkeypatch.setattr(prompt, "get_settings_for_prompt", lambda: {"workdir_path": ""})
    assert prompt._resolve_workdir(Agent()) == ""
    monkeypatch.setattr(prompt.projects, "get_context_project_name", lambda _: "project")
    monkeypatch.setattr(prompt.projects, "get_project_folder", lambda _: str(workdir))
    assert prompt._resolve_workdir(Agent()) == str(workdir)


@pytest.mark.parametrize("alias", [False, True])
def test_local_attachment_helpers_keep_bytes_and_missing_file_handling(tmp_path, alias):
    from plugins._email_integration.helpers import handler as email
    from plugins._whatsapp_integration.helpers import handler as whatsapp
    source = tmp_path / "attachment.bin"
    source.write_bytes(b"\x00\xffattachment")
    source_path = "/a0/attachment.bin" if alias else str(source)
    missing = str(tmp_path / "missing")
    assert asyncio.run(email._read_attachments_via_rfc([missing, source_path])) == [
        (source.name, source.read_bytes())
    ]
    staged = asyncio.run(whatsapp._read_attachments_to_host([missing, source_path]))
    assert len(staged) == 1 and Path(staged[0]).read_bytes() == source.read_bytes()
    incoming = asyncio.run(whatsapp._save_incoming_media([missing, str(source)]))
    assert incoming == staged and Path(incoming[0]).read_bytes() == source.read_bytes()


def test_development_file_api_roundtrip_and_mutation_hooks(monkeypatch, tmp_path):
    from api import (delete_work_dir_file, delete_work_dir_files, download_work_dir_files,
                     edit_work_dir_file, extract_work_dir_archive, file_info,
                     get_work_dir_files, rename_work_dir_file, upload_work_dir_files)
    hooks = AsyncMock()
    monkeypatch.setattr(extension, "call_extensions_async", hooks)
    async def run():
        request = SimpleNamespace(args={"path": str(tmp_path)}, method="GET")
        upload = FileStorage(stream=io.BytesIO(b"first"), filename="note.txt")
        assert await upload_work_dir_files.upload_files([upload], str(tmp_path)) == (["note.txt"], [])
        path = str(tmp_path / "note.txt")
        info = await file_info.FileInfoApi(None, None).process({"path": path}, request)
        assert info["is_file"] and info["size"] == 5
        assert "data" in await get_work_dir_files.GetWorkDirFiles(None, None).process({}, request)
        editor = edit_work_dir_file.EditWorkDirFile(None, None)
        request.method = "POST"
        assert await editor.process({"path": path, "content": "updated"}, request) == {"ok": True}
        request.method = "GET"
        request.args["path"] = path
        assert (await editor.process({}, request))["data"]["content"] == "updated"
        rename = rename_work_dir_file.RenameWorkDirFile(None, None)
        assert "data" in await rename.process({"path": path, "newName": "renamed.txt", "currentPath": str(tmp_path)}, request)
        path = str(tmp_path / "renamed.txt")
        download = download_work_dir_files.DownloadFiles(None, None)
        request.method = "POST"
        result = await download.process({"paths": [path], "currentPath": str(tmp_path)}, request)
        request.method = "GET"
        request.args = {"token": result["download_url"].split("token=")[1]}
        response = await download.process({}, request)
        try:
            assert b"".join(response.response) == b"updated"
        finally:
            response.close()
        archive = tmp_path / "bundle.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("inside.txt", "archive")
        extracted = await extract_work_dir_archive.ExtractWorkDirArchive(None, None).process(
            {"path": str(archive), "currentPath": str(tmp_path)}, request)
        assert (Path(extracted["extracted_path"]) / "inside.txt").read_text() == "archive"
        assert "data" in await delete_work_dir_file.DeleteWorkDirFile(None, None).process(
            {"path": path, "currentPath": str(tmp_path)}, request)
        result = await delete_work_dir_files.DeleteWorkDirFiles(None, None).process(
            {"paths": [str(archive)], "currentPath": str(tmp_path)}, request)
        assert result["deleted"] == [str(archive)]
        assert not Path(path).exists()
    asyncio.run(run())
    assert [call.kwargs["data"]["action"] for call in hooks.await_args_list] == [
        "edit", "rename", "extract", "delete", "bulk_delete"
    ]


@pytest.mark.parametrize("source", ["default", "configured", "project"])
def test_advertised_chat_paths_support_local_file_operations(monkeypatch, tmp_path, source):
    from api import chat_files_path_get, edit_work_dir_file, file_info, get_work_dir_files
    from helpers import projects, settings

    (tmp_path / "conf").mkdir()
    (tmp_path / "conf/workdir.gitignore").write_text("")
    monkeypatch.setattr(settings, "get_default_value", lambda _key, default: default)
    config = settings.get_default_settings()
    if source == "configured":
        config["workdir_path"] = "/a0/custom"
    monkeypatch.setattr(settings, "get_settings", lambda: config)
    monkeypatch.setattr(projects, "get_context_project_name", lambda _: "sample" if source == "project" else None)
    target = Path(projects.get_project_folder("sample")) if source == "project" else Path(files.fix_dev_path(config["workdir_path"]))
    target.mkdir(parents=True)
    (target / "note.txt").write_text("local contents")
    handler = chat_files_path_get.GetChatFilesPath(None, None)
    monkeypatch.setattr(handler, "use_context", lambda _: SimpleNamespace())

    async def run():
        advertised = (await handler.process({"ctxid": "fixture"}, None))["path"]
        assert advertised == str(target)
        listing = await get_work_dir_files.GetWorkDirFiles(None, None).process(
            {}, SimpleNamespace(args={"path": advertised}))
        assert "error" not in listing["data"]
        entry, = listing["data"]["entries"]
        assert entry["name"] == "note.txt"
        # Files emits root-relative entries; its consumers prepend the slash.
        path = "/" + entry["path"].lstrip("/")
        info = await file_info.get_file_info(path)
        assert info["is_file"] and info["abs_path"] == str(target / "note.txt")
        assert (await edit_work_dir_file.load_file(path))["content"] == "local contents"
        assert edit_work_dir_file.save_file(path, "edited locally")
        assert (target / "note.txt").read_text() == "edited locally"
    asyncio.run(run())


@pytest.mark.parametrize("path", ["", "$WORK_DIR", "/a0", "/a0/usr/workdir"])
def test_default_browser_and_saved_alias_open_local_directories(monkeypatch, tmp_path, path):
    from api import get_work_dir_files
    workdir = tmp_path / "usr/workdir"
    workdir.mkdir(parents=True)
    (workdir / "note.txt").write_text("local")
    result = asyncio.run(get_work_dir_files.GetWorkDirFiles(None, None).process(
        {}, SimpleNamespace(args={"path": path})))
    expected = workdir if path.endswith("/usr/workdir") else tmp_path
    assert "error" not in result["data"]
    assert result["data"]["current_path"] == str(expected)
    assert result["data"]["entries"][0]["name"] == ("note.txt" if expected == workdir else "usr")


def test_remote_browser_path_keeps_provider_routing(monkeypatch):
    from api import get_work_dir_files
    from helpers import file_connections
    path = "/@connections/ssh/0123456789abcdef0123456789abcdef/a0/usr/workdir"
    calls = []
    def listing(value):
        calls.append(value)
        return {"current_path": value, "entries": []}
    monkeypatch.setattr(file_connections, "listing", listing)
    assert asyncio.run(get_work_dir_files.get_files(path))["current_path"] == path
    assert calls == [path]


@pytest.mark.parametrize("project", [False, True])
def test_ssh_prepare_state_preserves_remote_cwd_without_local_creation(monkeypatch, tmp_path, project):
    from plugins._code_execution.tools import code_execution_tool as code
    data = {}
    tool = code.CodeExecution.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(context=SimpleNamespace(log=None), get_data=data.get, set_data=data.__setitem__)
    monkeypatch.setattr(code.projects, "get_context_project_name", lambda _: "project" if project else None)
    monkeypatch.setattr(code.projects, "get_project_folder", lambda _: str(tmp_path / "usr/projects/project"))
    monkeypatch.setattr(code.settings, "get_settings", lambda: {"workdir_path": "/a0/usr/workdir"})
    sessions = []
    class Session:
        connect = AsyncMock()
        close = AsyncMock()
        def __init__(self, logger, addr, port, user, password, *, cwd):
            self.cwd = cwd
            assert password == "fixture-ssh-password"
            sessions.append(self)
    monkeypatch.setattr(code, "SSHInteractiveSession", Session)
    def no_mkdir(*args):
        raise AssertionError("SSH setup must not create a local working directory")
    monkeypatch.setattr(code, "make_dir", no_mkdir)
    cfg = dict(ssh_enabled=True, ssh_addr="fixture", ssh_port=22, ssh_user="fixture", ssh_pass="fixture-ssh-password")
    state = asyncio.run(tool.prepare_state(cfg, session=0))
    assert state.shells[0].session is sessions[0]
    assert sessions[0].cwd == ("/a0/usr/projects/project" if project else "/a0/usr/workdir")
    Session.connect.assert_awaited_once()


def test_local_editor_aliases_share_read_write_patch_freshness(monkeypatch, tmp_path):
    from api import file_info
    from plugins._text_editor.tools import text_editor
    target = tmp_path / "usr/workdir/note.txt"
    target.parent.mkdir(parents=True)
    target.write_text("before\n")
    monkeypatch.setattr(text_editor.plugins, "get_plugin_config", lambda *a, **kw: {})
    monkeypatch.setattr(text_editor, "call_extensions_async", AsyncMock())
    tool = text_editor.TextEditor.__new__(text_editor.TextEditor)
    tool.agent = SimpleNamespace(data={}, context=SimpleNamespace(id="fixture"),
                                 read_prompt=lambda name, **kw: str(kw))
    alias = "/a0/usr/workdir/note.txt"
    async def run():
        assert (await file_info.get_file_info(alias))["abs_path"] == str(target)
        assert "before" in (await tool._read(path=alias)).message
        result = await tool._patch(path=str(target), edits=[{"from": 1, "to": 1, "content": "after\n"}])
        assert "error" not in result.message
        assert target.read_text() == "after\n"
        result = await tool._write(path=alias, content="written\n")
        assert "error" not in result.message
        await tool._patch(path=alias, old_text="written", new_text="replaced")
        assert target.read_text() == "replaced\n"
    asyncio.run(run())


def test_vision_load_materializes_development_alias_without_rfc(monkeypatch, tmp_path):
    from tools import vision_load
    source = tmp_path / "usr/workdir/image.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"fixture-image")
    monkeypatch.setattr(vision_load, "get_vision_model_config", lambda _: {})
    monkeypatch.setattr(vision_load, "get_chat_model_config", lambda _: {"max_embeds": 10})
    tool = vision_load.VisionLoad.__new__(vision_load.VisionLoad)
    tool.agent = SimpleNamespace(context=SimpleNamespace(id="fixture", get_data=lambda *_: None))
    alias = "/a0/usr/workdir/image.png"
    result = asyncio.run(tool.execute(paths=[alias]))
    assert "Loaded images (1)" in result.message
    stored, = tool.images_dict.values()
    assert Path(files.fix_dev_path(stored)).read_bytes() == source.read_bytes()
