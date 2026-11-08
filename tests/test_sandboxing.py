from __future__ import annotations

import datetime as dt
import dataclasses
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from plugins._sandboxing.helpers.images import (
    SandboxImageConfig,
    SandboxImageInfo,
    SandboxImageManager,
    image_info_dict,
    normalize_image_reference,
    validate_digest,
)
from plugins._sandboxing.helpers.manager import (
    ROOTFS_SNAPSHOT,
    SandboxConfig,
    SandboxError,
    SandboxInfo,
    SandboxManager,
    SandboxMount,
    sandbox_info_dict,
    validate_name,
)


IMAGE_DIGEST = "sha256:" + "a" * 64
IMAGE_REFERENCE = "docker.io/library/python:3.13-slim-bookworm"


def _cache_image(
    images: SandboxImageManager,
    *,
    digest: str = IMAGE_DIGEST,
    reference: str = IMAGE_REFERENCE,
    last_used_at: str | None = None,
) -> SandboxImageInfo:
    path = images.config.cache_dir / digest.replace(":", "-")
    rootfs = path / "rootfs"
    (rootfs / "bin").mkdir(parents=True)
    (rootfs / "bin" / "sh").write_text("", encoding="utf-8")
    (rootfs / "bin" / "bash").write_text("", encoding="utf-8")
    (rootfs / "workspace").mkdir()
    now = last_used_at or dt.datetime.now(dt.timezone.utc).isoformat()
    info = SandboxImageInfo(
        digest=digest,
        reference=reference,
        references=(reference,),
        status="ready",
        created_at=now,
        last_used_at=now,
        size_bytes=0,
        os="linux",
        architecture="amd64",
        rootfs=rootfs,
        environment=("PATH=/image/bin:/usr/bin:/bin",),
    )
    images._write_info_path(path / "metadata.json", info)
    return images.inspect(digest)


@pytest.fixture
def manager(tmp_path: Path) -> SandboxManager:
    runsc = tmp_path / "runsc"
    runsc.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    runsc.chmod(0o755)
    images = SandboxImageManager(
        SandboxImageConfig(
            skopeo=runsc,
            umoci=runsc,
            cache_dir=tmp_path / "images",
            default_image=IMAGE_REFERENCE,
            cleanup_days=30,
            max_output_bytes=4096,
        )
    )
    _cache_image(images)
    return SandboxManager(
        SandboxConfig(
            runsc=runsc,
            instances_dir=tmp_path / "state" / "instances",
            runsc_root=tmp_path / "runsc-root",
            shared_dir=tmp_path / "shared",
            default_image=IMAGE_REFERENCE,
            temporary_lifetime_days=7,
            max_output_bytes=4096,
        ),
        images,
    )


def _metadata(
    manager: SandboxManager,
    name: str,
    *,
    sandbox_type: str = "temporary",
    status: str = "running",
    last_used_at: str | None = None,
) -> dict:
    now = last_used_at or dt.datetime.now(dt.timezone.utc).isoformat()
    path = manager.config.instances_dir / name
    for directory in (path, path / "bundle", path / "overlay", path / "logs"):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    (path / ".lock").touch()
    value = {
        "schema_version": 2,
        "name": name,
        "sandbox_type": sandbox_type,
        "network": "host",
        "created_at": now,
        "last_used_at": now,
        "snapshot_at": None,
        "rootfs_snapshot": None,
        "image_ref": IMAGE_REFERENCE,
        "image_digest": IMAGE_DIGEST,
        "launch_mode": "detached",
        "launcher_pid": None,
        "last_known_status": status,
        "mounts": [],
        "ownership": {"chat_id": None, "project_id": None, "agent_id": None},
    }
    manager._atomic_write_json(path / "metadata.json", value)
    return value


def _info(name: str, status: str = "running") -> SandboxInfo:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return SandboxInfo(
        name=name,
        status=status,
        sandbox_type="temporary",
        network="host",
        created_at=now,
        last_used_at=now,
        snapshot_at=None,
        expires_at=None,
    )


def test_name_validation_and_path_traversal_are_conservative() -> None:
    for name in ("a", "alpha-1", "A.B_c", "x" * 64):
        assert validate_name(name) == name
    for name in ("", "../escape", "with/slash", "space here", "x" * 65):
        with pytest.raises(SandboxError):
            validate_name(name)


def test_public_info_is_json_serializable(tmp_path: Path) -> None:
    info = dataclasses.replace(
        _info("alpha"), mounts=(SandboxMount(tmp_path, "/mnt/data", True),)
    )

    encoded = json.dumps(sandbox_info_dict(info))

    assert str(tmp_path) in encoded


