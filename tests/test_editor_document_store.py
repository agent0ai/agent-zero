from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
import types
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import system_packages
from plugins._editor.helpers import (
    markdown_sessions as editor_markdown_sessions,
    open_files_context,
)
from plugins._editor.api.editor_session import EditorSession
from plugins._editor.helpers import document_store


@pytest.fixture(autouse=True)
def runtime_package_os(monkeypatch):
    monkeypatch.setattr(system_packages.platform, "freedesktop_os_release", lambda: {"ID": "debian"})


@pytest.fixture
def office_state(tmp_path, monkeypatch):
    from helpers import settings
    monkeypatch.setattr(settings, "get_settings", lambda: {"file_browser_max_text_size_mb": 10, "file_browser_max_transfer_size_mb": 100, "file_browser_max_extract_size_mb": 100, "file_browser_max_archive_entries": 1000})
    state = tmp_path / "state"
    backups = state / "backups"
    workdir = tmp_path / "workdir"
    documents = workdir / "documents"
    projects_parent = tmp_path / "projects"

    monkeypatch.setattr(document_store, "STATE_DIR", state)
    monkeypatch.setattr(document_store, "DB_PATH", state / "documents.sqlite3")
    monkeypatch.setattr(document_store, "BACKUP_DIR", backups)
    monkeypatch.setattr(document_store, "WORKDIR", workdir)
    monkeypatch.setattr(document_store, "DOCUMENTS_DIR", documents)
    settings_helpers = types.SimpleNamespace(get_settings=lambda: {"workdir_path": str(workdir)})
    project_helpers = types.SimpleNamespace(
        get_context_project_name=lambda context: None,
        get_project_folder=lambda name: str(projects_parent / name),
        get_projects_parent_folder=lambda: str(projects_parent),
    )
    monkeypatch.setattr(document_store, "_settings", lambda: settings_helpers)
    monkeypatch.setattr(document_store, "_projects", lambda: project_helpers)
    monkeypatch.setattr(
        editor_markdown_sessions,
        "_manager",
        editor_markdown_sessions.MarkdownSessionManager(),
        raising=False,
    )

    workdir.mkdir(parents=True, exist_ok=True)
    documents.mkdir(parents=True, exist_ok=True)
    projects_parent.mkdir(parents=True, exist_ok=True)
    document_store.ensure_dirs()
    return types.SimpleNamespace(
        state=state,
        backups=backups,
        workdir=workdir,
        documents=documents,
        projects_parent=projects_parent,
        project_helpers=project_helpers,
    )


def test_document_store_create_defaults_to_markdown(office_state):
    doc = document_store.create_document("document", "Research Note", content="A precise note.")

    assert doc["extension"] == "md"
    assert Path(doc["path"]).parent == office_state.workdir
    assert Path(doc["path"]).read_text(encoding="utf-8").startswith("# Research Note")


def test_text_files_register_as_editor_documents(office_state):
    path = office_state.workdir / "plain-note.txt"
    path.write_text("Plain text belongs in the Editor surface.\n", encoding="utf-8")

    doc = document_store.register_document(path)

    assert doc["extension"] == "txt"
    assert "txt" in document_store.EDITOR_TEXT_EXTENSIONS


def test_file_browser_can_register_runtime_root_markdown(office_state, monkeypatch):
    runtime_root = office_state.state.parent / "runtime-root"
    runtime_root.mkdir()
    path = runtime_root / "AGENTS.md"
    path.write_text("# Runtime Instructions\n", encoding="utf-8")
    monkeypatch.setattr(document_store.files, "get_base_dir", lambda: str(runtime_root))

    with pytest.raises(PermissionError, match="active project or workdir"):
        document_store.register_document(path)

    doc = document_store.register_document(path, allow_base_dir=True)

    assert doc["basename"] == "AGENTS.md"
    assert doc["path"] == str(path)


def test_editor_http_input_accepts_large_text_and_rejects_over_limit(office_state):
    path = office_state.workdir / "large.txt"
    text = "a" * (2 * 1024 * 1024)
    path.write_text(text, encoding="utf-8")
    handler = EditorSession(app=None, thread_lock=None)
    request = types.SimpleNamespace(headers={}, host_url="http://localhost/")
    opened = asyncio.run(handler.process({"action": "open", "path": str(path)}, request))
    assert opened["ok"] and opened["text"] == text
    payload = {"action": "input", "session_id": opened["session_id"], "text": text + "b"}
    assert asyncio.run(handler.process(payload, request))["ok"]
    with pytest.raises(ValueError, match="10 MiB"):
        asyncio.run(handler.process({**payload, "text": "a" * (10 * 1024 * 1024 + 1)}, request))
    assert asyncio.run(handler.process({"action": "save", "session_id": opened["session_id"]}, request))["ok"]
    assert path.read_text(encoding="utf-8") == text + "b"


