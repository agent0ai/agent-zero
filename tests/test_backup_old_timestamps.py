"""Backups must include files whose mtime predates the ZIP 1980 floor.

Package registries (cargo, npm, pip) extract entries with an epoch-zero mtime.
``zipfile`` refuses those timestamps by default, which used to abort the whole
backup instead of storing the file with a clamped date.
"""

from __future__ import annotations

import json
import os
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers.backup import BackupService


@pytest.fixture
def backup(tmp_path: Path):
    source = tmp_path / "old.txt"
    source.write_bytes(b"payload from an epoch-dated package registry file\n")

    service = BackupService()

    async def fake_test_patterns(metadata, max_files=1000):
        return [
            {
                "path": f"{service.agent_zero_root.rstrip('/')}/usr/old.txt",
                "real_path": str(source),
                "size": source.stat().st_size,
                "modified": "1970-01-01T00:00:00+00:00",
                "type": "file",
            }
        ]

    async def fake_info():
        return {}

    async def fake_author():
        return "test"

    # The pattern scan and environment probes are covered by other tests.
    service.test_patterns = fake_test_patterns  # type: ignore[method-assign]
    service._get_system_info = fake_info  # type: ignore[method-assign]
    service._get_environment_info = fake_info  # type: ignore[method-assign]
    service._get_backup_author = fake_author  # type: ignore[method-assign]
    return SimpleNamespace(service=service, source=source)


async def _create_backup(service: BackupService, backup_name: str) -> str:
    return await service.create_backup(
        include_patterns=[f"{service.agent_zero_root.rstrip('/')}/usr/**"],
        exclude_patterns=[],
        include_hidden=True,
        backup_name=backup_name,
    )


def _entry(archive: zipfile.ZipFile) -> str:
    return next(
        (name for name in archive.namelist() if name.endswith("usr/old.txt")), ""
    )


@pytest.mark.asyncio
async def test_create_backup_keeps_files_with_pre_1980_mtime(backup):
    os.utime(backup.source, (0, 0))
    assert backup.source.stat().st_mtime == 0

    zip_path = await _create_backup(backup.service, "old-timestamps")

    try:
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            entry = _entry(archive)
            assert entry, archive.namelist()
            assert archive.read(entry) == backup.source.read_bytes()
            info = archive.getinfo(entry)
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.compress_type == zipfile.ZIP_DEFLATED
            metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
            assert metadata["total_files"] == 1
    finally:
        Path(zip_path).unlink(missing_ok=True)

    # The clamp applies to the archive entry only, never to the source file.
    assert backup.source.stat().st_mtime == 0


@pytest.mark.asyncio
async def test_create_backup_preserves_regular_mtime(backup):
    # ZIP stores two-second granularity, so pin an even second for a stable value.
    timestamp = 1_700_000_000
    os.utime(backup.source, (timestamp, timestamp))

    zip_path = await _create_backup(backup.service, "recent-timestamps")

    try:
        with zipfile.ZipFile(zip_path) as archive:
            entry = _entry(archive)
            assert entry, archive.namelist()
            assert archive.getinfo(entry).date_time == time.localtime(timestamp)[:6]
            assert archive.read(entry) == backup.source.read_bytes()
    finally:
        Path(zip_path).unlink(missing_ok=True)
