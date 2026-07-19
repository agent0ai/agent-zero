import json
import shutil
import zipfile
from pathlib import Path

import pytest

from helpers.backup import BackupService


class UploadedBackup:
    def __init__(self, path: Path):
        self.path = path

    def save(self, target: str) -> None:
        shutil.copyfile(self.path, target)


@pytest.mark.asyncio
async def test_default_backup_patterns_exclude_time_travel_history(tmp_path):
    root = tmp_path / "a0"
    usr = root / "usr"
    time_travel = usr / ".time_travel" / "workspaces" / "demo" / "repo.git"
    time_travel.mkdir(parents=True)
    (usr / "settings.json").write_text('{"ok": true}\n', encoding="utf-8")
    (time_travel / "objects.pack").write_text("history\n", encoding="utf-8")

    service = BackupService()
    service.agent_zero_root = str(root)
    service.base_paths = {str(root): str(root)}
    metadata = service.get_default_backup_metadata()

    files = await service.test_patterns(metadata, max_files=None)
    paths = {item["real_path"] for item in files}

    assert str(usr / "settings.json") in paths
    assert str(time_travel / "objects.pack") not in paths
    assert f"{root}/usr/.time_travel/**" in metadata["exclude_patterns"]


@pytest.mark.asyncio
async def test_pattern_scan_can_run_without_file_limit(tmp_path):
    root = tmp_path / "a0"
    usr = root / "usr"
    usr.mkdir(parents=True)
    for index in range(3):
        (usr / f"file-{index}.txt").write_text(f"{index}\n", encoding="utf-8")

    service = BackupService()
    service.agent_zero_root = str(root)
    service.base_paths = {str(root): str(root)}
    metadata = {
        "include_patterns": [f"{root}/usr/**"],
        "exclude_patterns": [],
        "include_hidden": True,
    }

    capped_files = await service.test_patterns(metadata, max_files=2)
    all_files = await service.test_patterns(metadata, max_files=None)

    assert len(capped_files) == 2
    assert len(all_files) == 3


@pytest.mark.asyncio
async def test_create_backup_uses_unlimited_pattern_scan(tmp_path, monkeypatch):
    source_file = tmp_path / "source.txt"
    source_file.write_text("payload\n", encoding="utf-8")
    captured = {}

    service = BackupService()

    async def fake_test_patterns(metadata, max_files=1000):
        captured["max_files"] = max_files
        return [
            {
                "path": f"{service.agent_zero_root.rstrip('/')}/usr/file-{index}.txt",
                "real_path": str(source_file),
                "size": source_file.stat().st_size,
                "modified": "2026-06-26T00:00:00+00:00",
                "type": "file",
            }
            for index in range(3)
        ]

    async def fake_info():
        return {}

    async def fake_author():
        return "test"

    monkeypatch.setattr(service, "test_patterns", fake_test_patterns)
    monkeypatch.setattr(service, "_get_system_info", fake_info)
    monkeypatch.setattr(service, "_get_environment_info", fake_info)
    monkeypatch.setattr(service, "_get_backup_author", fake_author)

    zip_path = await service.create_backup(
        include_patterns=[f"{service.agent_zero_root}/usr/**"],
        exclude_patterns=[],
        include_hidden=True,
        backup_name="large-backup",
    )

    assert captured["max_files"] is None
    with zipfile.ZipFile(zip_path) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["total_files"] == 3
        assert (
            f"{service.agent_zero_root.rstrip('/').lstrip('/')}/usr/file-2.txt"
            in archive.namelist()
        )


@pytest.mark.asyncio
async def test_restore_can_reach_files_after_50000_archive_entries(tmp_path):
    old_root = "/old-a0"
    archive_root = old_root.lstrip("/")
    file_count = 50_001
    last_index = file_count - 1
    zip_path = tmp_path / "large-backup.zip"

    metadata = {
        "environment_info": {"agent_zero_root": old_root},
        "include_patterns": [f"{old_root}/usr/large/**"],
        "exclude_patterns": [],
        "include_hidden": True,
    }
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        for index in range(file_count):
            payload = "tail payload\n" if index == last_index else ""
            archive.writestr(
                f"{archive_root}/usr/large/file-{index:05d}.txt",
                payload,
            )

    service = BackupService()
    service.agent_zero_root = str(tmp_path / "restored-a0")

    result = await service.restore_backup(
        backup_file=UploadedBackup(zip_path),
        restore_include_patterns=[
            f"{old_root}/usr/large/file-{last_index:05d}.txt"
        ],
        restore_exclude_patterns=[],
        overwrite_policy="overwrite",
    )

    restored_path = (
        Path(service.agent_zero_root)
        / "usr"
        / "large"
        / f"file-{last_index:05d}.txt"
    )
    assert len(result["restored_files"]) == 1
    assert len(result["skipped_files"]) == file_count - 1
    assert result["errors"] == []
    assert restored_path.read_text(encoding="utf-8") == "tail payload\n"


@pytest.mark.asyncio
async def test_restore_clean_before_restore_uses_unlimited_pattern_scan(monkeypatch):
    service = BackupService()
    captured = {}

    async def fake_test_patterns(metadata, max_files=1000):
        captured["max_files"] = max_files
        return []

    monkeypatch.setattr(service, "test_patterns", fake_test_patterns)

    result = await service._find_files_to_clean_with_user_metadata(
        user_metadata={
            "include_patterns": [f"{service.agent_zero_root}/usr/**"],
            "exclude_patterns": [],
            "include_hidden": True,
        },
        original_metadata={
            "environment_info": {"agent_zero_root": service.agent_zero_root}
        },
    )

    assert result == []
    assert captured["max_files"] is None
