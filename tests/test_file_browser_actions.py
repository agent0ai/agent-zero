from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import os
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from helpers import file_browser_actions as actions
from helpers.file_browser import FileBrowser


def test_trash_restore_preserves_links_and_refuses_collisions(tmp_path, monkeypatch):
    monkeypatch.setattr(actions, "trash_root", lambda: tmp_path / "trash")
    real = tmp_path / "real"
    real.write_bytes(b"original")
    link = tmp_path / "other"
    link.symlink_to(real)
    actions.trash_item("trash", str(link))
    record, = actions.list_trash()
    assert record["path"] == str(link)
    link.write_bytes(b"replacement")
    with pytest.raises(FileExistsError):
        actions.trash_item("restore", record["id"])
    assert link.read_bytes() == b"replacement"
    link.unlink()
    actions.trash_item("restore", record["id"])
    assert link.is_symlink()
    actions.trash_item("trash", str(link))
    actions.trash_item("purge", actions.list_trash()[0]["id"])
    assert not os.path.lexists(link)
    assert real.read_bytes() == b"original"
    assert actions.list_trash() == []
    with pytest.raises(ValueError):
        actions.trash_item("purge", "../real")
    with pytest.raises(ValueError):
        actions.trash_item("trash", str(tmp_path))


def test_zip_and_listing_keep_exact_names(tmp_path):
    path = tmp_path / "two  spaces -> trailing "
    path.write_bytes(b"hello")
    link = tmp_path / "one -> two"
    link.symlink_to(path)
    browser = FileBrowser()
    browser.base_dir = tmp_path
    entries = {entry["name"]: entry for entry in browser.get_files("")["entries"]}
    assert entries[link.name]["symlink_target"] == str(path)
    archived = actions.compress([str(path)], str(tmp_path), "result")
    with zipfile.ZipFile(archived) as bundle:
        assert bundle.read(path.name) == b"hello"
    with pytest.raises(FileExistsError):
        actions.compress([str(path)], str(tmp_path), "result")
    with pytest.raises(ValueError):
        actions.compress([str(link)], str(tmp_path), "linked")


def test_device_upload_concurrent_collisions_and_sanitized_parents(tmp_path):
    browser = FileBrowser()
    browser.base_dir = tmp_path

    def upload(value):
        return browser.upload_tree([SimpleNamespace(stream=BytesIO(value))], "", ["report"], [])
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(upload, [b"one", b"two"]))
    assert sorted(result[0][0] for result in results) == ["report", "report (1)"]
    assert {item.read_bytes() for item in tmp_path.iterdir()} == {b"one", b"two"}
    with pytest.raises(ValueError, match="Duplicate upload name"):
        browser.upload_tree([], "", [], ["a?/first", "a*/second"])


def test_failed_copy_discards_staged_items_without_publishing(tmp_path):
    browser = FileBrowser()
    browser.base_dir = tmp_path
    (tmp_path / "destination").mkdir()
    (tmp_path / "regular").write_text("keep")
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(ValueError, match="regular files"):
        browser.transfer_items(["regular", "pipe"], "destination", copy=True)
    assert list((tmp_path / "destination").iterdir()) == []
    assert (tmp_path / "regular").read_text() == "keep"
