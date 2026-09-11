"""Provider boundaries without network access or real connection state."""
import contextlib
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from helpers import file_connections as service
from helpers.file_browser import FileBrowser


def test_remote_transfers_and_editing_have_independent_limits(storage, monkeypatch):
    remote, item, _, _ = storage
    monkeypatch.setattr(FileBrowser, "max_file_bytes", classmethod(lambda cls: 4))
    path = service.path_for(item, "text.py")
    service.write(path, b"1234")
    assert service.read(path)[0] == b"1234"
    with pytest.raises(ValueError):
        service.write(path, b"12345")
    remote["text.py"] = b"12345"
    with pytest.raises(ValueError):
        service.read(path)
    with pytest.raises(ValueError):
        service.archive([path])
    session = service.editor("open", {"path": path})
    assert service.editor("save", {"session_id": session["session_id"], "text": "123456"})["ok"]
    assert remote["text.py"] == b"123456"


def test_editors_inherit_file_browser_text_rules(storage, monkeypatch, tmp_path):
    from plugins._office.helpers import document_store
    remote, item, _, _ = storage
    monkeypatch.setattr(FileBrowser, "max_text_bytes", classmethod(lambda cls: 4))
    assert document_store.editor_text_bytes("éé") == "éé".encode()
    path = tmp_path / "local.py"
    path.write_text("éé", encoding="utf-8")
    assert document_store.read_text_for_editor({"path": str(path), "extension": "py"}) == "éé"
    remote["remote.py"] = "éé".encode()
    opened = service.editor("open", {"path": service.path_for(item, "remote.py")})
    assert opened["text"] == "éé"
    for text in ("ééx", "a\0", "\x01\x02"):
        with pytest.raises(ValueError):
            document_store.editor_text_bytes(text)
        with pytest.raises(ValueError):
            service.editor("save", {"session_id": opened["session_id"], "text": text})
    assert remote["remote.py"] == "éé".encode()
    monkeypatch.setattr(FileBrowser, "max_text_bytes", classmethod(lambda cls: 6))
    assert document_store.editor_text_bytes("ééé") == "ééé".encode()
    assert service.editor("save", {"session_id": opened["session_id"], "text": "ééé"})["ok"]


@pytest.fixture
def storage(tmp_path, monkeypatch):
    from helpers import settings
    monkeypatch.setattr(settings, "get_settings", lambda: {"file_browser_max_text_size_mb": 10, "file_browser_max_transfer_size_mb": 100, "file_browser_max_extract_size_mb": 100, "file_browser_max_archive_entries": 1000})
    remote = {}
    class FS:
        def list(self, path):
            return [dict(name=k, is_dir=False, size=len(v), modified=0) for k,v in remote.items()]
        def stat(self, path):
            return dict(is_dir=not path, size=len(remote.get(path, b"")))
        def read(self, path, destination, limit):
            from helpers.file_transfers import copy_stream
            return copy_stream(io.BytesIO(remote[path]), destination, limit)["sha256"]
        def write(self, path, source, expected=None):
            content = source.read()
            if expected is None and path in remote:
                raise ValueError("exists")
            if expected is not None and hashlib.sha256(remote[path]).hexdigest() != expected:
                raise ValueError("changed")
            remote[path] = content
            return hashlib.sha256(content).hexdigest()
        def rename(self, path, target):
            remote[target] = remote.pop(path)
        def remove(self, path, directory=False):
            del remote[path]
    class Provider:
        id = "test"
        plugin_name = "file_browser_test"
        title = "Test storage"
        fields = [{"name":"password", "secret":True}]
        def validate(self, config):
            return config
        @contextlib.contextmanager
        def open(self, config, directory):
            yield FS()
    enabled = {"test":Provider()}
    monkeypatch.setattr(service, "providers", lambda: enabled)
    monkeypatch.setattr(service, "data_dir", lambda provider: tmp_path)
    monkeypatch.setattr(service, "SESSIONS", {})
    item = service.save_connection(dict(provider="test", name="Test", password="private-test-only", permissions={p:True for p in service.PERMISSIONS}))
    return remote, item, enabled, tmp_path


def test_secret_roundtrip_and_private_storage(storage):
    _, item, _, path = storage
    assert "password" not in item
    assert item["savedSecrets"] == {"password":True}
    assert (path / "connections.json").stat().st_mode & 0o777 == 0o600
    service.save_connection(item)
    assert service.get_connection("test", item["id"])[1]["password"] == "private-test-only"
    assert "private-test-only" not in json.dumps(service.listing_config())


def test_editor_permissions_conflicts_and_plugin_disable(storage):
    remote, item, enabled, _ = storage
    root = service.path_for(item)
    service.write(root + "/code.py", b"print(1)")
    doc = service.editor("open", {"path":root + "/code.py"})
    service.editor("save", {"session_id":doc["session_id"], "text":"print(2)"})
    assert remote["code.py"] == b"print(2)"
    remote["code.py"] = b"external edit"
    with pytest.raises(ValueError, match="changed"):
        service.editor("save", {"session_id":doc["session_id"], "text":"stale"})
    assert remote["code.py"] == b"external edit"
    with zipfile.ZipFile(service.archive([root + "/code.py"])) as archive:
        assert archive.read("code.py") == b"external edit"
    item["permissions"]["delete"] = False
    service.save_connection(item)
    with pytest.raises(PermissionError):
        service.mutate("delete", root + "/code.py")
    enabled.clear()
    with pytest.raises(ValueError, match="not installed or enabled"):
        service.read(root + "/code.py")


def test_paths_and_unsupported_actions(storage):
    _, item, enabled, _ = storage
    root = service.path_for(item)
    for path in ("/@connections/test", root + "/../outside", root + "/a\\b", root + "/a\0b"):
        with pytest.raises(ValueError):
            service.split(path)
    enabled["test"].permissions = ("browse", "download")
    saved = service.save_connection(item)
    assert not saved["permissions"]["upload"]
    with pytest.raises(PermissionError):
        service.write(root + "/new", b"x")


def test_saved_connections_use_utf8_json_without_prototype_migration(tmp_path, monkeypatch):
    class Provider:
        @property
        def legacy_connections(self):
            raise AssertionError("Prototype connection state must not be consulted")

    monkeypatch.setattr(service, "data_dir", lambda provider: tmp_path)
    assert service._load(Provider()) == {}
    saved = {"example": {"name": "Archivio città"}}
    (tmp_path / "connections.json").write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    assert service._load(Provider()) == saved