def test_public_image_info_omits_private_rootfs_and_environment(
    manager: SandboxManager,
) -> None:
    info = manager.images.inspect(IMAGE_DIGEST)

    payload = image_info_dict(info)

    assert payload["digest"] == IMAGE_DIGEST
    assert "rootfs" not in payload
    assert "environment" not in payload
    json.dumps(payload)


def test_image_reference_and_digest_validation_is_conservative() -> None:
    assert normalize_image_reference("docker://python:3.13") == "python:3.13"
    assert validate_digest(IMAGE_DIGEST) == IMAGE_DIGEST
    for reference in ("", " docker:// ", "file:///tmp/image", "../image", "bad image"):
        with pytest.raises(Exception):
            normalize_image_reference(reference)
    for digest in ("", "sha256:nope", "md5:" + "a" * 32):
        with pytest.raises(Exception):
            validate_digest(digest)


def test_daemonless_image_pull_is_digest_pinned_and_atomic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "tool"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    images = SandboxImageManager(
        SandboxImageConfig(
            skopeo=executable,
            umoci=executable,
            cache_dir=tmp_path / "images",
            default_image="docker.io/example/sandbox:latest",
            max_output_bytes=4096,
        )
    )
    calls: list[list[str]] = []

    def fake_run(argv, *, timeout, operation, check=True):
        command = list(argv)
        calls.append(command)
        if "inspect" in command:
            return (
                0,
                json.dumps(
                    {
                        "Digest": IMAGE_DIGEST,
                        "Os": "linux",
                        "Architecture": "amd64",
                    }
                ),
                "",
                False,
            )
        if "unpack" in command:
            bundle = Path(command[-1])
            rootfs = bundle / "rootfs"
            (rootfs / "bin").mkdir(parents=True)
            (rootfs / "bin" / "sh").write_text("sh", encoding="utf-8")
            (rootfs / "bin" / "bash").write_text("bash", encoding="utf-8")
            (bundle / "config.json").write_text(
                json.dumps({"process": {"env": ["PATH=/custom/bin:/bin"]}}),
                encoding="utf-8",
            )
        return 0, "", "", False

    monkeypatch.setattr(images, "_run", fake_run)

    info = images.pull("docker.io/example/sandbox:latest")

    assert info.digest == IMAGE_DIGEST
    assert info.rootfs and info.rootfs.is_dir()
    copy = next(command for command in calls if "copy" in command)
    assert (
        f"docker://docker.io/example/sandbox@{IMAGE_DIGEST}" in copy
    )
    assert not any(path.name.startswith(".pull-") for path in images.config.cache_dir.iterdir())


def test_image_cleanup_preserves_every_sandbox_reference(
    manager: SandboxManager,
) -> None:
    now = dt.datetime(2026, 8, 5, tzinfo=dt.timezone.utc)
    old = (now - dt.timedelta(days=31)).isoformat()
    unused_digest = "sha256:" + "b" * 64
    _cache_image(
        manager.images,
        digest=unused_digest,
        reference="docker.io/example/unused:old",
        last_used_at=old,
    )
    _metadata(manager, "alpha", last_used_at=old)

    removed = manager.cleanup_images(now=now)

    assert removed == [unused_digest]
    assert not (manager.images.config.cache_dir / unused_digest.replace(":", "-")).exists()
    assert manager.images.inspect(IMAGE_DIGEST).digest == IMAGE_DIGEST
    with pytest.raises(SandboxError, match="still used by sandboxes: alpha"):
        manager.delete_image(IMAGE_DIGEST)


def test_tag_alias_updates_do_not_rebase_existing_digest(
    manager: SandboxManager,
) -> None:
    refreshed_digest = "sha256:" + "c" * 64
    _cache_image(
        manager.images,
        digest=refreshed_digest,
        reference=IMAGE_REFERENCE,
    )
    manager.images._ensure_layout()
    with manager.images._cache_lock():
        manager.images._set_alias_locked(IMAGE_REFERENCE, refreshed_digest)

    old = manager.images.ensure(IMAGE_REFERENCE, digest=IMAGE_DIGEST)
    new = manager.images.ensure(IMAGE_REFERENCE)

    assert old.digest == IMAGE_DIGEST
    assert new.digest == refreshed_digest


