import calendar
import datetime
import importlib.util
import json
import os
import stat
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers.backup import BackupService
from helpers.localization import Localization


@pytest.fixture(params=["UTC0", "EST5", "JST-9"])
def process_timezone(request, monkeypatch):
    if not hasattr(time, "tzset"):
        pytest.skip("Changing the process timezone requires time.tzset")
    previous_timezone = os.environ.get("TZ")
    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    try:
        yield request.param
    finally:
        if previous_timezone is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous_timezone
        time.tzset()


@pytest.fixture(
    params=[
        (0, (1980, 1, 1, 0, 0, 0)),
        (315532800, (1980, 1, 1, 0, 0, 0)),
        (calendar.timegm((2024, 6, 7, 8, 9, 10)), None),
        (calendar.timegm((2107, 12, 31, 23, 59, 58)), None),
        (calendar.timegm((2108, 1, 2, 0, 0, 0)), (2107, 12, 31, 23, 59, 58)),
    ],
    ids=[
        "epoch-zero",
        "lower-bound-utc",
        "ordinary",
        "upper-bound-utc",
        "after-upper-bound",
    ],
)
def timestamped_file(request, tmp_path, process_timezone):
    timestamp, expected_zip_time = request.param
    source = tmp_path / "repo" / "usr" / "registry-file.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"user data must remain in the backup\n")
    source.chmod(0o640)
    os.utime(source, (timestamp, timestamp))
    if timestamp == 315532800 and process_timezone == "JST-9":
        expected_zip_time = (1980, 1, 1, 9, 0, 0)
    elif expected_zip_time is None:
        if timestamp == calendar.timegm((2024, 6, 7, 8, 9, 10)):
            hour = {"UTC0": 8, "EST5": 3, "JST-9": 17}[process_timezone]
            expected_zip_time = (2024, 6, 7, hour, 9, 10)
        else:
            hour = 18 if process_timezone == "EST5" else 23
            expected_zip_time = (2107, 12, 31, hour, 59, 58)
    return source, expected_zip_time


@pytest.mark.asyncio
async def test_manual_backup_accepts_out_of_range_file_times(
    timestamped_file, monkeypatch
):
    source, expected_zip_time = timestamped_file
    original_mtime = source.stat().st_mtime_ns
    original_mode = source.stat().st_mode
    root = source.parent.parent
    # Keep localization independent of the host TZ and avoid writing user state.
    localization = SimpleNamespace(
        now_iso=lambda: "2026-10-01T00:00:00+00:00",
        get_tzinfo=lambda: datetime.timezone.utc,
        get_timezone=lambda: "UTC",
    )
    monkeypatch.setattr(Localization, "get", lambda: localization)
    monkeypatch.setattr(BackupService, "_get_agent_zero_version", lambda self: "test")
    service = BackupService()
    service.agent_zero_root = str(root)
    service.base_paths = {str(root): str(root)}

    zip_path = Path(await service.create_backup([f"{root}/usr/**"], []))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive_name = str(source).lstrip("/")
            assert archive.read(archive_name) == source.read_bytes()
            assert archive.getinfo(archive_name).date_time == expected_zip_time
            assert stat.S_IMODE(
                archive.getinfo(archive_name).external_attr >> 16
            ) == stat.S_IMODE(original_mode)
            assert archive.testzip() is None
            metadata = json.loads(archive.read("metadata.json"))
            assert metadata["total_files"] == 1
            assert (
                metadata["files"][0]["modified"]
                == datetime.datetime.fromtimestamp(
                    source.stat().st_mtime, tz=datetime.timezone.utc
                ).isoformat()
            )
    finally:
        zip_path.unlink()
        zip_path.parent.rmdir()

    assert source.stat().st_mtime_ns == original_mtime
    assert source.stat().st_mode == original_mode


def test_self_update_backup_accepts_out_of_range_file_times(timestamped_file, tmp_path):
    source, expected_zip_time = timestamped_file
    original_mtime = source.stat().st_mtime_ns
    original_mode = source.stat().st_mode
    manager_path = (
        Path(__file__).resolve().parents[1]
        / "docker"
        / "run"
        / "fs"
        / "exe"
        / "self_update_manager.py"
    )
    spec = importlib.util.spec_from_file_location(
        "timestamp_backup_manager", manager_path
    )
    assert spec is not None and spec.loader is not None
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)

    zip_path = manager.create_usr_backup(
        repo_dir=source.parent.parent,
        backup_path=str(tmp_path / "backups"),
        backup_name="timestamp-backup.zip",
        conflict_policy="rename",
        logger=manager.NullLogger(),
    )

    with zipfile.ZipFile(zip_path) as archive:
        archive_name = "usr/registry-file.txt"
        assert archive.read(archive_name) == source.read_bytes()
        assert archive.getinfo(archive_name).date_time == expected_zip_time
        assert stat.S_IMODE(
            archive.getinfo(archive_name).external_attr >> 16
        ) == stat.S_IMODE(original_mode)
        assert archive.testzip() is None
    assert source.stat().st_mtime_ns == original_mtime
    assert source.stat().st_mode == original_mode