def test_editor_file_browser_source_opens_runtime_root_markdown(office_state, monkeypatch):
    runtime_root = office_state.state.parent / "runtime-root"
    runtime_root.mkdir()
    path = runtime_root / "AGENTS.md"
    path.write_text("# Runtime Instructions\n", encoding="utf-8")
    monkeypatch.setattr(document_store.files, "get_base_dir", lambda: str(runtime_root))
    handler = EditorSession(app=None, thread_lock=None)
    request = types.SimpleNamespace(headers={}, host_url="http://localhost/")

    blocked = asyncio.run(handler.process({"action": "open", "path": str(path)}, request))
    opened = asyncio.run(handler.process({
        "action": "open",
        "path": str(path),
        "source": "file-browser",
    }, request))

    assert blocked["ok"] is False
    assert "active project or workdir" in blocked["error"]
    assert opened["ok"] is True
    assert opened["title"] == "AGENTS.md"
    assert opened["text"] == "# Runtime Instructions\n"


@pytest.mark.parametrize(
    ("kind", "title", "fmt", "expected_name"),
    [
        ("document", "real-chat-canvas-smoke.md", "md", "real-chat-canvas-smoke.md"),
    ],
)
def test_create_document_does_not_duplicate_matching_extension(office_state, kind, title, fmt, expected_name):
    doc = document_store.create_document(kind, title, fmt, content="Smoke")

    assert Path(doc["path"]).name == expected_name


def test_project_scoped_creation_uses_active_project_root(office_state, monkeypatch):
    project_root = office_state.projects_parent / "apollo"
    project_root.mkdir(parents=True, exist_ok=True)
    context = object()
    agent_module = types.SimpleNamespace(
        AgentContext=types.SimpleNamespace(get=staticmethod(lambda context_id: context))
    )

    monkeypatch.setitem(sys.modules, "agent", agent_module)
    monkeypatch.setattr(office_state.project_helpers, "get_context_project_name", lambda active_context: "apollo")
    monkeypatch.setattr(office_state.project_helpers, "get_project_folder", lambda name: str(project_root))

    markdown = document_store.create_document("document", "Project Note", "md", "Scoped.", context_id="ctx-project")

    assert Path(markdown["path"]).parent == project_root


def test_non_project_creation_uses_configured_workdir(office_state):
    markdown = document_store.create_document("document", "Workdir Note", content="Plain.")

    assert markdown["extension"] == "md"
    assert Path(markdown["path"]).parent == office_state.workdir


def test_editor_open_files_are_scoped_to_active_context(office_state):
    first = document_store.create_document("document", "First Editor Note", "md", "First private body.")
    second = document_store.create_document("document", "Second Editor Note", "md", "Second private body.")
    manager = editor_markdown_sessions.get_manager()

    first_session = manager.open(first, context_id="ctx-a")
    second_session = manager.open(second, context_id="ctx-b")
    manager.input(first_session["session_id"], text="Unsaved ctx-a text")
    reopened_first = manager.open(first, context_id="ctx-a")

    ctx_a_files = manager.list_open("ctx-a")
    ctx_b_files = manager.list_open("ctx-b")
    prompt_context = open_files_context.build_context("ctx-a")

    assert reopened_first["session_id"] == first_session["session_id"]
    assert reopened_first["text"] == "Unsaved ctx-a text"
    assert [item["file_id"] for item in ctx_a_files] == [first["file_id"]]
    assert [item["file_id"] for item in ctx_b_files] == [second["file_id"]]
    assert ctx_a_files[0]["dirty"] is True
    assert ctx_a_files[0]["active"] is True
    assert ctx_a_files[0]["open_sessions"] == 1
    assert "First Editor Note.md" in prompt_context
    assert "Second Editor Note.md" not in prompt_context
    assert "First private body" not in prompt_context
    assert "Unsaved ctx-a text" not in prompt_context


def test_markdown_save_tracks_version_history(office_state):
    doc = document_store.create_document("document", "Versioned", "md", "First")
    updated = document_store.write_markdown(doc["file_id"], "# Versioned\n\nSecond\n")
    history = document_store.version_history(doc["file_id"])

    assert updated["version"] == 2
    assert history
    assert Path(updated["path"]).read_text(encoding="utf-8").endswith("Second\n")