def test_broken_unreferenced_image_can_be_deleted_by_exact_digest(
    manager: SandboxManager,
) -> None:
    digest = "sha256:" + "d" * 64
    path = manager.images.config.cache_dir / digest.replace(":", "-")
    (path / "rootfs").mkdir(parents=True)
    (path / "metadata.json").write_text("{}", encoding="utf-8")

    assert manager.delete_image(digest) is True
    assert not path.exists()


def test_image_deletion_honors_digest_even_when_other_sandbox_metadata_is_broken(
    manager: SandboxManager,
) -> None:
    metadata = _metadata(manager, "broken-alpha")
    metadata["schema_version"] = 999
    metadata["created_at"] = "not-a-timestamp"
    manager._atomic_write_json(
        manager.config.instances_dir / "broken-alpha" / "metadata.json", metadata
    )

    with pytest.raises(SandboxError, match="still used by sandboxes: broken-alpha"):
        manager.delete_image(IMAGE_DIGEST)


def test_runsc_commands_select_fast_or_disk_overlay(manager: SandboxManager) -> None:
    temporary = manager.runsc_command_for_test(
        "alpha", "host", "temporary", "state", "alpha"
    )
    permanent = manager.runsc_command_for_test(
        "alpha", "none", "permanent", "state", "alpha"
    )
    assert "--overlay2=root:memory" in temporary
    assert not any(value.startswith("--overlay2=root:dir=") for value in temporary)
    assert f"--overlay2=root:dir={manager.config.instances_dir / 'alpha' / 'overlay'}" in permanent
    assert "--network=none" in permanent
    for required in (
        "--allow-rootfs-tar-annotation",
        "--rootless=true",
        "--platform=systrap",
        "--directfs=false",
        "--file-access=exclusive",
        "--file-access-mounts=shared",
    ):
        assert required in temporary


def test_oci_network_shared_and_optional_mount_contract(
    manager: SandboxManager, tmp_path: Path
) -> None:
    source_ro = tmp_path / "read-only"
    source_rw = tmp_path / "read-write"
    source_ro.mkdir()
    source_rw.mkdir()
    host = manager.oci_config_for_test(
        "alpha",
        "host",
        "temporary",
        mounts=[
            {"source": str(source_ro), "destination": "/mnt/input", "read_only": True},
            {"source": str(source_rw), "destination": "/mnt/output", "read_only": False},
        ],
    )
    isolated = manager.oci_config_for_test("alpha", "none", "temporary")
    assert {item["type"] for item in host["linux"]["namespaces"]} == {
        "pid",
        "ipc",
        "uts",
        "mount",
    }
    assert {item["type"] for item in isolated["linux"]["namespaces"]} == {
        "pid",
        "ipc",
        "uts",
        "mount",
        "network",
    }
    mounts = {item["destination"]: item for item in host["mounts"]}
    assert mounts["/shared"]["source"] == str(manager.config.shared_dir)
    assert "rw" in mounts["/shared"]["options"]
    assert "ro" in mounts["/mnt/input"]["options"]
    assert "rw" in mounts["/mnt/output"]["options"]
    assert "CAP_SYS_ADMIN" not in host["process"]["capabilities"]["bounding"]
    assert host["root"]["path"] == str(manager.images.inspect(IMAGE_DIGEST).rootfs)
    assert "PATH=/image/bin:/usr/bin:/bin" in host["process"]["env"]


def test_mounts_reject_symlinks_reserved_paths_and_duplicates(
    manager: SandboxManager, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    link = tmp_path / "link"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(SandboxError):
        manager.oci_config_for_test(
            "alpha", "host", "temporary", [{"source": str(link), "destination": "/mnt/a"}]
        )
    with pytest.raises(SandboxError):
        manager.oci_config_for_test(
            "alpha", "host", "temporary", [{"source": str(source), "destination": "/etc/a"}]
        )
    with pytest.raises(SandboxError):
        manager.oci_config_for_test(
            "alpha", "host", "temporary", [{"source": str(source), "destination": "//etc/a"}]
        )
    with pytest.raises(SandboxError):
        manager.oci_config_for_test(
            "alpha",
            "host",
            "temporary",
            [
                {"source": str(source), "destination": "/mnt/a"},
                {"source": str(source), "destination": "/mnt/a"},
            ],
        )


def test_inspect_classifies_running_stopped_recoverable_stale_and_broken(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = _metadata(manager, "alpha")
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: ({"status": "running"}, None))
    assert manager.inspect("alpha").status == "running"

    snapshot = manager.config.instances_dir / "alpha" / ROOTFS_SNAPSHOT
    snapshot.write_bytes(b"snapshot")
    metadata["rootfs_snapshot"] = ROOTFS_SNAPSHOT
    metadata["last_known_status"] = "stopped"
    manager._atomic_write_json(snapshot.parent / "metadata.json", metadata)
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: (None, "container not found"))
    assert manager.inspect("alpha").status == "stopped"
    metadata["last_known_status"] = "running"
    manager._atomic_write_json(snapshot.parent / "metadata.json", metadata)
    assert manager.inspect("alpha").status == "recoverable"
    snapshot.unlink()
    assert manager.inspect("alpha").status == "stale"
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: (None, "permission denied"))
    assert manager.inspect("alpha").status == "broken"


