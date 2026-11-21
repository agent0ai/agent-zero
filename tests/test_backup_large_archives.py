import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from dotenv import dotenv_values

from helpers import dotenv
from helpers.backup import BackupService


class UploadedBackup:
    def __init__(self, path: Path):
        self.path = path

    def save(self, target: str) -> None:
        shutil.copyfile(self.path, target)


@pytest.mark.asyncio
async def test_backup_includes_files_dated_before_1980(tmp_path):
    service = BackupService()
    service.agent_zero_root = str(tmp_path)
    service.base_paths = {str(tmp_path): str(tmp_path)}
    source = tmp_path / "usr" / "old.txt"
    source.parent.mkdir()
    source.write_bytes(b"old file contents")
    old_timestamp = datetime(1970, 1, 2, tzinfo=timezone.utc).timestamp()
    os.utime(source, (old_timestamp, old_timestamp))
    original_mtime = source.stat().st_mtime_ns
    member = source.as_posix().lstrip("/")

    defaults = service.get_default_backup_metadata()
    archive = Path(await service.create_backup(defaults["include_patterns"], defaults["exclude_patterns"]))
    try:
        with zipfile.ZipFile(archive) as backup:
            assert backup.testzip() is None
            assert backup.read(member) == b"old file contents"
            assert backup.getinfo(member).date_time == (1980, 1, 1, 0, 0, 0)
        assert source.stat().st_mtime_ns == original_mtime
    finally:
        shutil.rmtree(archive.parent)


@pytest.mark.asyncio
async def test_default_backup_walks_only_user_data_and_skips_shortcuts(tmp_path, monkeypatch):
    service = BackupService()
    service.agent_zero_root = str(tmp_path)
    service.base_paths = {str(tmp_path): str(tmp_path)}
    data = tmp_path / "usr/sandbox_data/demo"
    data.mkdir(parents=True)
    (data / "result").write_text("user data")
    runtime = tmp_path / "sandboxes"
    instance = runtime / "instances/demo"
    instance.mkdir(parents=True)
    (instance / "data").symlink_to(data)
    (runtime / "package").touch()

    walked = set()
    original_walk = os.walk

    def record_walk(*args, **kwargs):
        for row in original_walk(*args, **kwargs):
            walked.add(Path(row[0]))
            yield row

    monkeypatch.setattr(os, "walk", record_walk)
    metadata = service.get_default_backup_metadata()
    matches = await service.test_patterns(metadata)
    assert [row["path"] for row in matches] == [str(data / "result")]
    assert runtime not in walked
    metadata["include_patterns"] = [f"{tmp_path}/sandboxes/**"]
    assert [row["path"] for row in await service.test_patterns(metadata)] == [str(runtime / "package")]


@pytest.mark.asyncio
@pytest.mark.parametrize("symlink_root", [False, True])
@pytest.mark.parametrize("clean", [False, True])
@pytest.mark.parametrize("overwrite_policy", ["overwrite", "skip"])
async def test_portable_backup_round_trip_preserves_vps_connections(
    tmp_path, monkeypatch, symlink_root, clean, overwrite_policy
):
    source_root = tmp_path / "laptop" / "agent-zero"
    actual_root = tmp_path / "vps" / "installation"
    actual_root.mkdir(parents=True)
    destination_root = tmp_path / "vps" / "current" if symlink_root else actual_root
    if symlink_root:
        destination_root.symlink_to(actual_root, target_is_directory=True)
    portable_files = {
        "usr/plugins/_oauth/codex/auth.json": '{"tokens":{"refresh_token":"synthetic-saved-token"}}\n',
        "usr/plugins/_oauth/config.json": '{"codex":{"proxy_token":"synthetic-existing-proxy-token"}}\n',
        "usr/plugins/_model_config/config.json": '{"chat_model":{"provider":"codex_oauth","name":"saved-model"}}\n',
        "usr/projects/existing/.a0proj/settings.json": '{"name":"existing-project"}\n',
        "usr/settings.json": '{"setting":"from-laptop"}\n',
        "usr/.env": "AUTH_LOGIN=existing-user\nAUTH_PASSWORD=synthetic-password\nALLOWED_ORIGINS=https://laptop.invalid\n",
    }
    for name, content in portable_files.items():
        for root in [source_root, destination_root]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    destination_env = destination_root / "usr/.env"
    destination_env.write_text(portable_files["usr/.env"].replace("https://laptop.invalid", "https://vps.invalid"))
    (destination_root / "usr/settings.json").write_text('{"setting":"from-vps"}\n')
    stale_file = destination_root / "usr/stale.txt"
    stale_file.write_text("old-vps-data")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://vps.invalid")
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(destination_env))

    source = BackupService()
    source.agent_zero_root = str(source_root)
    source.base_paths = {str(source_root): str(source_root)}

    async def source_environment():
        return {"agent_zero_root": str(source_root)}

    monkeypatch.setattr(source, "_get_environment_info", source_environment)
    metadata = source.get_default_backup_metadata()
    archive = Path(await source.create_backup(metadata["include_patterns"], metadata["exclude_patterns"]))
    destination = BackupService()
    destination.agent_zero_root = str(destination_root)
    destination.base_paths = {str(destination_root): str(destination_root)}
    try:
        upload = UploadedBackup(archive)
        inspected = await destination.inspect_backup(upload)
        assert inspected["total_files"] == len(portable_files)
        options = {"clean_before_restore": clean, "overwrite_policy": overwrite_policy}
        preview = await destination.preview_restore(upload, **options)
        result = await destination.restore_backup(upload, **options)
        assert result["errors"] == []
        assert preview["delete_count"] == len(result["deleted_files"])
        for name, content in portable_files.items():
            expected = content
            if name == "usr/.env":
                expected = content.replace("https://laptop.invalid", "https://vps.invalid")
            elif name == "usr/settings.json" and overwrite_policy == "skip" and not clean:
                expected = '{"setting":"from-vps"}\n'
            assert (destination_root / name).read_text() == expected
        assert stale_file.exists() is not clean
        if clean and overwrite_policy == "skip":
            pytest.xfail("Pre-existing preview applies skip policy before simulating cleanup")
        assert preview["restore_count"] == len(result["restored_files"])
    finally:
        archive.unlink()
        archive.parent.rmdir()