def test_document_path_update_preserves_file_id_after_rename(office_state):
    doc = document_store.create_document("document", "Rename Me", "md", "Body")
    original = Path(doc["path"])
    renamed = original.with_name("Renamed.md")
    original.rename(renamed)

    updated = document_store.update_document_path(doc["file_id"], renamed)

    assert updated["file_id"] == doc["file_id"]
    assert updated["basename"] == "Renamed.md"
    assert updated["path"] == str(renamed)
    assert document_store.get_document(doc["file_id"])["path"] == str(renamed)


def test_document_rename_materializes_missing_markdown_with_editor_text(office_state):
    doc = document_store.create_document("document", "Unsaved Draft", "md", "Seed")
    original = Path(doc["path"])
    original.unlink()
    renamed = original.with_name("Renamed Draft.md")

    updated = document_store.rename_document(
        doc["file_id"],
        renamed,
        content="# Renamed Draft\n\nCanvas text",
    )

    assert updated["file_id"] == doc["file_id"]
    assert updated["basename"] == "Renamed Draft.md"
    assert updated["path"] == str(renamed)
    assert renamed.read_text(encoding="utf-8") == "# Renamed Draft\n\nCanvas text"


def test_document_rename_saves_dirty_markdown_and_removes_original(office_state):
    doc = document_store.create_document("document", "Dirty Rename", "md", "Old")
    original = Path(doc["path"])
    renamed = original.with_name("Clean Rename.md")

    updated = document_store.rename_document(
        doc["file_id"],
        renamed,
        content="# Clean Rename\n\nFresh text",
    )

    assert updated["version"] == 2
    assert not original.exists()
    assert renamed.read_text(encoding="utf-8") == "# Clean Rename\n\nFresh text"


