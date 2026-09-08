import asyncio
import io
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from helpers import file_transfers as transfers
from helpers.file_browser import FileBrowser
from helpers.file_archives import create_selected_zip, extract_archive


def test_atomic_write_failure_preserves_bytes_and_mode(tmp_path):
    destination = tmp_path / "script"
    destination.write_bytes(b"keep"); destination.chmod(0o751)
    class Broken:
        calls = 0
        def read(self, size):
            self.calls += 1
            if self.calls == 1: return b"partial"
            raise OSError("interrupted")
    with pytest.raises(OSError):
        transfers.write_stream_atomic(Broken(), destination)
    assert destination.read_bytes() == b"keep"
    assert destination.stat().st_mode & 0o777 == 0o751
    assert not list(tmp_path.glob(".partial-*"))
    transfers.write_stream_atomic(io.BytesIO(b"updated"), destination)
    assert destination.read_bytes() == b"updated"
    assert destination.stat().st_mode & 0o777 == 0o751


def test_atomic_write_rejects_concurrent_replacement(tmp_path):
    destination = tmp_path / "file"
    destination.write_bytes(b"old")
    class Changed(io.BytesIO):
        def read(self, size):
            result = super().read(size)
            if result:
                destination.unlink(); destination.write_bytes(b"external change")
            return result
    with pytest.raises(ValueError, match="changed"):
        transfers.write_stream_atomic(Changed(b"new"), destination)
    assert destination.read_bytes() == b"external change"
    assert not list(tmp_path.glob(".partial-*"))


def test_download_holds_original_descriptor_and_cleans_temp(tmp_path):
    source = tmp_path / "snapshot"
    source.write_bytes(b"original")
    response = transfers.stream_file_download(source, "snapshot", delete_after=True)
    assert b"".join(response.response) == b"original"
    response.close()
    assert not source.exists()
    source.write_bytes(b"original")
    response = transfers.stream_file_download(source, "snapshot")
    source.unlink(); source.write_bytes(b"replacement")
    assert b"".join(response.response) == b"original"
    response.close()


def test_download_ticket_is_single_use_and_rechecks_permission():
    body = io.BytesIO(b"file")
    response = transfers.stream_file_download(body, "file")
    token = transfers.prepare_download_response(response)
    assert transfers.take_download_response(token) is response
    with pytest.raises(FileNotFoundError): transfers.take_download_response(token)
    response.close()
    body = io.BytesIO(b"file")
    def revoked(): raise PermissionError("revoked")
    token = transfers.prepare_download_response(transfers.stream_file_download(body, "file"), revoked)
    with pytest.raises(PermissionError): transfers.take_download_response(token)
    assert body.closed
    assert token not in transfers._DOWNLOADS


def test_rejected_zip_creation_deletes_temporary_output(tmp_path, monkeypatch):
    import tempfile
    source = tmp_path / "large"
    source.write_bytes(b"a" * 1000)
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    with pytest.raises(transfers.FileLimitExceeded):
        create_selected_zip([str(source)], max_bytes=10)
    assert list(tmp_path.iterdir()) == [source]


def test_extraction_limits_and_duplicate_paths_cleanup(tmp_path, monkeypatch):
    from helpers import files
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(FileBrowser, "max_extract_bytes", classmethod(lambda cls: 10))
    monkeypatch.setattr(FileBrowser, "max_archive_entries", classmethod(lambda cls: 1))
    source = tmp_path / "archive.zip"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("large", b"a" * 1000)
    with pytest.raises(transfers.FileLimitExceeded): extract_archive(str(source))
    assert not (tmp_path / "archive").exists()
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("first", b"a"); archive.writestr("second", b"b")
    with pytest.raises(ValueError, match="entry limit"): extract_archive(str(source))
    assert not (tmp_path / "archive").exists()
    monkeypatch.setattr(FileBrowser, "max_archive_entries", classmethod(lambda cls: 10))
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("same", b"a")
        with pytest.warns(UserWarning): archive.writestr("same", b"b")
    with pytest.raises(ValueError, match="duplicate"): extract_archive(str(source))
    assert not (tmp_path / "archive").exists()