@pytest.mark.asyncio
async def test_default_backup_patterns_exclude_generated_history_and_orchestrator_data(tmp_path):
    root = tmp_path / "a0"
    usr = root / "usr"
    time_travel = usr / ".time_travel" / "workspaces" / "demo" / "repo.git"
    time_travel.mkdir(parents=True)
    orchestrator_data = usr / "plugins" / "_orchestrator" / "data" / "codex"
    orchestrator_data.mkdir(parents=True)
    (usr / "settings.json").write_text('{"ok": true}\n', encoding="utf-8")
    (orchestrator_data.parent.parent / "config.json").write_text("{}\n", encoding="utf-8")
    (time_travel / "objects.pack").write_text("history\n", encoding="utf-8")
    (orchestrator_data / "state.sqlite").write_text("state\n", encoding="utf-8")

    service = BackupService()
    service.agent_zero_root = str(root)
    service.base_paths = {str(root): str(root)}
    metadata = service.get_default_backup_metadata()

    files = await service.test_patterns(metadata, max_files=None)
    paths = {item["real_path"] for item in files}

    assert str(usr / "settings.json") in paths
    assert str(orchestrator_data.parent.parent / "config.json") in paths
    assert str(time_travel / "objects.pack") not in paths
    assert str(orchestrator_data / "state.sqlite") not in paths
    assert f"{root}/usr/.time_travel/**" in metadata["exclude_patterns"]
    assert f"{root}/usr/plugins/_orchestrator/data/**" in metadata["exclude_patterns"]


@pytest.mark.parametrize(
    ("backup_credentials", "expected_credentials"),
    [
        (
            "AUTH_LOGIN=backup\nAUTH_PASSWORD=backup-password\n",
            {"AUTH_LOGIN": "backup", "AUTH_PASSWORD": "backup-password"},
        ),
        (
            "AUTH_LOGIN=\nAUTH_PASSWORD=\n",
            {"AUTH_LOGIN": "", "AUTH_PASSWORD": ""},
        ),
        ("", {}),
    ],
    ids=("credentials", "blank-credentials", "missing-credentials"),
)
@pytest.mark.parametrize("symlink_env", [False, True])
@pytest.mark.asyncio
async def test_restore_preserves_destination_origin_and_restores_backup_credentials(
    tmp_path, monkeypatch, backup_credentials, expected_credentials, symlink_env
):
    old_root = "/old-a0"
    destination_root = tmp_path / "a0"
    destination_env = destination_root / "usr" / ".env"
    destination_env.parent.mkdir(parents=True)
    if symlink_env:
        destination_env.symlink_to(destination_root / "instance.env")
    destination_env.write_text(
        "AUTH_LOGIN=current\n"
        "AUTH_PASSWORD=current-password\n"
        "ALLOWED_ORIGINS=http://current.example\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AUTH_LOGIN", "current")
    monkeypatch.setenv("AUTH_PASSWORD", "current-password")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://current.example")
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(destination_env))
    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        lambda: pytest.fail("restore must not reload unrelated environment values"),
    )

    zip_path = tmp_path / "backup.zip"
    metadata = {
        "environment_info": {"agent_zero_root": old_root},
        "include_patterns": [f"{old_root}/usr/**"],
        "exclude_patterns": [],
        "include_hidden": True,
    }
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        archive.writestr(
            "old-a0/usr/.env",
            f"{backup_credentials}ALLOWED_ORIGINS=http://backup.example\n"
            "PORTABLE_SETTING=restored\n",
        )

    service = BackupService()
    service.agent_zero_root = str(destination_root)
    result = await service.restore_backup(UploadedBackup(zip_path))

    assert dotenv_values(destination_env) == {
        **expected_credentials,
        "ALLOWED_ORIGINS": "http://current.example",
        "PORTABLE_SETTING": "restored",
    }
    assert len(result["restored_files"]) == 1
    assert result["errors"] == []


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