def test_text_session_save_as_creates_new_file_without_mutating_original(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Original Note", "md", "# Original Note\n")
    original = Path(doc["path"])
    session = manager.open(doc, context_id="ctx-a")
    target = office_state.workdir / "notes" / "Saved Copy.txt"

    result = manager.save_as(
        session["session_id"],
        str(target),
        text="Saved Copy\n\nExact body\n",
    )

    saved_session = manager._sessions[session["session_id"]]
    assert result["ok"] is True
    assert result["document"]["file_id"] != doc["file_id"]
    assert result["previous_file_id"] == doc["file_id"]
    assert saved_session.file_id == result["document"]["file_id"]
    assert saved_session.path == str(target)
    assert saved_session.extension == "txt"
    assert saved_session.dirty is False
    assert original.read_text(encoding="utf-8") == "# Original Note"
    assert target.read_text(encoding="utf-8") == "Saved Copy\n\nExact body\n"


def test_editor_session_opens_and_saves_txt_documents(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Plain Note", "txt", "First line")
    session = manager.open(doc, context_id="ctx-a")

    assert session["extension"] == "txt"
    assert session["text"] == "First line"

    result = manager.save(session["session_id"], text="Second line\n")

    assert result["ok"] is True
    assert result["document"]["extension"] == "txt"
    assert Path(result["document"]["path"]).read_text(encoding="utf-8") == "Second line\n"


def test_refresh_open_markdown_session_reloads_external_file_edits(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "External Refresh", "md", "First")
    session = manager.open(doc, context_id="ctx-a")

    Path(doc["path"]).write_text("# External Refresh\n\nSecond\n", encoding="utf-8")
    refreshed = manager.open(doc, context_id="ctx-a", refresh=True)

    assert refreshed["session_id"] == session["session_id"]
    assert refreshed["text"] == "# External Refresh\n\nSecond\n"
    assert manager._sessions[session["session_id"]].dirty is False


def test_refresh_open_markdown_session_preserves_dirty_editor_text(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Dirty External Refresh", "md", "First")
    session = manager.open(doc, context_id="ctx-a")
    manager.input(session["session_id"], text="Unsaved editor text")

    Path(doc["path"]).write_text("External disk text\n", encoding="utf-8")
    refreshed = manager.open(doc, context_id="ctx-a", refresh=True)

    assert refreshed["text"] == "Unsaved editor text"
    assert manager._sessions[session["session_id"]].dirty is True


def test_external_text_editor_mutation_refreshes_clean_open_markdown_session(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Synced External Edit", "md", "First")
    session = manager.open(doc, context_id="ctx-a")

    Path(doc["path"]).write_text("# Synced External Edit\n\nSecond\n", encoding="utf-8")
    result = manager.sync_external_file_mutations([doc["path"]])

    assert result["matched"] == 1
    assert manager._sessions[session["session_id"]].text == "# Synced External Edit\n\nSecond\n"
    assert manager._sessions[session["session_id"]].dirty is False
    assert manager._sessions[session["session_id"]].external_modified is False


def test_external_text_editor_mutation_marks_dirty_markdown_session_pending(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Dirty Synced External Edit", "md", "First")
    session = manager.open(doc, context_id="ctx-a")
    manager.input(session["session_id"], text="Unsaved editor text")

    Path(doc["path"]).write_text("External disk text\n", encoding="utf-8")
    result = manager.sync_external_file_mutations([doc["path"]])

    dirty_session = manager._sessions[session["session_id"]]
    assert result["matched"] == 1
    assert dirty_session.text == "Unsaved editor text"
    assert dirty_session.dirty is True
    assert dirty_session.external_modified is True


def test_markdown_editor_save_rejects_stale_canvas_overwrite(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = document_store.create_document("document", "Stale Save Guard", "md", "First")
    session = manager.open(doc, context_id="ctx-a")

    Path(doc["path"]).write_text("# Stale Save Guard\n\nExternal newer text\n", encoding="utf-8")
    result = manager.save(session["session_id"], text="# Stale Save Guard\n\nOlder canvas text\n")

    assert result["ok"] is False
    assert result["code"] == "external_change_conflict"
    assert "External newer text" in Path(doc["path"]).read_text(encoding="utf-8")
    assert "Older canvas text" not in Path(doc["path"]).read_text(encoding="utf-8")


def test_markdown_session_rejects_office_binaries(office_state):
    manager = editor_markdown_sessions.MarkdownSessionManager()
    doc = {"extension": "odt"}

    with pytest.raises(ValueError, match="Open .odt files in the Desktop"):
        manager.open(doc)


def test_desktop_gateway_patches_xpra_menu_script():
    source = (PROJECT_ROOT / "helpers" / "virtual_desktop_routes.py").read_text(encoding="utf-8")

    assert "XPRA_MENU_CUSTOM_PATCH" in source
    assert 'upstream_path.endswith("/js/MenuCustom.js")' in source
    assert "window.noWindowList" in source
    assert "__a0SafeWindowList" in source
    assert "XPRA_WINDOW_OFFSET_WARNING_PATCH" in source
    assert "XPRA_WINDOW_SCRIPT_PATCH" in source
    assert "a0_desktop_patch=20260506" in source
    assert 'upstream_path.endswith("/index.html")' in source
    assert 'upstream_path.endswith("/js/Window.js")' in source
    assert "window does not fit in canvas, offsets:" in source


@pytest.mark.parametrize("name", ["probe.jsonl", "module.py", "settings.yaml", "page.html", "Dockerfile", ".env", "custom.unknown"])
def test_editor_arbitrary_text_file_lifecycle(office_state, name):
    path = office_state.workdir / name
    original = b'first line\r\nsecond line\r\n'
    path.write_bytes(original)
    manager = editor_markdown_sessions.get_manager()
    doc = document_store.register_document(path)
    session = manager.open(doc)
    assert session["text"].encode() == original
    manager.input(session["session_id"], text="local edit\n")
    path.write_text("external edit\n")
    assert manager.save(session["session_id"])["code"] == "external_change_conflict"
    copy = path.with_name("copy-" + name)
    result = manager.save_as(session["session_id"], str(copy), text="saved copy\n")
    assert path.read_text() == "external edit\n"
    assert copy.read_text() == "saved copy\n"
    assert result["document"]["extension"] == copy.suffix.lstrip(".")
    with pytest.raises(FileExistsError):
        manager.save_as(session["session_id"], str(copy))
    renamed = copy.with_name("renamed-" + name)
    updated = document_store.rename_document(result["document"]["file_id"], renamed, content="renamed\n")
    manager.renamed(updated["file_id"], updated, text="renamed\n")
    assert not copy.exists()
    assert renamed.read_text() == "renamed\n"
    assert manager.save(session["session_id"], text="final\n")["ok"]
    assert renamed.read_text() == "final\n"
    manager.close(session["session_id"])


@pytest.mark.parametrize("content, message", [(b'a\x00b', "Binary"), (b'\xff\xfe', "UTF-8"), (b'x' * (10 * 1024 * 1024 + 1), "10 MiB")], ids=["binary", "encoding", "size"])
def test_editor_rejects_binary_invalid_encoding_and_large_files(office_state, content, message):
    path = office_state.workdir / "unsafe.jsonl"
    path.write_bytes(content)
    with pytest.raises(ValueError, match=message):
        document_store.register_document(path)
    assert path.read_bytes() == content


def test_editor_named_create_and_save_as_match_file_browser_scope(office_state, tmp_path):
    path = tmp_path / "outside-workdir.py"
    handler = EditorSession(app=None, thread_lock=None)
    request = types.SimpleNamespace(headers={}, host_url="http://localhost/")
    payload = {"action": "create", "path": str(path), "source": "file-browser", "content": "print(1)\n"}
    opened = asyncio.run(handler.process(payload, request))
    assert opened["ok"]
    assert opened["text"] == "print(1)\n"
    assert not asyncio.run(handler.process(payload, request))["ok"]
    assert path.read_text() == "print(1)\n"
    target = tmp_path / "Dockerfile"
    result = asyncio.run(handler.process({"action": "save_as", "session_id": opened["session_id"], "path": str(target), "text": "FROM scratch\n"}, request))
    assert result["ok"]
    assert result["document"]["extension"] == ""
    assert target.read_text() == "FROM scratch\n"
    with pytest.raises(PermissionError):
        document_store.register_document(target)


@pytest.mark.parametrize("mode", [0o755, 0o600])
def test_editor_preserves_file_permissions_and_private_backups(office_state, mode):
    import stat

    path = office_state.workdir / "script.sh"
    path.write_text("echo original\n")
    path.chmod(mode)
    original = path.stat()
    office_state.backups.chmod(0o775)
    manager = editor_markdown_sessions.get_manager()
    session = manager.open(document_store.register_document(path))
    assert manager.save(session["session_id"], text="echo saved\n")["ok"]
    copy = path.with_name("copy.sh")
    result = manager.save_as(session["session_id"], str(copy))
    renamed = path.with_name("renamed.sh")
    document_store.rename_document(result["document"]["file_id"], renamed, content="echo renamed\n")
    for target in (path, renamed):
        saved = target.stat()
        assert stat.S_IMODE(saved.st_mode) == mode
        assert (saved.st_uid, saved.st_gid) == (original.st_uid, original.st_gid)
    assert stat.S_IMODE(office_state.backups.stat().st_mode) == 0o700
    assert list(office_state.backups.iterdir())
    assert all(stat.S_IMODE(backup.stat().st_mode) == 0o600 for backup in office_state.backups.iterdir())


def test_editor_atomic_metadata_failure_keeps_original(office_state, monkeypatch):
    path = office_state.workdir / "private.sh"
    path.write_text("original\n")
    path.chmod(0o600)
    doc = document_store.register_document(path)

    def fail_chmod(*_args):
        raise PermissionError("metadata update failed")

    monkeypatch.setattr(document_store.os, "fchmod", fail_chmod)
    with pytest.raises(PermissionError, match="metadata update failed"):
        document_store.write_text_document(doc["file_id"], "replacement\n")
    assert path.read_text() == "original\n"
    assert not list(path.parent.glob(".private.sh.*.tmp"))


def test_legacy_state_copy_preserves_source_and_current_state(tmp_path, monkeypatch):
    legacy = tmp_path / 'legacy'
    legacy.mkdir()
    (legacy / 'documents.sqlite3').write_bytes(b'existing history')
    (legacy / 'backups').mkdir()
    (legacy / 'backups/version').write_bytes(b'original text')
    target = tmp_path / 'current'
    monkeypatch.setattr(document_store, 'LEGACY_STATE_DIRS', [legacy])
    monkeypatch.setattr(document_store, 'STATE_DIR', target)
    monkeypatch.setattr(document_store, 'BACKUP_DIR', target / 'backups')
    document_store.ensure_dirs()
    assert (target / 'documents.sqlite3').read_bytes() == b'existing history'
    assert (target / 'backups/version').read_bytes() == b'original text'
    assert (legacy / 'documents.sqlite3').exists()
    (target / 'documents.sqlite3').write_bytes(b'new history')
    document_store.ensure_dirs()
    assert (target / 'documents.sqlite3').read_bytes() == b'new history'


def test_failed_legacy_copy_does_not_publish_partial_state(tmp_path, monkeypatch):
    legacy = tmp_path / 'legacy'
    legacy.mkdir()
    target = tmp_path / 'current'
    monkeypatch.setattr(document_store, 'LEGACY_STATE_DIRS', [legacy])
    monkeypatch.setattr(document_store, 'STATE_DIR', target)
    def fail(*args, **kwargs):
        raise OSError('fixture copy failure')
    monkeypatch.setattr(document_store.shutil, 'copytree', fail)
    with pytest.raises(OSError):
        document_store.ensure_dirs()
    assert not target.exists()
    assert legacy.exists()
