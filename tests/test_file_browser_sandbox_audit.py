from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from helpers import files
from helpers.file_browser import AUDIT_LOG_FILENAME, FileBrowser


def audit_log_path(base: Path) -> Path:
    return base / "logs" / AUDIT_LOG_FILENAME


def test_file_browser_base_dir_rooted_at_work_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))

    browser = FileBrowser()

    assert browser.base_dir == Path(str(tmp_path)).resolve()
    assert str(browser.base_dir) != "/"


def test_file_browser_sandbox_rejects_escape_from_work_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    browser = FileBrowser()

    # Paths that resolve outside the sandboxed work dir must be rejected.
    assert browser.delete_file("../../../etc") is False
    with pytest.raises(ValueError):
        browser.rename_item("../../../etc/passwd", "evil")

    # Rejected mutations must not produce audit lines.
    assert not audit_log_path(tmp_path).exists()


def test_file_browser_mutation_appends_audit_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    browser = FileBrowser()
    source = tmp_path / "original.txt"
    source.write_text("hello", encoding="utf-8")
    target = tmp_path / "renamed.txt"

    assert browser.rename_item("original.txt", "renamed.txt") is True
    assert target.read_text(encoding="utf-8") == "hello"

    log_file = audit_log_path(tmp_path)
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    parts = [part.strip() for part in lines[0].split("|")]
    assert len(parts) == 5
    timestamp, remote_addr, action, src, dst = parts

    parsed = datetime.fromisoformat(timestamp)
    assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)
    assert remote_addr == "unknown"  # no flask request context in tests
    assert action == "rename"
    assert Path(src) == source.resolve()
    assert Path(dst) == target.resolve()


def test_file_browser_audit_failure_does_not_block_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    source = tmp_path / "original.txt"
    source.write_text("hello", encoding="utf-8")

    def broken_log_path() -> Path:
        raise RuntimeError("audit log unavailable")

    monkeypatch.setattr("helpers.file_browser._get_audit_log_path", broken_log_path)
    browser = FileBrowser()

    assert browser.rename_item("original.txt", "renamed.txt") is True
    assert (tmp_path / "renamed.txt").read_text(encoding="utf-8") == "hello"
    assert not (tmp_path / "original.txt").exists()