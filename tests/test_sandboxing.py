from __future__ import annotations

import datetime as dt
import dataclasses
import json
import io
import os
import subprocess
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest

from plugins._sandboxing.helpers.images import (
    SandboxImageConfig,
    SandboxImageError,
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
def manager(tmp_path: Path, monkeypatch) -> SandboxManager:
    proot = tmp_path / "proot"
    proot.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    proot.chmod(0o755)
    images = SandboxImageManager(
        SandboxImageConfig(
            skopeo=proot,
            umoci=proot,
            cache_dir=tmp_path / "images",
            default_image=IMAGE_REFERENCE,
            cleanup_days=30,
            max_output_bytes=4096,
        )
    )
    _cache_image(images)
    from plugins._sandboxing.helpers import storage, bootstrap, manager as module
    monkeypatch.setattr(module, 'RUNTIME_DIR', tmp_path / 'scratch')
    monkeypatch.setattr(bootstrap, 'ensure', lambda *a: None)
    monkeypatch.setattr(SandboxManager, '_require_runtime_artifacts', lambda *a: None)
    monkeypatch.setattr(storage, 'ensure_base', lambda *a: None)
    monkeypatch.setattr(storage, 'grant', lambda *a, **kw: None)
    monkeypatch.setattr(storage, 'traverse', lambda *a: None)
    monkeypatch.setattr(module, 'set_owner', lambda *a: None)
    def lease(registry, owner):
        registry.mkdir(exist_ok=True)
        for p in registry.iterdir():
            if p.read_text() == str(owner): return int(p.name)
        uid = 20000 + len(list(registry.iterdir()))
        (registry / str(uid)).write_text(str(owner))
        return uid
    monkeypatch.setattr(storage, 'lease_uid', lease)
    def prepare(base, root, control, uid):
        shutil.copytree(base, root, symlinks=True)
        control.mkdir()
    monkeypatch.setattr(storage, 'prepare', prepare)
    return SandboxManager(
        SandboxConfig(
            proot=proot,
            instances_dir=tmp_path / "state" / "instances",
            uid_registry=tmp_path / "uids",
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


def test_files_connection_browses_stopped_sandbox_without_following_links(
    manager, monkeypatch, tmp_path,
):
    from helpers import file_connections
    from plugins._sandboxing.helpers import file_browser

    metadata = _metadata(manager, "research", status="stopped") | {"filesystem": "cow"}
    instance = manager.config.instances_dir / "research"
    manager._atomic_write_json(instance / "metadata.json", metadata)
    root = instance / "rootfs"
    (root / "workspace").mkdir(parents=True)
    (root / "workspace" / "report.txt").write_text("sandbox report")
    (tmp_path / "secret").write_text("outside")
    (root / "outside").symlink_to(tmp_path, target_is_directory=True)
    (root / "link").symlink_to(tmp_path / "secret")
    os.mkfifo(root / "pipe")

    provider = file_browser.SandboxFilesProvider()
    monkeypatch.setattr(file_browser, "get_manager", lambda: manager)
    monkeypatch.setattr(file_connections, "providers", lambda: {provider.id: provider})
    monkeypatch.setattr(file_connections, "data_dir", lambda _: tmp_path)

    info = manager.inspect("research")
    assert info.status == "stopped"
    path = provider.browse_path(manager, info)
    assert path
    assert file_connections.listing_config()["connections"][0]["name"] == "Sandbox — research"
    entries = file_connections.listing(path)["entries"]
    assert [entry["name"] for entry in entries] == ["workspace"]
    report = file_connections.listing(entries[0]["path"])["entries"][0]
    assert report["name"] == "report.txt"
    assert file_connections.read(report["path"], limit=20)[0] == b"sandbox report"
    with pytest.raises(ValueError, match="size limit"):
        file_connections.read(report["path"], limit=3)
    with pytest.raises(PermissionError):
        file_connections.write_from(report["path"], io.BytesIO(b"changed"))
    with pytest.raises(PermissionError):
        file_connections.mutate("delete", report["path"])
    for relative in ("outside/secret", "link", "pipe", "../metadata.json"):
        with pytest.raises(ValueError):
            file_connections.read(f"{path}/{relative}", limit=20)

    old_item, = provider.connections().values()
    later = dt.datetime.fromisoformat(metadata["created_at"]) + dt.timedelta(seconds=1)
    metadata["created_at"] = later.isoformat()
    manager._atomic_write_json(instance / "metadata.json", metadata)
    with pytest.raises(ValueError, match="no longer exists"):
        file_connections.listing(path)
    with pytest.raises(SandboxError, match="no longer available"):
        with provider.open(old_item, tmp_path):
            pytest.fail("Stale connection opened a replacement sandbox.")

    manager._atomic_write_json(instance / "metadata.json", metadata | {"service": True})
    assert not provider.connections()


def test_sandbox_workspace_survives_recreation_and_respects_explicit_mount(manager, tmp_path, monkeypatch):
    from plugins._sandboxing.helpers import file_browser

    usr = tmp_path / "usr"
    manager.config = dataclasses.replace(manager.config, user_dir=usr, instance_id="instance")
    seed = manager.images.inspect(IMAGE_DIGEST).rootfs / "workspace"
    (seed / "example").write_text("from image")
    monkeypatch.setattr(manager, "_launch", lambda *args: None)
    monkeypatch.setattr(manager, "_save_locked", lambda *args: None)
    info = manager.create("research")
    workspace = usr / "sandbox_data/research/workspace"
    shortcut = manager.config.instances_dir / "research/data"
    assert not shortcut.readlink().is_absolute()
    assert (shortcut / "workspace").samefile(workspace)
    assert SandboxMount(workspace, "/workspace", False) in info.mounts
    assert (workspace / "example").read_text() == "from image"
    (workspace / "example").write_text("user edit")
    assert (seed / "example").read_text() == "from image"
    config = json.loads((manager.config.instances_dir / "research/bundle/config.json").read_text())
    assert [str(workspace), "/workspace"] in config["bindings"]
    assert any(dest == "/a0/usr/sandbox_data" for _, dest in config["bindings"])

    monkeypatch.setattr(file_browser, "get_manager", lambda: manager)
    provider = file_browser.SandboxFilesProvider()
    with provider.open(provider.connection(manager, info), None) as browser:
        stream = io.BytesIO()
        browser.read("workspace/example", stream, 100)
        assert stream.getvalue() == b"user edit"

    manager.delete("research")
    assert not shortcut.is_symlink()
    assert (workspace / "example").read_text() == "user edit"
    manager.create("research")
    assert (shortcut / "workspace").samefile(workspace)
    assert (workspace / "example").read_text() == "user edit"
    supplied = tmp_path / "custom-workspace"
    supplied.mkdir()
    explicit = manager.create("custom", mounts=[SandboxMount(supplied, "/workspace")])
    assert [m for m in explicit.mounts if m.destination == "/workspace"] == [SandboxMount(supplied, "/workspace")]
    assert not (usr / "sandbox_data/custom/workspace").exists()
    assert (manager.config.instances_dir / "custom/data").samefile(usr / "sandbox_data/custom")
    selected = usr / "sandbox_data/another/selected"
    selected.mkdir(parents=True)
    manager.create("another", mounts=[SandboxMount(supplied, "/workspace"), SandboxMount(selected, "/data", False)])
    assert (manager.config.instances_dir / "another/data/selected").samefile(selected)


def test_workspace_rejects_symlink_ancestors_and_incomplete_seed(tmp_path):
    from plugins._sandboxing.helpers import storage

    target = tmp_path / "outside"
    target.mkdir()
    (tmp_path / "sandboxes").symlink_to(target)
    with pytest.raises(OSError):
        storage.prepare_workspace(tmp_path / "sandboxes/guest/workspace")
    assert not list(target.iterdir())

    seed = tmp_path / "seed"
    seed.mkdir()
    os.mkfifo(seed / "pipe")
    directory = tmp_path / "guest/workspace"
    with pytest.raises(shutil.Error):
        storage.prepare_workspace(directory, seed)
    assert not list(directory.parent.iterdir())
    (seed / "pipe").unlink()
    storage.prepare_workspace(directory, seed)
    assert directory.is_dir()

    link = tmp_path / "data"
    link.write_text("existing file")
    with pytest.raises(SandboxError, match="data shortcut"):
        storage.link_sandbox_data(link, directory)
    assert link.read_text() == "existing file"


def test_shared_cache_keeps_images_used_by_another_instance(manager):
    parent = manager.config.instances_dir
    manager.config = dataclasses.replace(manager.config, instances_dir=parent / "one", instance_id="one")
    peer = parent / "two" / "guest"
    peer.mkdir(parents=True)
    (peer / "metadata.json").write_text(json.dumps({"image_digest": IMAGE_DIGEST}))
    with pytest.raises(SandboxError, match="another Agent Zero instance"):
        manager.delete_image(IMAGE_DIGEST)
    assert manager.list() == []
    assert manager.images.inspect(IMAGE_DIGEST).digest == IMAGE_DIGEST


def test_storage_defaults_preserve_existing_stores_and_custom_paths(tmp_path, monkeypatch):
    from plugins._sandboxing.helpers import runtime

    monkeypatch.setattr(runtime.files, "get_abs_path", lambda path: str(tmp_path / path))
    store = tmp_path / "sandboxes"
    monkeypatch.setattr(runtime.runtime, "get_persistent_id", lambda: "instance")
    fresh = runtime.normalize_config({})
    assert fresh["image_cache_dir"] == str(store / "images")
    assert fresh["state_dir"] == str(store)
    assert fresh["uid_registry"] == fresh["state_dir"] + "/uids"
    monkeypatch.setattr(runtime.plugins, "get_plugin_config", lambda *args, **kwargs: {})
    config, images = runtime.manager_config()
    assert config.instances_dir == store / "instances"
    assert images.cache_dir == store / "images"
    (tmp_path / runtime.LEGACY_STORE / "images").mkdir(parents=True)
    old = runtime.normalize_config({})
    assert old["image_cache_dir"] == runtime.LEGACY_STORE + "/images"
    assert old["state_dir"] == runtime.LEGACY_STORE + "/runtime"
    assert runtime.manager_config()[0].instances_dir == tmp_path / runtime.LEGACY_STORE / "runtime/instances/instance"
    (store / "instances").mkdir(parents=True)
    assert runtime.normalize_config({})["state_dir"] == fresh["state_dir"]
    paths = dict(image_cache_dir="/custom/images", state_dir="/custom/state", uid_registry="/custom/uids")
    assert paths.items() <= runtime.normalize_config(paths).items()


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


@pytest.mark.parametrize("local_archive", [False, True])
def test_daemonless_image_load_is_digest_pinned_and_atomic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, local_archive: bool
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
            assert command[1:3] == ["raw", "unpack"]
            rootfs = Path(command[-1])
            (rootfs / "bin").mkdir(parents=True)
            (rootfs / "bin" / "sh").write_text("sh", encoding="utf-8")
            (rootfs / "bin" / "bash").write_text("bash", encoding="utf-8")
        if "runtime-config" in command:
            assert command[-3] == "--rootfs" and (Path(command[-2]) / "bin/sh").is_file()
            Path(command[-1]).write_text(
                json.dumps({"process": {"env": ["PATH=/custom/bin:/bin"]}}),
                encoding="utf-8",
            )
        return 0, "", "", False

    monkeypatch.setattr(images, "_run", fake_run)

    reference = "docker.io/example/sandbox:latest"
    if local_archive:
        archive = tmp_path / "image.tar"
        archive.write_bytes(b"test archive")
        info = images.import_archive(archive, reference)
    else:
        info = images.pull(reference)

    assert info.digest == IMAGE_DIGEST
    assert info.environment == ("PATH=/custom/bin:/bin",)
    assert info.rootfs and info.rootfs.is_dir()
    copy = next(command for command in calls if "copy" in command)
    if local_archive:
        inspected = next(command for command in calls if "inspect" in command)[-1]
        assert inspected.startswith(f"docker-archive:{images.config.cache_dir}/.pull-")
        assert inspected in copy
    else:
        assert f"docker://docker.io/example/sandbox@{IMAGE_DIGEST}" in copy
    calls.clear()
    assert images.ensure(reference).digest == IMAGE_DIGEST
    assert not calls
    assert not any(path.name.startswith(".pull-") for path in images.config.cache_dir.iterdir())


def test_image_archive_import_rejects_unsafe_or_oversized_sources(manager, tmp_path):
    archive = tmp_path / "image.tar"
    link = tmp_path / "link.tar"
    link.symlink_to(archive)
    for source in (archive, link, tmp_path):
        with pytest.raises(SandboxImageError, match="regular non-symlink"):
            manager.images.import_archive(source, "sandbox:local")
    archive.touch()
    with archive.open("wb") as output:
        output.truncate(manager.images.config.max_image_bytes + 1)
    with pytest.raises(SandboxImageError, match="size limit"):
        manager.images.import_archive(archive, "sandbox:local")


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


def test_runtime_command_has_no_engine_flags_and_preserves_arguments(manager):
    command = manager._process_command('alpha', {}, ['echo', 'a b;$(id)'], '/workspace')
    assert command[-4:] == [str(manager.config.instances_dir / 'alpha/bundle/config.json'), '--', 'echo', 'a b;$(id)']
    assert 'execute' in command and '--cwd' in command


def test_network_shared_and_readonly_bindings_are_explicit(manager, monkeypatch, tmp_path):
    from tests.test_sandbox_services import create_disk
    ro, rw = tmp_path / 'input', tmp_path / 'output'
    ro.mkdir(); rw.mkdir()
    create_disk(manager, monkeypatch, network='none', mounts=[SandboxMount(ro, '/input'), SandboxMount(rw, '/output', False)])
    config = json.loads((manager.config.instances_dir / 'service/bundle/config.json').read_text())
    assert config['network'] == 'none'
    assert dict((b,a) for a,b in config['bindings'])['/shared'] == str(manager.config.shared_dir)
    assert str(ro) in config['readonly'] and str(rw) not in config['readonly']
    assert config['environment']['PATH'] == '/image/bin:/usr/bin:/bin'
    assert config['root'].endswith('/service/fs')


def test_mounts_reject_symlinks_reserved_paths_and_duplicates(manager, tmp_path):
    source=tmp_path/'source'; source.mkdir()
    link=tmp_path/'link';link.symlink_to(source)
    for mounts in ([SandboxMount(link, '/input')], [SandboxMount(source, '/etc/a')],
                   [SandboxMount(source, '//etc/a')], [SandboxMount(source, '/a'), SandboxMount(source, '/a')],
                   [SandboxMount(source, '/a:b')]):
        with pytest.raises(SandboxError): manager._normalize_mounts(mounts)


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


def test_stop_cleans_uid_descendants_even_without_supervisor(manager, monkeypatch):
    from plugins._sandboxing.helpers import process
    metadata=_metadata(manager,'alpha');metadata['uid']=20001
    monkeypatch.setattr(manager,'_runtime_state',lambda *a:(None,'runtime not found'))
    killed=[];monkeypatch.setattr(process,'terminate_uid',lambda uid, timeout:killed.append(uid))
    manager._stop_runtime('alpha',metadata)
    assert killed == [20001]


def test_start_refuses_missing_snapshot(manager: SandboxManager, monkeypatch: pytest.MonkeyPatch) -> None:
    _metadata(manager, "alpha", status="stopped")
    monkeypatch.setattr(manager, "_runtime_state", lambda *args: (None, "container not found"))
    with pytest.raises(SandboxError, match="no valid restart snapshot"):
        manager.start("alpha")


def test_unsupported_legacy_snapshot_is_preserved(manager, monkeypatch):
    metadata=_metadata(manager,'alpha')
    snapshot=manager.config.instances_dir/'alpha'/ROOTFS_SNAPSHOT
    snapshot.write_bytes(b'last-good');metadata['rootfs_snapshot']=ROOTFS_SNAPSHOT
    manager._atomic_write_json(snapshot.parent/'metadata.json',metadata)
    monkeypatch.setattr(manager,'_runtime_state',lambda *a:({'status':'running'},None))
    with pytest.raises(SandboxError,match='migration'):manager.save('alpha')
    assert snapshot.read_bytes()==b'last-good'


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
    assert captured['argv'][-4:] == ['--', 'sh', '-c', 'exit 37']
    assert '--cwd' in captured['argv']
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
    assert command[-3:] == ['--', '/bin/bash', '--login']
    assert 'execute' in command


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
        return subprocess.CompletedProcess(args[0], 0, "A0-COW-2", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(manager, "_require_runtime_artifacts", lambda: __import__("plugins._sandboxing.helpers.bootstrap", fromlist=["ready"]).ready(manager.config.proot))
    manager.doctor()
    assert calls and all(call.get("shell", False) is False for call in calls)


def test_docker_image_contains_small_runtime_and_default_seccomp():
    root=Path(__file__).resolve().parents[1]
    dockerfile=(root/'Dockerfile').read_text()
    compose=(root/'docker/run/docker-compose.yml').read_text()
    assert '/tools/usr/local/bin/a0-proot /usr/local/bin/' in dockerfile
    assert 'gvisor' not in dockerfile and 'runsc' not in dockerfile
    assert 'privileged: false' in compose and 'init: true' not in compose
    assert 'unconfined' not in compose and 'cap_add' not in compose


def test_runtime_bootstrap_requires_access_probe_fix(tmp_path, monkeypatch):
    from plugins._sandboxing.helpers import bootstrap
    executable = tmp_path/'a0-proot'
    executable.touch()
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a[0],0,'A0-COW-1',''))
    assert not bootstrap.ready(executable)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a[0],0,'A0-COW-2',''))
    assert bootstrap.ready(executable)
