import asyncio
import inspect
import io
from types import SimpleNamespace

import pytest
from api import download_work_dir_file as endpoint
from helpers import files, runtime

from pathlib import Path
import zipfile

from api.download_work_dir_file import resolve_download_path
from helpers.file_archives import create_selected_zip


def test_download_resolvers_match_file_browser_root(tmp_path: Path) -> None:
    file_path = tmp_path / "outside-a0.txt"
    file_path.write_text("downloadable", encoding="utf-8")

    assert resolve_download_path(str(file_path)) == str(file_path.resolve())

    archive_path = Path(create_selected_zip([str(file_path)], "/"))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            name = str(file_path).lstrip("/")
            assert archive.namelist() == [name]
            assert archive.read(name) == b"downloadable"
    finally:
        archive_path.unlink(missing_ok=True)


@pytest.mark.parametrize("development", [False, True])
@pytest.mark.parametrize("fail", [False, True])
def test_directory_download_cleans_owned_zip(tmp_path, monkeypatch, development, fail):
    source = tmp_path / "folder"
    source.mkdir()
    (source / "file.txt").write_text("downloadable")
    archive_paths = []
    original_zip = files.zip_dir
    def make_zip(path):
        result = original_zip(path)
        archive_paths.append(Path(result))
        return result
    async def call(function, *args, **kwargs):
        result = function(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result
    def broken(*args, **kwargs):
        raise OSError("interrupted")
    monkeypatch.setattr(files, "zip_dir", make_zip)
    monkeypatch.setattr(runtime, "is_development", lambda: development)
    monkeypatch.setattr(runtime, "call_development_function", call)
    if fail:
        monkeypatch.setattr(files if development else endpoint,
                            "read_file_base64" if development else "stream_file_download", broken)
    handler = endpoint.DownloadFile(None, None)
    request = SimpleNamespace(args={"path": str(source)})
    if fail:
        with pytest.raises(OSError, match="interrupted"):
            asyncio.run(handler.process({}, request))
    else:
        response = asyncio.run(handler.process({}, request))
        try:
            with zipfile.ZipFile(io.BytesIO(b"".join(response.response))) as archive:
                assert archive.read("folder/file.txt") == b"downloadable"
        finally:
            response.close()
    assert archive_paths and not any(path.exists() for path in archive_paths)
    assert (source / "file.txt").read_text() == "downloadable"