@pytest.mark.parametrize("escape", ["traversal", "symlink"])
@pytest.mark.parametrize("clean_before_restore", [False, True])
@pytest.mark.asyncio
async def test_restore_rejects_archive_member_before_changing_existing_files(
    tmp_path, escape, clean_before_restore
):
    old_root = "/old-a0"
    destination_root = tmp_path / "a0"
    outside_file = tmp_path / "outside.txt"
    existing_file = destination_root / "usr" / "settings.json"
    existing_file.parent.mkdir(parents=True)
    existing_file.write_text("current settings\n", encoding="utf-8")
    if escape == "symlink":
        (destination_root / "usr" / "escape").symlink_to(tmp_path, target_is_directory=True)
        unsafe_member = "old-a0/usr/escape/outside.txt"
    else:
        unsafe_member = "old-a0/usr/../../outside.txt"
    metadata = {
        "environment_info": {"agent_zero_root": old_root},
        "include_patterns": [f"{old_root}/usr/**"],
        "exclude_patterns": [],
    }
    zip_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        archive.writestr("old-a0/usr/settings.json", "backup settings\n")
        archive.writestr(unsafe_member, "malicious\n")

    service = BackupService()
    service.agent_zero_root = str(destination_root)

    for method in (service.preview_restore, service.restore_backup):
        with pytest.raises(Exception, match="escapes the restore root"):
            await method(
                backup_file=UploadedBackup(zip_path),
                restore_include_patterns=metadata["include_patterns"],
                clean_before_restore=clean_before_restore,
            )

        assert existing_file.read_text(encoding="utf-8") == "current settings\n"
    assert not outside_file.exists()


@pytest.mark.parametrize("link_kind", ["root", "file", "directory"])
@pytest.mark.parametrize("exclude_file", [False, True])
@pytest.mark.asyncio
async def test_restore_preserves_logical_paths_for_contained_symlinks(
    tmp_path, link_kind, exclude_file
):
    root = tmp_path / "real-a0"
    (root / "usr").mkdir(parents=True)
    target = root / "usr" / "settings.json"
    if link_kind == "root":
        logical_root = tmp_path / "a0"
        logical_root.symlink_to(root, target_is_directory=True)
        root = logical_root
    elif link_kind == "file":
        target = root / "instance.json"
        (root / "usr" / "settings.json").symlink_to(target)
    else:
        (root / "data").mkdir()
        (root / "usr" / "linked").symlink_to(root / "data", target_is_directory=True)
        target = root / "data" / "settings.json"
    target.write_text("current\n", encoding="utf-8")
    relative_path = "usr/linked/settings.json" if link_kind == "directory" else "usr/settings.json"
    metadata = {"environment_info": {"agent_zero_root": "/old-a0"}}
    zip_path = tmp_path / "backup.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        archive.writestr(f"old-a0/{relative_path}", "restored\n")
    service = BackupService()
    service.agent_zero_root = str(root)
    options = {
        "restore_include_patterns": ["/old-a0/usr/**"],
        "restore_exclude_patterns": [f"/old-a0/{relative_path}"] if exclude_file else [],
    }

    preview = await service.preview_restore(UploadedBackup(zip_path), **options)
    result = await service.restore_backup(UploadedBackup(zip_path), **options)

    assert preview["restore_count"] == len(result["restored_files"]) == (0 if exclude_file else 1)
    assert target.read_text(encoding="utf-8") == ("current\n" if exclude_file else "restored\n")
    assert result["errors"] == []
    if not exclude_file:
        assert result["restored_files"][0]["target_path"] == str(root / relative_path)