def test_seven_zip_streams_members_without_direct_extraction(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from helpers import file_archives as archives
    calls = []
    @contextmanager
    def fake_process(args):
        calls.append(args)
        if args[0] == "l":
            yield io.BytesIO(b"----------\nPath = note.txt\nSize = 4\nFolder = -\n\n")
        else:
            assert args[:4] == ["x", "-so", "-spd", "--"]
            yield io.BytesIO(b"safe")
    monkeypatch.setattr(archives, "seven_zip", fake_process)
    archives.extract_with_7zip(tmp_path / "archive.7z", tmp_path, 4, 1)
    assert (tmp_path / "note.txt").read_bytes() == b"safe"
    assert len(calls) == 2


def test_cancelled_preparation_closes_late_response(monkeypatch):
    import threading
    from helpers import file_browser
    entered, release, closed = threading.Event(), threading.Event(), threading.Event()
    def prepare(*args):
        entered.set()
        assert release.wait(2)
        return {"download_name": "file"}
    monkeypatch.setattr(file_browser, "prepare_files_download", prepare)
    monkeypatch.setattr(transfers, "stream_file_download", lambda **kwargs: SimpleNamespace(close=closed.set))
    async def run():
        task = asyncio.create_task(file_browser.prepare_files_response(["/file"]))
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
        release.set()
        assert await asyncio.to_thread(closed.wait, 2)
    asyncio.run(run())


def test_delete_and_rename_operate_on_link_not_target(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"keep")
    link = tmp_path / "link"
    link.symlink_to(target)
    browser = FileBrowser()
    assert browser.rename_item(str(link), "renamed")
    renamed = tmp_path / "renamed"
    assert renamed.is_symlink() and target.read_bytes() == b"keep"
    assert browser.delete_file(str(renamed))
    assert target.read_bytes() == b"keep"
    assert not renamed.is_symlink()


def test_missing_delete_path_never_targets_root(monkeypatch):
    import shutil
    monkeypatch.setattr(shutil, "rmtree", lambda *args, **kwargs: pytest.fail("Root deletion attempted"))
    assert FileBrowser().delete_file("") is False
    assert FileBrowser().delete_file("/") is False


def test_files_download_endpoint_prepares_then_delivers(tmp_path, monkeypatch):
    from api.download_work_dir_files import DownloadFiles
    from helpers import runtime
    monkeypatch.setattr(runtime, "is_development", lambda: False)
    monkeypatch.setattr(FileBrowser, "max_file_bytes", classmethod(lambda cls: 100))
    path = tmp_path / "file.txt"
    path.write_bytes(b"download")
    handler = DownloadFiles(None, None)
    post = SimpleNamespace(method="POST", args={})
    prepared = asyncio.run(handler.process({"paths": [str(path)]}, post))
    token = prepared["download_url"].split("token=", 1)[1]
    response = asyncio.run(handler.process({}, SimpleNamespace(method="GET", args={"token": token})))
    assert b"".join(response.response) == b"download"
    response.close()
    assert handler.requires_auth() and handler.requires_csrf()


def test_download_endpoint_maps_plain_errors_locally():
    from api.download_work_dir_files import DownloadFiles
    from helpers import file_transfers
    handler = DownloadFiles(None, None)
    request = SimpleNamespace(method="GET", args={"token": "missing"})
    assert asyncio.run(handler.process({}, request)).status_code == 404
    body = io.BytesIO(b"content")
    def denied():
        raise PermissionError("Download permission revoked")
    token = file_transfers.prepare_download_response(file_transfers.stream_file_download(body, "file"), denied)
    request.args["token"] = token
    assert asyncio.run(handler.process({}, request)).status_code == 403
    assert body.closed