def test_invalid_metadata_and_symlink_entries_are_not_adopted(
    manager: SandboxManager, tmp_path: Path
) -> None:
    manager.config.instances_dir.mkdir(parents=True)
    broken = manager.config.instances_dir / "broken"
    broken.mkdir()
    (broken / "metadata.json").write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (manager.config.instances_dir / "linked").symlink_to(outside, target_is_directory=True)
    listed = manager.list()
    assert [(item.name, item.status) for item in listed] == [("broken", "broken")]
    with pytest.raises(SandboxError):
        manager.delete("linked")
    assert outside.exists()


def test_ensure_running_creates_missing_and_wakes_stopped(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = Mock(return_value=_info("new"))
    monkeypatch.setattr(manager, "create", created)
    assert manager.ensure_running("new").name == "new"
    created.assert_called_once_with(
        "new", network="host", sandbox_type="temporary", image=""
    )

    _metadata(manager, "sleeping", status="stopped")
    monkeypatch.setattr(manager, "inspect", lambda name: _info(name, "stopped"))
    started = Mock(return_value=_info("sleeping"))
    monkeypatch.setattr(manager, "start", started)
    assert manager.ensure_running("sleeping").status == "running"
    started.assert_called_once_with("sleeping")


def test_stop_saves_before_termination_and_cleanup(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    _metadata(manager, "alpha")
    calls: list[str] = []
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: ({"status": "running"}, None))
    monkeypatch.setattr(manager, "_save_locked", lambda *args: calls.append("save"))
    monkeypatch.setattr(manager, "_stop_runtime", lambda *args: calls.append("stop"))
    monkeypatch.setattr(manager, "_force_runtime_delete", lambda *args: calls.append("delete") or True)
    monkeypatch.setattr(manager, "inspect", lambda name: _info(name, "stopped"))
    assert manager.stop("alpha").status == "stopped"
    assert calls == ["save", "stop", "delete"]


def test_stop_runtime_force_deletes_when_kill_state_remains_running(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = _metadata(manager, "alpha")
    monkeypatch.setattr(
        manager,
        "_runtime_state",
        lambda *args: ({"status": "running"}, None),
    )
    monkeypatch.setattr(
        manager,
        "_wait_for_status",
        lambda *args, **kwargs: ({"status": "running"}, "last status was 'running'"),
    )
    monkeypatch.setattr(manager, "_run_quiet", lambda *args, **kwargs: None)
    force_delete = Mock(return_value=True)
    monkeypatch.setattr(manager, "_force_runtime_delete", force_delete)

    manager._stop_runtime("alpha", metadata)

    force_delete.assert_called_once_with("alpha", metadata)


def test_start_refuses_missing_snapshot(manager: SandboxManager, monkeypatch: pytest.MonkeyPatch) -> None:
    _metadata(manager, "alpha", status="stopped")
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: (None, "container not found"))
    with pytest.raises(SandboxError, match="no valid restart snapshot"):
        manager.start("alpha")


def test_failed_save_preserves_previous_snapshot(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = _metadata(manager, "alpha")
    path = manager.config.instances_dir / "alpha"
    snapshot = path / ROOTFS_SNAPSHOT
    snapshot.write_bytes(b"last-good")
    metadata["rootfs_snapshot"] = ROOTFS_SNAPSHOT
    manager._atomic_write_json(path / "metadata.json", metadata)
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: ({"status": "running"}, None))
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "snapshot failed", ""),
    )
    with pytest.raises(SandboxError, match="snapshot failed"):
        manager.save("alpha")
    assert snapshot.read_bytes() == b"last-good"


def test_delete_removes_exact_instance_only(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    _metadata(manager, "alpha")
    _metadata(manager, "beta")
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: (None, "container not found"))
    monkeypatch.setattr(manager, "_force_runtime_delete", lambda *args: True)
    assert manager.delete("alpha") is True
    assert not (manager.config.instances_dir / "alpha").exists()
    assert (manager.config.instances_dir / "beta").exists()


