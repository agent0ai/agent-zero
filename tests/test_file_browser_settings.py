import asyncio

import pytest

from api.file_browser_settings import FileBrowserSettings
from helpers import settings
from helpers.file_browser import FileBrowser


def test_editor_limit_defaults_to_ten_mib():
    assert settings.get_default_settings()["file_browser_max_text_size_mb"] == 10
    assert settings.get_default_settings()["file_browser_max_transfer_size_mb"] == 100


def test_limit_updates_only_its_setting_and_shared_validation(monkeypatch):
    saved = {"file_browser_max_text_size_mb": 10, "file_browser_max_transfer_size_mb": 100, "unrelated": "keep"}
    def update(delta, apply):
        assert apply is False
        assert set(delta) == {"file_browser_max_text_size_mb"}
        saved.update(delta)
    monkeypatch.setattr(settings, "set_settings_delta", update)
    monkeypatch.setattr(settings, "get_settings", lambda: saved)
    handler = FileBrowserSettings(None, None)
    result = asyncio.run(handler.process({"max_text_size_mb": 2}, None))
    assert result["limits"]["max_text_bytes"] == 2 * 1024 * 1024
    assert saved["unrelated"] == "keep"
    assert len(FileBrowser.text_bytes("a" * (2 * 1024 * 1024))) == 2 * 1024 * 1024
    with pytest.raises(ValueError, match="2 MiB"):
        FileBrowser.text_bytes("a" * (2 * 1024 * 1024 + 1))
    for value in (0, 101, 1.5, "10", True, None):
        assert not asyncio.run(handler.process({"max_text_size_mb": value}, None))["ok"]
    assert saved["file_browser_max_text_size_mb"] == 2
    assert handler.requires_auth() and handler.requires_csrf()


def test_transfer_setting_has_no_artificial_ceiling(monkeypatch):
    saved = {"file_browser_max_text_size_mb": 10, "file_browser_max_transfer_size_mb": 100}
    monkeypatch.setattr(settings, "get_settings", lambda: saved)
    monkeypatch.setattr(settings, "set_settings_delta", lambda delta, apply: saved.update(delta))
    handler = FileBrowserSettings(None, None)
    result = asyncio.run(handler.process({"max_transfer_size_mb": 10240}, None))
    assert result["ok"] and result["limits"]["max_file_bytes"] == 10240 * 1024 * 1024
    assert result["limits"]["max_text_bytes"] == 10 * 1024 * 1024
    for value in (0, -1, 1.5, "100", True, None):
        assert not asyncio.run(handler.process({"max_transfer_size_mb": value}, None))["ok"]


def test_local_transfer_limit_rejects_before_overwrite(tmp_path, monkeypatch):
    import base64
    import io
    from werkzeug.datastructures import FileStorage
    from api.download_work_dir_file import stream_file_download
    from api.upload_work_dir_files import UploadWorkDirFiles
    from types import SimpleNamespace
    from werkzeug.datastructures import MultiDict

    monkeypatch.setattr(FileBrowser, "max_file_bytes", classmethod(lambda cls: 4))
    browser = FileBrowser()
    target = tmp_path / "backup.zip"
    target.write_bytes(b"keep")
    uploaded = FileStorage(stream=io.BytesIO(b"large"), filename=target.name)
    request = SimpleNamespace(files=MultiDict([("files[]", uploaded)]), form={"path": str(tmp_path)})
    response = asyncio.run(UploadWorkDirFiles(None, None).process({}, request))
    assert response.status_code == 413
    assert "transfer limit" in response.get_json()["error"]
    assert browser.save_files([uploaded], str(tmp_path)) == ([], [target.name])
    assert not browser.save_file_b64(str(tmp_path), target.name, base64.b64encode(b"large").decode())
    assert target.read_bytes() == b"keep"
    assert stream_file_download(io.BytesIO(b"large"), "file", max_bytes=4).status_code == 413
    assert stream_file_download(io.BytesIO(b"keep"), "file", max_bytes=4).status_code == 200
    assert stream_file_download(io.BytesIO(b"large"), "file").status_code == 200