def test_exec_uses_exact_argv_and_touches_last_use(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = _metadata(manager, "alpha")
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: ({"status": "running"}, None))
    captured: dict[str, object] = {}

    def fake_run(argv, *, timeout, operation):
        captured.update(argv=argv, timeout=timeout, operation=operation)
        return 37, "out", "err", False

    monkeypatch.setattr(manager, "_run_captured", fake_run)
    result = manager.exec("alpha", ["sh", "-c", "exit 37"], timeout=12)
    assert result.exit_code == 37
    assert result.stdout == "out"
    assert captured["argv"][-7:] == [
        "exec",
        "--cwd=/workspace",
        "--user=0:0",
        "alpha",
        "sh",
        "-c",
        "exit 37",
    ]
    updated = json.loads((manager.config.instances_dir / "alpha" / "metadata.json").read_text())
    assert updated["last_used_at"] >= metadata["last_used_at"]


def test_interactive_command_uses_stdio_pty_without_unsupported_terminal_flag(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    _metadata(manager, "alpha")
    monkeypatch.setattr(
        manager,
        "_runtime_state",
        lambda *args: ({"status": "running"}, None),
    )

    command = manager.interactive_command("alpha")

    assert "--terminal" not in command
    assert command[command.index("exec") :] == [
        "exec",
        "--cwd=/workspace",
        "--user=0:0",
        "alpha",
        "/bin/bash",
        "--login",
    ]


def test_cleanup_expired_only_deletes_old_temporary_sandboxes(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc)
    old = (now - dt.timedelta(days=8)).isoformat()
    recent = (now - dt.timedelta(days=1)).isoformat()
    items = [
        SandboxInfo("old", "stopped", "temporary", "host", old, old, None, (now - dt.timedelta(days=1)).isoformat()),
        SandboxInfo("recent", "stopped", "temporary", "host", recent, recent, None, (now + dt.timedelta(days=6)).isoformat()),
        SandboxInfo("permanent", "stopped", "permanent", "host", old, old, None, None),
    ]
    monkeypatch.setattr(manager, "list", lambda: items)
    deleted: list[str] = []
    monkeypatch.setattr(
        manager,
        "_delete_if_expired",
        lambda name, now: deleted.append(name) or True,
    )
    assert manager.cleanup_expired(now=now) == ["old"]
    assert deleted == ["old"]


def test_expiry_is_rechecked_under_the_deletion_lock(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc)
    _metadata(
        manager,
        "recently-used",
        last_used_at=(now - dt.timedelta(days=1)).isoformat(),
    )
    runtime_state = Mock()
    monkeypatch.setattr(manager, "_runtime_state", runtime_state)

    assert manager._delete_if_expired("recently-used", now) is False
    runtime_state.assert_not_called()


def test_doctor_never_requests_a_host_shell(
    manager: SandboxManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []

    def fake_run(*args, **kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(args[0], 0, "runsc version test", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.doctor()
    assert calls and all(call.get("shell") is False for call in calls)


def test_docker_image_contains_sandbox_runtime_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "docker" / "base" / "Dockerfile").read_text(encoding="utf-8")
    packages = (
        root / "docker" / "base" / "fs" / "ins" / "install_base_packages4.sh"
    ).read_text(encoding="utf-8")
    compose = (root / "docker" / "run" / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    assert "AS sandbox-rootfs" not in dockerfile
    assert "/opt/agent-zero/sandbox-rootfs" not in dockerfile
    assert "FROM debian:trixie-slim AS gvisor-package" in dockerfile
    assert "apt-get install -y --no-install-recommends runsc" in dockerfile
    assert "https://storage.googleapis.com/gvisor/releases release main" in dockerfile
    assert "COPY --from=gvisor-package /usr/bin/runsc /usr/bin/runsc" in dockerfile
    assert (
        "COPY --from=gvisor-package /usr/bin/gvisor-bin/gvisor_sentry "
        "/usr/bin/gvisor-bin/gvisor_sentry"
    ) in dockerfile
    assert "containerd-shim-runsc-v1" not in dockerfile
    assert "checkpointgofer" not in dockerfile
    assert "runsc-metric-server" not in dockerfile
    assert "ca-certificates util-linux procps iproute2 skopeo umoci" in packages
    assert "gnupg" not in packages
    assert "privileged: false" in compose
    assert "seccomp:unconfined" in compose
