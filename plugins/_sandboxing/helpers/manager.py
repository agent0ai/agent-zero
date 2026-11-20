from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import fcntl
import json
import os
from os import chown as set_owner
import platform
import re
import shutil
import stat
import signal
import sys
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from helpers.sandbox_types import SandboxError, SandboxMount
from plugins._sandboxing.helpers.images import (
    SandboxImageError,
    SandboxImageInfo,
    SandboxImageManager,
    validate_digest,
)


from plugins._sandboxing.helpers import storage, bootstrap, process as processes

NetworkMode = Literal["host", "none"]
SandboxType = Literal["temporary", "permanent"]
SandboxStatus = Literal[
    "creating",
    "running",
    "stopped",
    "recoverable",
    "stale",
    "broken",
]

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
ROOTFS_SNAPSHOT = "rootfs-upper.tar"
SCHEMA_VERSION = 3
RUNTIME_DIR = Path('/run/a0-proot')
_ABSENT_MARKERS = (
    "file does not exist",
    "no such file",
    "not found",
    "container does not exist",
)
_PROTECTED_MOUNT_ROOTS = ("/proc", "/dev", "/sys", "/etc", "/shared")
_OWNERSHIP_KEYS = ("chat_id", "project_id", "agent_id", "plugin_id")


@dataclass(frozen=True, slots=True)
class SandboxConfig:
    proot: Path
    instances_dir: Path
    uid_registry: Path
    shared_dir: Path
    default_image: str
    temporary_lifetime_days: float = 7.0
    start_timeout: float = 8.0
    stop_timeout: float = 3.0
    exec_timeout: float = 600.0
    max_output_bytes: int = 1_048_576
    instance_id: str = ""
    user_dir: Path | None = None


@dataclass(frozen=True, slots=True)
class SandboxInfo:
    name: str
    status: SandboxStatus
    sandbox_type: SandboxType
    network: NetworkMode
    created_at: str
    last_used_at: str
    snapshot_at: str | None
    expires_at: str | None
    image_ref: str = ""
    image_digest: str = ""
    size_bytes: int | None = None
    mounts: tuple[SandboxMount, ...] = ()
    ownership: Mapping[str, str | None] = field(default_factory=dict)
    runtime_error: str | None = None
    instance_id: str = ""
    standalone: bool = False
    service: bool = False
    desired_running: bool = False
    disk_backed: bool = False


@dataclass(frozen=True, slots=True)
class ExecResult:
    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    output_truncated: bool = False


def validate_name(name: str) -> str:
    name = str(name or "")
    if not NAME_RE.fullmatch(name):
        raise SandboxError(
            f"invalid sandbox name {name!r}; expected {NAME_RE.pattern}"
        )
    return name


def runtime_is_absent(error: str | None) -> bool:
    if not error:
        return False
    lowered = error.lower()
    return any(marker in lowered for marker in _ABSENT_MARKERS)


def allocated_bytes(path: Path) -> int:
    total = 0
    seen: set[tuple[int, int]] = set()
    pending = [path]
    while pending:
        current = pending.pop()
        try:
            info = current.lstat()
        except OSError:
            continue
        identity = (info.st_dev, info.st_ino)
        if identity in seen:
            continue
        seen.add(identity)
        total += getattr(info, "st_blocks", (info.st_size + 511) // 512) * 512
        if stat.S_ISDIR(info.st_mode):
            with contextlib.suppress(OSError):
                pending.extend(current.iterdir())
    return total


class SandboxManager:
    """Manage copy-on-write PRoot sandboxes under separate Linux users."""

    def __init__(self, config: SandboxConfig, images: SandboxImageManager) -> None:
        self.config = self._validated_config(config)
        self.images = images
        image_cache = self.images.config.cache_dir.resolve(strict=False)
        instances = self.config.instances_dir.resolve(strict=False)
        shared = self.config.shared_dir.resolve(strict=False)
        if (
            image_cache == instances
            or image_cache in instances.parents
            or instances in image_cache.parents
        ):
            raise SandboxError("sandbox instances and image cache must be separate")
        if (
            image_cache == shared
            or image_cache in shared.parents
            or shared in image_cache.parents
        ):
            raise SandboxError("shared exchange and image cache must be separate")
        self._locks_guard = threading.Lock()
        self._locks: dict[str, threading.RLock] = {}
        self._child_pipes: dict[str, int] = {}
        self._launchers = {}

    @staticmethod
    def _validated_config(config: SandboxConfig) -> SandboxConfig:
        if config.instance_id and not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", config.instance_id):
            raise SandboxError("invalid Agent Zero instance ID")
        if config.user_dir is not None and not config.user_dir.is_absolute():
            raise SandboxError("user directory must be absolute")
        paths = {
            "proot": config.proot,
            "instances_dir": config.instances_dir,
            "uid_registry": config.uid_registry,
            "shared_dir": config.shared_dir,
        }
        for label, value in paths.items():
            if not value.is_absolute():
                raise SandboxError(f"{label} must be an absolute path: {value}")
        instances = config.instances_dir.resolve(strict=False)
        shared = config.shared_dir.resolve(strict=False)
        if instances == shared or instances in shared.parents or shared in instances.parents:
            raise SandboxError("private sandbox state and shared exchange must be separate")
        if config.temporary_lifetime_days <= 0:
            raise SandboxError("temporary_lifetime_days must be positive")
        if config.max_output_bytes < 4096:
            raise SandboxError("max_output_bytes must be at least 4096")
        return config

    def doctor(self) -> list[str]:
        diagnostics = []
        if platform.system() != 'Linux' or os.geteuid() != 0:
            diagnostics.append('ERROR: PRoot sandboxes need Linux and a root manager for separate guest UIDs; Docker supplies this')
        try:
            self._require_runtime_artifacts()
            diagnostics.append('OK: PRoot copy-on-write runtime; no FUSE, mount capability or user namespaces required')
        except SandboxError as exc:
            diagnostics.append('ERROR: ' + str(exc))
        diagnostics.extend(self.images.doctor())
        return diagnostics

    def list(self) -> list[SandboxInfo]:
        self._ensure_layout()
        results: list[SandboxInfo] = []
        with self._index_lock(exclusive=False):
            for entry in sorted(self.config.instances_dir.iterdir(), key=lambda p: p.name):
                if entry.is_symlink() or not entry.is_dir() or not NAME_RE.fullmatch(entry.name):
                    continue
                try:
                    results.append(self.inspect(entry.name))
                except SandboxError as exc:
                    results.append(self._broken_info(entry.name, str(exc)))
        return results

    def is_running(self, name: str) -> bool:
        """Check liveness without scanning the guest filesystem for disk usage."""
        name = validate_name(name)
        state, _ = self._runtime_state(name, self._read_metadata(name))
        return bool(state and state.get("status") == "running")

    def disk_usage(self, name: str) -> int:
        """Measure on explicit request, without holding lifecycle locks."""
        name = validate_name(name)
        path = self._instance_path(name)
        if path.is_symlink() or not path.is_dir():
            raise SandboxError(f"sandbox {name!r} does not exist")
        self._read_metadata(name)
        return storage.private_bytes(path, self._read_metadata(name).get('uid'))

    def inspect(self, name: str) -> SandboxInfo:
        name = validate_name(name)
        path = self._instance_path(name)
        if not path.exists() or path.is_symlink() or not path.is_dir():
            raise SandboxError(f"sandbox {name!r} does not exist")
        try:
            metadata = self._read_metadata(name)
        except SandboxError as exc:
            return self._broken_info(name, str(exc))
        state, error = self._runtime_state(name, metadata)
        snapshot = self._valid_snapshot(name, metadata)
        if state is not None:
            observed = str(state.get("status") or "")
            if observed == "running":
                status: SandboxStatus = "running"
            elif observed == "stopped":
                status = "stopped"
            elif observed in {"created", "creating"}:
                status = "creating"
            else:
                status = "broken"
                error = f"unexpected runtime status {observed!r}"
        elif runtime_is_absent(error):
            if snapshot is None and not self._disk_root(name, metadata):
                status = "stale"
            elif metadata.get("last_known_status") == "stopped":
                status = "stopped"
            else:
                status = "recoverable"
        else:
            status = "broken"
        image_error: str | None = None
        if status != "running":
            try:
                self.images.inspect(str(metadata.get("image_digest") or ""))
            except SandboxImageError as exc:
                image_error = f"base image will be restored on start: {exc}"
                if status not in {"stopped", "recoverable"}:
                    status = "broken"
        return self._info(
            name,
            metadata,
            status,
            image_error or (error if status == "broken" else None),
        )

    def create(
        self,
        name: str,
        *,
        network: NetworkMode = "host",
        sandbox_type: SandboxType = "temporary",
        image: str = "",
        mounts: Sequence[SandboxMount | Mapping[str, Any]] = (),
        ownership: Mapping[str, str | None] | None = None,
        standalone: bool = False,
        service: bool = False,
        share_usr: bool = True,
        host_root: bool = False,
        command: Sequence[str] = (),
    ) -> SandboxInfo:
        name = validate_name(name)
        network = self._validate_network(network)
        sandbox_type = self._validate_type(sandbox_type)
        requested_mounts = list(mounts)
        if share_usr and self.config.user_dir is not None:
            self.config.user_dir.mkdir(parents=True, exist_ok=True)
            requested_mounts.append(SandboxMount(self.config.user_dir, "/a0/usr", False))
        if host_root:
            raise SandboxError("Host-root bindings are unavailable with PRoot; use explicit directories")
        normalized_mounts = self._normalize_mounts(requested_mounts)
        if not host_root and any(m.source == Path("/") for m in normalized_mounts):
            raise SandboxError("mounting the host root requires host_root=True")
        command = self._validate_command(command)
        normalized_owner = self._normalize_ownership(ownership)
        self._ensure_layout()
        with self._index_lock(exclusive=False):
            path = self._instance_path(name)
            if path.exists() or path.is_symlink():
                raise SandboxError(f"sandbox {name!r} already exists")
        bootstrap.ensure(self.config.proot)
        self._require_runtime_artifacts()
        try:
            image_info = self.images.ensure(image or self.config.default_image)
        except SandboxImageError as exc:
            raise SandboxError(str(exc)) from exc
        self._ensure_shared_directory()

        with self._name_thread_lock(name), self._index_lock(exclusive=True):
            try:
                image_info = self.images.ensure(
                    image_info.reference, digest=image_info.digest
                )
            except SandboxImageError as exc:
                raise SandboxError(str(exc)) from exc
            path = self._instance_path(name)
            if path.exists() or path.is_symlink():
                raise SandboxError(f"sandbox {name!r} already exists")
            bundle = path / "bundle"
            logs = path / "logs"
            for directory in (path, bundle, logs):
                directory.mkdir(mode=0o700)
            (path / ".lock").touch(mode=0o600, exist_ok=True)
            now = self._now()
            metadata: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "instance_id": self.config.instance_id,
                "filesystem": "cow",
                "managed_workspace": self.config.user_dir is not None and not any(
                    mount.destination == "/workspace" for mount in normalized_mounts
                ),
                "uid": storage.lease_uid(self.config.uid_registry, path),
                "standalone": bool(standalone),
                "service": bool(service),
                "desired_running": True,
                "command": command,
                "host_root": bool(host_root),
                "name": name,
                "sandbox_type": sandbox_type,
                "network": network,
                "created_at": now,
                "last_used_at": now,
                "snapshot_at": None,
                "rootfs_snapshot": None,
                "image_ref": image_info.reference,
                "image_digest": image_info.digest,
                "launch_mode": "starting",
                "launcher_pid": None,
                "last_known_status": "creating",
                "mounts": [self._mount_json(mount) for mount in normalized_mounts],
                "ownership": normalized_owner,
            }
            try:
                storage.ensure_base(image_info.rootfs)
                storage.prepare(image_info.rootfs, path / 'fs', path / 'cow', metadata['uid'])
                if not self._disk_root(name, metadata):
                    raise SandboxError("failed to prepare writable sandbox filesystem")
                self._refresh_bundle(name, metadata, workspace_seed=image_info.rootfs / "workspace")
                self._atomic_write_json(path / "metadata.json", metadata)
                self._launch(name, metadata)
                self._save_locked(name, metadata)
                return self.inspect(name)
            except BaseException:
                cleaned = self._force_runtime_delete(name, metadata)
                if cleaned and path.exists() and not path.is_symlink():
                    shutil.rmtree(path)
                elif not cleaned:
                    self._append_log(
                        path / "logs" / "launcher.log",
                        "runtime cleanup was not confirmed; preserving state for diagnosis",
                    )
                raise

    def ensure_running(
        self,
        name: str,
        *,
        network: NetworkMode = "host",
        sandbox_type: SandboxType = "temporary",
        image: str = "",
    ) -> SandboxInfo:
        name = validate_name(name)
        path = self._instance_path(name)
        if not path.exists() and not path.is_symlink():
            return self.create(
                name,
                network=network,
                sandbox_type=sandbox_type,
                image=image,
            )
        info = self.inspect(name)
        if info.status == "running":
            self.touch(name)
            return self.inspect(name)
        if info.status in {"stopped", "recoverable"}:
            return self.start(name)
        raise SandboxError(
            f"sandbox {name!r} cannot be started automatically from status {info.status!r}"
        )

    def exec(
        self,
        name: str,
        argv: Sequence[str],
        *,
        cwd: str = "/workspace",
        timeout: float | None = None,
    ) -> ExecResult:
        name = validate_name(name)
        args = tuple(str(item) for item in argv)
        if not args or not args[0]:
            raise SandboxError("exec requires a non-empty argv")
        cwd = self._validate_guest_path(cwd, label="cwd")
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            self._require_running(name, metadata)
            command = self._process_command(name, metadata, args, cwd)
            result = self._run_captured(
                command,
                timeout=self.config.exec_timeout if timeout is None else timeout,
                operation=f"execute in sandbox {name!r}",
            )
            self._touch_locked(name, metadata)
            return ExecResult(
                argv=args,
                exit_code=result[0],
                stdout=result[1],
                stderr=result[2],
                output_truncated=result[3],
            )

    def bash(
        self,
        name: str,
        script: str,
        *,
        cwd: str = "/workspace",
        timeout: float | None = None,
    ) -> ExecResult:
        return self.exec(
            name,
            ["/bin/bash", "-lc", str(script)],
            cwd=cwd,
            timeout=timeout,
        )

    def set_mounts(self, name: str, mounts: Sequence[SandboxMount]) -> None:
        """Update explicit binds of a stopped service, preserving its disk root."""
        normalized = self._normalize_mounts(mounts)
        if any(m.source == Path('/') for m in normalized):
            raise SandboxError('Host root must be explicitly enabled at creation')
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            state, _ = self._runtime_state(name, metadata)
            if state and state.get('status') != 'stopped':
                raise SandboxError('Stop the sandbox before changing mounts')
            workspace = self._managed_workspace(name, metadata)
            metadata['mounts'] = [
                self._mount_json(mount) for mount in normalized
                if workspace is None or mount != SandboxMount(workspace, "/workspace", False)
            ]
            self._atomic_write_json(self._instance_path(name) / 'metadata.json', metadata)

    def process_command(
        self, name: str, argv: Sequence[str], *, cwd: str = "/workspace", agent_only: bool = False,
    ) -> list[str]:
        """Validated argv for an administrative caller that owns subprocess pipes/lifetime."""
        args = self._validate_command(argv)
        if not args:
            raise SandboxError("exec requires a non-empty argv")
        cwd = self._validate_guest_path(cwd, label="cwd")
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            if agent_only and metadata.get("service"):
                raise SandboxError("Plugin service sandboxes are not agent destinations")
            self._require_running(name, metadata)
            self._touch_locked(name, metadata)
            return self._process_command(name, metadata, args, cwd)

    def interactive_command(self, name, *, cwd='/workspace'):
        return self.process_command(name, ['/bin/bash', '--login'], cwd=cwd)

    def save(self, name: str) -> SandboxInfo:
        name = validate_name(name)
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            self._require_running(name, metadata)
            self._save_locked(name, metadata)
            self._touch_locked(name, metadata)
        return self.inspect(name)

    def stop(self, name: str) -> SandboxInfo:
        name = validate_name(name)
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            state, error = self._runtime_state(name, metadata)
            snapshot = self._valid_snapshot(name, metadata)
            metadata["desired_running"] = False
            self._atomic_write_json(self._instance_path(name) / "metadata.json", metadata)
            if state is None:
                if runtime_is_absent(error) and (snapshot is not None or self._disk_root(name, metadata)):
                    metadata["last_known_status"] = "stopped"
                    self._atomic_write_json(
                        self._instance_path(name) / "metadata.json", metadata
                    )
                    return self.inspect(name)
                raise SandboxError(
                    f"cannot stop sandbox {name!r}: {error or 'runtime state is unknown'}"
                )
            status = state.get("status")
            if status == "running":
                self._save_locked(name, metadata)
                self._stop_runtime(name, metadata)
            elif status != "stopped":
                raise SandboxError(f"cannot stop sandbox {name!r} from status {status!r}")
            elif snapshot is None and not self._disk_root(name, metadata):
                raise SandboxError(
                    f"sandbox {name!r} is stopped but has no restartable snapshot"
                )
            if not self._force_runtime_delete(name, metadata):
                raise SandboxError(
                    f"sandbox {name!r} stopped but runtime cleanup was not confirmed"
                )
            metadata["last_used_at"] = self._now()
            metadata["last_known_status"] = "stopped"
            self._atomic_write_json(self._instance_path(name) / "metadata.json", metadata)
        return self.inspect(name)

    def start(self, name: str) -> SandboxInfo:
        name = validate_name(name)
        bootstrap.ensure(self.config.proot)
        self._require_runtime_artifacts()
        self._ensure_shared_directory()
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            metadata["desired_running"] = True
            try:
                self.images.ensure(
                    str(metadata.get("image_ref") or ""),
                    digest=str(metadata.get("image_digest") or ""),
                )
            except SandboxImageError as exc:
                raise SandboxError(
                    f"cannot restore pinned base image for {name!r}: {exc}"
                ) from exc
            state, error = self._runtime_state(name, metadata)
            if state is not None and state.get("status") == "running":
                self._touch_locked(name, metadata)
                return self.inspect(name)
            if state is not None:
                if not self._force_runtime_delete(name, metadata):
                    raise SandboxError(f"could not clear stopped runtime for {name!r}")
            elif error and not runtime_is_absent(error):
                raise SandboxError(f"cannot determine runtime state for {name!r}: {error}")
            snapshot = self._valid_snapshot(name, metadata)
            if snapshot is None and not self._disk_root(name, metadata):
                raise SandboxError(f"sandbox {name!r} has no valid restart snapshot or disk filesystem")
            self._refresh_bundle(name, metadata, snapshot=snapshot)
            self._launch(name, metadata)
            self._touch_locked(name, metadata)
        return self.inspect(name)

    def restart(self, name: str) -> SandboxInfo:
        self.stop(name)
        return self.start(name)

    def set_command(self, name: str, command: Sequence[str]) -> None:
        """Set the next boot command; stop the sandbox before changing it."""
        command = self._validate_command(command)
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            state, error = self._runtime_state(name, metadata)
            if state and state.get("status") != "stopped":
                raise SandboxError("stop the sandbox before setting its command")
            if state is None and not runtime_is_absent(error):
                raise SandboxError("cannot determine sandbox state")
            metadata["command"] = command
            self._atomic_write_json(self._instance_path(name) / "metadata.json", metadata)

    def restore_standalone(self) -> list[str]:
        restored = []
        for info in self.list():
            if info.standalone and info.desired_running and info.status in {"stopped", "recoverable"}:
                self.start(info.name)
                restored.append(info.name)
        return restored

    @contextlib.contextmanager
    def open_browse_root(self, name: str, created_at: str, *, workspace: bool = False) -> Iterator[int]:
        """Pin the validated sandbox root before releasing the lifecycle index lock."""
        with self._index_lock(exclusive=False):
            metadata = self._read_metadata(validate_name(name))
            if metadata.get("service") or metadata["created_at"] != created_at:
                raise SandboxError("Sandbox files are no longer available.")
            root = self._disk_root(name, metadata)
            if root is None:
                raise SandboxError("Sandbox files need a persistent disk filesystem.")
            data = self._managed_workspace(name, metadata) if workspace else None
            fd = storage.open_directory(data or (root / "workspace" if workspace else root))
        try:
            yield fd
        finally:
            os.close(fd)

    def read_file(self, name: str, relative: str, *, limit: int = 65536) -> str:
        """Read bounded service output without spawning an exec process."""
        metadata = self._read_metadata(validate_name(name))
        root = self._disk_root(name, metadata)
        if root is None:
            raise SandboxError("direct reads require a disk-backed sandbox")
        parts = PurePosixPath(relative).parts
        if not parts or relative.startswith("/") or any(p in {".", ".."} for p in parts):
            raise SandboxError("invalid sandbox file path")
        # Open each component without following guest-controlled symlinks.
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            target = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            with os.fdopen(target, "rb") as handle:
                import stat
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise SandboxError("sandbox output must be a regular file")
                handle.seek(max(0, os.fstat(handle.fileno()).st_size - limit))
                return handle.read(limit).decode("utf-8", errors="replace")
        finally:
            os.close(fd)

    def delete(self, name: str, *, missing_ok: bool = False) -> bool:
        name = validate_name(name)
        self._ensure_layout()
        with self._name_thread_lock(name), self._index_lock(exclusive=True):
            path = self._instance_path(name)
            if not path.exists() and not path.is_symlink():
                if missing_ok:
                    return False
                raise SandboxError(f"sandbox {name!r} does not exist")
            if path.is_symlink() or not path.is_dir():
                raise SandboxError(f"refusing to delete unsafe sandbox entry {path}")
            with self._file_lock(path / ".lock"):
                metadata = self._read_metadata(name)
                self._delete_locked(name, path, metadata)
            return True

    def touch(self, name: str) -> None:
        name = validate_name(name)
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            self._touch_locked(name, metadata)

    def cleanup_expired(self, *, now: dt.datetime | None = None) -> list[str]:
        current = now or dt.datetime.now(dt.timezone.utc)
        deleted: list[str] = []
        for info in self.list():
            if info.sandbox_type != "temporary" or not info.expires_at:
                continue
            try:
                expires = dt.datetime.fromisoformat(info.expires_at)
            except ValueError:
                continue
            if expires <= current and self._delete_if_expired(info.name, current):
                deleted.append(info.name)
        return deleted

    def list_images(self) -> list[SandboxImageInfo]:
        usage = self._image_usage()
        try:
            images = self.images.list()
        except SandboxImageError as exc:
            raise SandboxError(str(exc)) from exc
        return [
            dataclasses.replace(info, used_by=tuple(sorted(usage.get(info.digest, ()))))
            for info in images
        ]

    def inspect_image(self, identifier: str) -> SandboxImageInfo:
        try:
            info = self.images.inspect(identifier)
        except SandboxImageError as exc:
            raise SandboxError(str(exc)) from exc
        usage = self._image_usage()
        return dataclasses.replace(
            info, used_by=tuple(sorted(usage.get(info.digest, ())))
        )

    def pull_image(self, reference: str = "") -> SandboxImageInfo:
        try:
            info = self.images.pull(reference or self.config.default_image)
        except SandboxImageError as exc:
            raise SandboxError(str(exc)) from exc
        return dataclasses.replace(
            info, used_by=tuple(sorted(self._image_usage().get(info.digest, ())))
        )

    def delete_image(self, identifier: str, *, missing_ok: bool = False) -> bool:
        try:
            digest = validate_digest(identifier)
        except SandboxImageError:
            try:
                digest = self.images.inspect(identifier).digest
            except SandboxImageError as inspect_exc:
                if missing_ok:
                    return False
                raise SandboxError(str(inspect_exc)) from inspect_exc
        with self._index_lock(exclusive=True):
            usage = self._image_usage_locked(strict=True)
            referenced = sorted(usage.get(digest, ()))
            if referenced:
                raise SandboxError(
                    f"image {digest} is still used by sandboxes: {', '.join(referenced)}"
                )
            try:
                return self.images.delete(digest, missing_ok=missing_ok)
            except SandboxImageError as exc:
                raise SandboxError(str(exc)) from exc

    def cleanup_images(self, *, now: dt.datetime | None = None) -> list[str]:
        with self._index_lock(exclusive=True):
            used = set(self._image_usage_locked(strict=True))
            try:
                return self.images.cleanup(used_digests=used, now=now)
            except SandboxImageError as exc:
                raise SandboxError(str(exc)) from exc

    def _image_usage(self) -> dict[str, set[str]]:
        with self._index_lock(exclusive=False):
            return self._image_usage_locked()

    def _image_usage_locked(self, *, strict: bool = False) -> dict[str, set[str]]:
        usage: dict[str, set[str]] = {}
        current = self.config.instances_dir
        if not current.exists():
            return usage
        entries = current.iterdir()
        if strict and current.parent.name == "instances" and current.name == self.config.instance_id:
            # Image eviction shares the index lock across instances using this store.
            entries = (
                guest for instance in current.parent.iterdir()
                if not instance.is_symlink() and instance.is_dir()
                for guest in instance.iterdir()
            )
        for entry in entries:
            if entry.is_symlink() or not entry.is_dir() or not NAME_RE.fullmatch(entry.name):
                continue
            metadata_path = entry / "metadata.json"
            if metadata_path.is_symlink() or not metadata_path.is_file():
                if strict:
                    raise SandboxError(
                        f"cannot safely determine image use for sandbox {entry.name!r}"
                    )
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                if not isinstance(metadata, dict):
                    raise ValueError("metadata is not an object")
                digest = validate_digest(str(metadata.get("image_digest") or ""))
            except (OSError, json.JSONDecodeError, SandboxImageError, ValueError) as exc:
                if strict:
                    raise SandboxError(
                        f"cannot safely determine image use for sandbox {entry.name!r}: {exc}"
                    ) from exc
                continue
            owner = entry.name if entry.parent == current else "another Agent Zero instance"
            usage.setdefault(digest, set()).add(owner)
        return usage

    def _delete_if_expired(self, name: str, now: dt.datetime) -> bool:
        """Recheck expiry while holding the same locks as execution and deletion."""
        name = validate_name(name)
        self._ensure_layout()
        with self._name_thread_lock(name), self._index_lock(exclusive=True):
            path = self._instance_path(name)
            if not path.exists() and not path.is_symlink():
                return False
            if path.is_symlink() or not path.is_dir():
                raise SandboxError(f"refusing to delete unsafe sandbox entry {path}")
            with self._file_lock(path / ".lock"):
                metadata = self._read_metadata(name)
                if self._validate_type(metadata.get("sandbox_type")) != "temporary":
                    return False
                expires_at = self._expiry(str(metadata.get("last_used_at") or ""))
                if not expires_at:
                    return False
                try:
                    expires = dt.datetime.fromisoformat(expires_at)
                except ValueError:
                    return False
                if expires > now:
                    return False
                self._delete_locked(name, path, metadata)
                return True

    def _delete_locked(
        self, name: str, path: Path, metadata: Mapping[str, Any]
    ) -> None:
        state, error = self._runtime_state(name, metadata)
        if state is not None:
            self._stop_runtime(name, metadata)
        elif error and not runtime_is_absent(error):
            raise SandboxError(
                f"cannot safely determine runtime state for {name!r}: {error}"
            )
        if not self._force_runtime_delete(name, metadata):
            raise SandboxError(f"runtime could not delete sandbox {name!r}")
        shutil.rmtree(path)
        self._fsync_directory(self.config.instances_dir)



    def _validated_metadata(self, name: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise SandboxError(f"sandbox {name!r} metadata is not an object")
        if value.get("schema_version") not in {2, SCHEMA_VERSION} or value.get("name") != name:
            raise SandboxError(f"sandbox {name!r} has incompatible metadata")
        owner = value.get("instance_id", "")
        if owner and owner != self.config.instance_id:
            raise SandboxError("sandbox belongs to another Agent Zero instance")
        self._validate_command(value.get("command", []))
        self._validate_network(value.get("network"))
        self._validate_type(value.get("sandbox_type"))
        for key in ("created_at", "last_used_at"):
            self._parse_timestamp(value.get(key), key)
        image_ref = str(value.get("image_ref") or "").strip()
        if not image_ref:
            raise SandboxError(f"sandbox {name!r} has no base image reference")
        try:
            value["image_digest"] = validate_digest(
                str(value.get("image_digest") or "")
            )
        except SandboxImageError as exc:
            raise SandboxError(f"sandbox {name!r} has invalid image metadata: {exc}") from exc
        if value.get('schema_version') == SCHEMA_VERSION:
            uid = value.get('uid')
            if not isinstance(uid, int) or not 20000 <= uid < 60000:
                raise SandboxError('Invalid sandbox UID')
            lease = self.config.uid_registry / str(uid)
            if not lease.is_file() or lease.read_text() != str(self._instance_path(name)):
                raise SandboxError('Sandbox UID reservation is missing or belongs to another sandbox')
        mounts = value.get("mounts", [])
        if not isinstance(mounts, list):
            raise SandboxError(f"sandbox {name!r} has invalid mount metadata")
        self._normalize_mounts(mounts, allow_missing=value.get("service") is True)
        value["ownership"] = self._normalize_ownership(value.get("ownership"))
        return value

    def _read_metadata(self, name: str) -> dict[str, Any]:
        path = self._instance_path(name)
        if path.is_symlink() or not path.is_dir():
            raise SandboxError(f"sandbox {name!r} has an unsafe instance path")
        metadata_path = path / "metadata.json"
        if metadata_path.is_symlink():
            raise SandboxError(f"sandbox {name!r} metadata must not be a symlink")
        try:
            with metadata_path.open(encoding="utf-8") as handle:
                value = json.load(handle)
        except FileNotFoundError as exc:
            raise SandboxError(f"sandbox {name!r} does not exist") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise SandboxError(f"cannot read metadata for {name!r}: {exc}") from exc
        return self._validated_metadata(name, value)

    def _info(
        self,
        name: str,
        metadata: Mapping[str, Any],
        status: SandboxStatus,
        runtime_error: str | None,
    ) -> SandboxInfo:
        mounts = self._normalize_mounts(metadata.get("mounts", []), allow_missing=metadata.get("service") is True)
        workspace = self._managed_workspace(name, metadata)
        if workspace is not None:
            mounts = (SandboxMount(workspace, "/workspace", False), *mounts)
        last_used = str(metadata.get("last_used_at") or metadata.get("created_at") or "")
        sandbox_type = self._validate_type(metadata.get("sandbox_type"))
        expires = self._expiry(last_used) if sandbox_type == "temporary" else None
        return SandboxInfo(
            name=name,
            status=status,
            sandbox_type=sandbox_type,
            network=self._validate_network(metadata.get("network")),
            created_at=str(metadata.get("created_at") or ""),
            last_used_at=last_used,
            snapshot_at=str(metadata.get("snapshot_at")) if metadata.get("snapshot_at") else None,
            expires_at=expires,
            image_ref=str(metadata.get("image_ref") or ""),
            image_digest=str(metadata.get("image_digest") or ""),
            mounts=mounts,
            ownership=dict(self._normalize_ownership(metadata.get("ownership"))),
            runtime_error=runtime_error,
            instance_id=str(metadata.get("instance_id") or ""),
            standalone=bool(metadata.get("standalone", True)),
            service=bool(metadata.get("service", False)),
            desired_running=bool(metadata.get("desired_running", False)),
            disk_backed=metadata.get("filesystem") in {"disk", "cow"},
        )

    def _broken_info(self, name: str, error: str) -> SandboxInfo:
        return SandboxInfo(
            name=name,
            status="broken",
            sandbox_type="temporary",
            network="host",
            created_at="",
            last_used_at="",
            snapshot_at=None,
            expires_at=None,
            image_ref="",
            image_digest="",
            ownership={key: None for key in _OWNERSHIP_KEYS},
            runtime_error=error,
        )

    def _runtime_state(self, name, metadata):
        if metadata.get('schema_version') == 2:
            return None, 'legacy runtime not found; filesystem will migrate on start'
        state_path = self._instance_path(name) / 'bundle/state.json'
        try:
            state = json.loads(state_path.read_text())
            if processes.alive(state):
                return {**state, 'status': 'running'}, None
            if state.get('status') == 'stopped':
                return state, None
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            return None, str(exc)
        return None, 'runtime not found'



    def _managed_workspace(self, name, metadata) -> Path | None:
        if not metadata.get("managed_workspace") or self.config.user_dir is None:
            return None
        if any(mount["destination"] == "/workspace" for mount in metadata.get("mounts", [])):
            return None
        return self.config.user_dir / "sandbox_data" / name / "workspace"

    def _refresh_bundle(self, name, metadata, *, snapshot=None, workspace_seed=None):
        path = self._instance_path(name)
        root = self._disk_root(name, metadata)
        if root is None:
            raise SandboxError('Legacy overlay snapshots must be exported with the previous version; original data is preserved')
        if metadata.get('schema_version') == 2:
            for proc in Path('/proc').iterdir():
                if not proc.name.isdigit():
                    continue
                try:
                    command = (proc / 'cmdline').read_bytes()
                except OSError:
                    continue
                if b'runsc' in command and str(path).encode() in command:
                    raise SandboxError('Stop the previous sandbox runtime or restart the container before migration')
            metadata['uid'] = storage.lease_uid(self.config.uid_registry, path)
            storage.adopt(root, path / 'cow', metadata['uid'])
            metadata.update(schema_version=SCHEMA_VERSION, filesystem='cow')
            self._atomic_write_json(path / 'metadata.json', metadata)
        uid = metadata['uid']
        bundle = path / 'bundle'
        bundle.mkdir(mode=0o700, exist_ok=True)
        bindings = [('/proc', '/proc'), ('/dev', '/dev')]
        readonly = []
        # Unix socket paths must fit 108 bytes even under deeply nested user storage.
        runtime_dir = RUNTIME_DIR / str(uid)
        runtime_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        set_owner(runtime_dir, uid, uid)
        storage.traverse(runtime_dir, uid)
        for target in ('tmp', 'run', 'trace'):
            scratch = runtime_dir / target
            scratch.mkdir(mode=0o700, exist_ok=True)
            set_owner(scratch, uid, uid)
            if target != 'trace':
                bindings.append((str(scratch), '/' + target))
        for source, target in ((Path('/etc/resolv.conf'), 'resolv.conf'), (Path('/etc/hosts'), 'hosts')):
            self._atomic_write_text(bundle / target, source.read_text(), mode=0o644)
            bindings.append((str(bundle / target), '/etc/' + target))
            readonly.append(str(bundle / target))
        private = (self.config.instances_dir.parent, self.images.config.cache_dir, self.config.uid_registry)
        mounts = list(self._normalize_mounts(metadata.get('mounts', [])))
        if self.config.user_dir is not None:
            data_root = self.config.user_dir / "sandbox_data"
            private += (data_root,)
            if "managed_workspace" in metadata:
                workspace = self._managed_workspace(name, metadata)
                if workspace is None:
                    storage.prepare_workspace(data_root / name)
                else:
                    storage.prepare_workspace(workspace, workspace_seed)
                    mounts.insert(0, SandboxMount(workspace, "/workspace", False))
                storage.link_sandbox_data(path / "data", data_root / name)
        if metadata.get('service'):
            shared = path / 'shared'
            shared.mkdir(mode=0o700, exist_ok=True)
            set_owner(shared, uid, uid)
        else:
            shared = self.config.shared_dir
            storage.grant(shared, uid, writable=True, exclude=private)
        bindings.append((str(shared), '/shared'))
        for item in mounts:
            if item.source == Path('/'):
                raise SandboxError('Host-root bindings are unavailable with PRoot; use explicit directories')
            storage.grant(item.source, uid, writable=not item.read_only,
                          exclude=[p for p in private if p == item.source or item.source in p.parents])
            bindings.append((str(item.source), item.destination))
            if item.read_only:
                readonly.append(str(item.source))
            # Hide manager state even inside a broad user-directory binding.
            for hidden in private:
                try:
                    relative = hidden.relative_to(item.source)
                except ValueError:
                    continue
                empty = path / 'masked' / str(len(bindings))
                empty.mkdir(parents=True, mode=0o700, exist_ok=True)
                set_owner(empty, uid, uid)
                bindings.append((str(empty), str(PurePosixPath(item.destination) / relative)))
                readonly.append(str(empty))
        storage.traverse(root, uid)
        storage.traverse(path / 'cow', uid)
        storage.traverse(bundle, uid)
        temp = runtime_dir / 'trace'
        image = self.images.inspect(metadata['image_digest'])
        environment = dict(value.split('=', 1) for value in image.environment if '=' in value)
        environment.update(HOME='/root', LANG=environment.get('LANG', 'C.UTF-8'), TERM='xterm-256color',
                           PAGER='cat', GIT_PAGER='cat', PIP_DISABLE_PIP_VERSION_CHECK='1',
                           PIP_NO_CACHE_DIR='1', PIP_ROOT_USER_ACTION='ignore', PYTHONDONTWRITEBYTECODE='1',
                           A0_INSTANCE_ID=str(metadata.get('instance_id') or ''))
        environment.setdefault('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')
        command = self._validate_command(metadata.get('command', [])) or ['/bin/sh', '-c', 'while :; do sleep 3600; done']
        config = dict(uid=uid, proot=str(self.config.proot), root=str(root), control=str(path / 'cow'),
                      temp=str(temp), bindings=bindings, readonly=readonly, network=metadata['network'],
                      cwd='/workspace', command=command, environment=environment)
        self._atomic_write_json(bundle / 'config.json', config)

    def _launch(self, name: str, metadata: dict[str, Any]) -> None:
        read_fd = write_fd = None
        if not metadata.get("standalone", True):
            read_fd, write_fd = os.pipe()
        try:
            self._launch_runtime(name, metadata, read_fd)
            if write_fd is not None:
                old = self._child_pipes.pop(name, None)
                if old is not None:
                    os.close(old)
                self._child_pipes[name] = write_fd
                write_fd = None
        finally:
            if read_fd is not None:
                os.close(read_fd)
            if write_fd is not None:
                os.close(write_fd)

    def _launch_runtime(self, name, metadata, read_fd):
        path = self._instance_path(name)
        (path / 'bundle/state.json').unlink(missing_ok=True)
        command = [sys.executable, str(Path(processes.__file__))]
        if read_fd is not None:
            command += ['--owner-fd', str(read_fd)]
        command += ['supervise', str(path / 'bundle/config.json')]
        with (path / 'logs/launcher.log').open('ab', buffering=0) as output:
            launcher = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                        stderr=subprocess.STDOUT, start_new_session=True,
                                        pass_fds=(read_fd,) if read_fd is not None else ())
        metadata.update(launcher_pid=launcher.pid, launch_mode='proot', last_known_status='running')
        self._atomic_write_json(path / 'metadata.json', metadata)
        state, error = self._wait_for_status(name, metadata, {'running', 'stopped'}, self.config.start_timeout, launcher=launcher)
        if not state:
            launcher.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                launcher.wait(timeout=3)
            raise SandboxError(f"sandbox {name!r} failed to start: {error}; {self._log_tail(path / 'logs/launcher.log')}")
        metadata['last_known_status'] = state['status']
        self._atomic_write_json(path / 'metadata.json', metadata)
        self._launchers[name] = launcher

    def _save_locked(self, name, metadata):
        if not self._disk_root(name, metadata):
            raise SandboxError('This sandbox needs filesystem migration before use')

    def _stop_runtime(self, name, metadata):
        state, _ = self._runtime_state(name, metadata)
        if state and processes.alive(state):
            with contextlib.suppress(ProcessLookupError):
                os.kill(state['pid'], signal.SIGTERM)
        if metadata.get('uid'):
            processes.terminate_uid(metadata['uid'], self.config.stop_timeout)
        if state:
            deadline = time.monotonic() + self.config.stop_timeout + 2
            while processes.alive(state) and time.monotonic() < deadline:
                time.sleep(.05)
            if processes.alive(state):
                os.kill(state['pid'], signal.SIGKILL)
        launcher = self._launchers.pop(name, None)
        if launcher:
            with contextlib.suppress(subprocess.TimeoutExpired):
                launcher.wait(timeout=2)
        (self._instance_path(name) / 'bundle/state.json').unlink(missing_ok=True)
        if metadata.get('uid'):
            shutil.rmtree(RUNTIME_DIR / str(metadata['uid']), ignore_errors=True)

    def _force_runtime_delete(self, name, metadata):
        try:
            self._stop_runtime(name, metadata)
        except (OSError, RuntimeError) as exc:
            self._append_log(self._instance_path(name) / 'logs/launcher.log', str(exc))
            return False
        fd = self._child_pipes.pop(name, None)
        if fd is not None:
            os.close(fd)
        return True

    def _wait_for_status(
        self,
        name: str,
        metadata: Mapping[str, Any],
        wanted: set[str],
        timeout: float,
        *,
        launcher: subprocess.Popen[bytes] | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        deadline = time.monotonic() + timeout
        last_state: dict[str, Any] | None = None
        last_error: str | None = None
        while time.monotonic() < deadline:
            last_state, last_error = self._runtime_state(name, metadata)
            if last_state is not None and last_state.get("status") in wanted:
                return last_state, None
            if launcher is not None and launcher.poll() is not None:
                return last_state, f"PRoot launcher exited {launcher.returncode}"
            time.sleep(0.1)
        if last_state is not None:
            return last_state, f"last status was {last_state.get('status')!r}"
        return None, last_error or "runtime state did not appear"

    def _require_running(self, name: str, metadata: Mapping[str, Any]) -> None:
        state, error = self._runtime_state(name, metadata)
        if state is None or state.get("status") != "running":
            detail = error or f"status is {state.get('status') if state else 'unknown'}"
            raise SandboxError(f"sandbox {name!r} is not running: {detail}")

    def _run_captured(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        operation: str,
    ) -> tuple[int, str, str, bool]:
        if timeout <= 0:
            raise SandboxError("execution timeout must be positive")
        try:
            process = subprocess.Popen(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError as exc:
            raise SandboxError(f"could not {operation}: {exc}") from exc
        buffers = [bytearray(), bytearray()]
        truncated = [False, False]

        def drain(stream: Any, index: int) -> None:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    return
                remaining = self.config.max_output_bytes - len(buffers[index])
                if remaining > 0:
                    buffers[index].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated[index] = True

        threads = [
            threading.Thread(target=drain, args=(process.stdout, 0), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, 1), daemon=True),
        ]
        for thread in threads:
            thread.start()
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            for thread in threads:
                thread.join(timeout=1)
            raise SandboxError(f"timed out after {timeout:g}s while trying to {operation}") from exc
        for thread in threads:
            thread.join(timeout=2)
        stdout = bytes(buffers[0]).decode("utf-8", "replace")
        stderr = bytes(buffers[1]).decode("utf-8", "replace")
        if truncated[0]:
            stdout += "\n[output truncated by sandbox policy]\n"
        if truncated[1]:
            stderr += "\n[output truncated by sandbox policy]\n"
        return exit_code, stdout, stderr, any(truncated)

    def _valid_snapshot(self, name: str, metadata: Mapping[str, Any]) -> Path | None:
        if metadata.get("rootfs_snapshot") != ROOTFS_SNAPSHOT:
            return None
        snapshot = self._instance_path(name) / ROOTFS_SNAPSHOT
        if snapshot.is_symlink() or not snapshot.is_file():
            return None
        if snapshot.parent.resolve() != self._instance_path(name).resolve():
            return None
        return snapshot

    def _normalize_mounts(
        self, mounts: Sequence[SandboxMount | Mapping[str, Any]], *, allow_missing: bool = False
    ) -> tuple[SandboxMount, ...]:
        if isinstance(mounts, (str, bytes)) or not isinstance(mounts, Sequence):
            raise SandboxError("mounts must be a list")
        normalized: list[SandboxMount] = []
        destinations: set[str] = set()
        for raw in mounts:
            if isinstance(raw, SandboxMount):
                source = raw.source
                destination = raw.destination
                read_only = raw.read_only
            elif isinstance(raw, Mapping):
                source = Path(str(raw.get("source") or ""))
                destination = str(raw.get("destination") or "")
                read_only = self._as_bool(raw.get("read_only", True))
            else:
                raise SandboxError("each mount must be a SandboxMount or object")
            if any(c in str(source) + destination for c in ("\n", "\r", ":", "!")):
                raise SandboxError("unsupported character in binding path")
            if not source.is_absolute():
                raise SandboxError(f"mount source must be absolute: {source}")
            if source.is_symlink():
                raise SandboxError(f"mount source must not be a symlink: {source}")
            source = source.resolve(strict=False)
            if not source.is_dir() and (not allow_missing or source.exists()):
                raise SandboxError(f"mount source must be an existing non-symlink directory: {source}")
            destination = self._validate_guest_path(destination, label="mount destination")
            if any(
                destination == root or destination.startswith(root + "/")
                for root in _PROTECTED_MOUNT_ROOTS
            ):
                raise SandboxError(f"mount destination is reserved: {destination}")
            if destination in destinations:
                raise SandboxError(f"duplicate mount destination: {destination}")
            destinations.add(destination)
            normalized.append(SandboxMount(source, destination, read_only))
        return tuple(normalized)

    @staticmethod
    def _mount_json(mount: SandboxMount) -> dict[str, Any]:
        return {
            "source": str(mount.source),
            "destination": mount.destination,
            "read_only": mount.read_only,
        }

    @staticmethod
    def _normalize_ownership(
        ownership: Mapping[str, str | None] | None,
    ) -> dict[str, str | None]:
        raw = ownership if isinstance(ownership, Mapping) else {}
        result: dict[str, str | None] = {}
        for key in _OWNERSHIP_KEYS:
            value = raw.get(key)
            result[key] = str(value).strip()[:256] if value is not None and str(value).strip() else None
        return result

    @staticmethod
    def _validate_network(value: Any) -> NetworkMode:
        if value not in {"host", "none"}:
            raise SandboxError(f"unsupported network mode {value!r}")
        return value

    @staticmethod
    def _validate_type(value: Any) -> SandboxType:
        if value not in {"temporary", "permanent"}:
            raise SandboxError(f"unsupported sandbox type {value!r}")
        return value

    @staticmethod
    def _validate_guest_path(value: str, *, label: str) -> str:
        value = str(value or "")
        if "\x00" in value:
            raise SandboxError(f"{label} must not contain NUL bytes")
        path = PurePosixPath(value)
        normalized = str(path)
        if (
            not value.startswith("/")
            or value.startswith("//")
            or ".." in path.parts
            or value == "/"
            or normalized != value
        ):
            raise SandboxError(f"{label} must be an absolute sandbox path below /: {value!r}")
        return normalized

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _require_runtime_artifacts(self):
        if os.geteuid() != 0:
            raise SandboxError('The PRoot manager needs root to allocate separate Linux UIDs; use Docker')
        if not bootstrap.ready(self.config.proot):
            raise SandboxError(f'PRoot copy-on-write runtime not found at {self.config.proot}; rebuild the image or run docker/sandbox/proot/install.sh')
        if not shutil.which('setfacl'):
            raise SandboxError('Sandbox bindings need the acl package; rebuild the image or run the runtime installer')

    def _touch_locked(self, name: str, metadata: dict[str, Any]) -> None:
        metadata["last_used_at"] = self._now()
        self._atomic_write_json(self._instance_path(name) / "metadata.json", metadata)
        try:
            self.images.touch(str(metadata.get("image_digest") or ""))
        except SandboxImageError as exc:
            raise SandboxError(f"could not update base image usage: {exc}") from exc

    def _expiry(self, last_used_at: str) -> str | None:
        try:
            used = dt.datetime.fromisoformat(last_used_at)
        except ValueError:
            return None
        return (used + dt.timedelta(days=self.config.temporary_lifetime_days)).isoformat()

    @staticmethod
    def _parse_timestamp(value: Any, label: str) -> dt.datetime:
        if not isinstance(value, str):
            raise SandboxError(f"metadata {label} must be an ISO timestamp")
        try:
            parsed = dt.datetime.fromisoformat(value)
        except ValueError as exc:
            raise SandboxError(f"metadata {label} is invalid") from exc
        if parsed.tzinfo is None:
            raise SandboxError(f"metadata {label} must include a timezone")
        return parsed

    @staticmethod
    def _now() -> str:
        return dt.datetime.now(dt.timezone.utc).isoformat()

    @staticmethod
    def _validate_command(command: Sequence[str]) -> list[str]:
        if isinstance(command, (str, bytes)) or not isinstance(command, (list, tuple)):
            raise SandboxError("command must be an argument list")
        if any(not isinstance(arg, str) or "\0" in arg for arg in command):
            raise SandboxError("invalid command argument")
        if command and not command[0]:
            raise SandboxError("command executable must not be empty")
        return list(command)

    def _disk_root(self, name: str, metadata: Mapping[str, Any]) -> Path | None:
        if metadata.get("filesystem") not in {"disk", "cow"}:
            return None
        instance = self._instance_path(name)
        path = instance / "fs"
        if not os.path.lexists(path):
            path = instance / "rootfs"  # Previously created disk roots stay in place.
        if path.is_symlink() or not path.is_dir():
            raise SandboxError("sandbox disk filesystem is missing or unsafe")
        return path

    def _instance_path(self, name: str) -> Path:
        validate_name(name)
        path = self.config.instances_dir / name
        if path.parent != self.config.instances_dir:
            raise SandboxError("sandbox path escaped the instances directory")
        return path

    def _ensure_layout(self):
        for path in (self.config.instances_dir.parent, self.config.instances_dir):
            path.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _ensure_shared_directory(self) -> None:
        self.config.shared_dir.mkdir(mode=0o770, parents=True, exist_ok=True)
        if self.config.shared_dir.is_symlink() or not self.config.shared_dir.is_dir():
            raise SandboxError(f"shared path is not a safe directory: {self.config.shared_dir}")

    @contextlib.contextmanager
    def _name_thread_lock(self, name: str) -> Iterator[None]:
        with self._locks_guard:
            lock = self._locks.setdefault(name, threading.RLock())
        with lock:
            yield

    @contextlib.contextmanager
    def _operation_lock(self, name: str) -> Iterator[None]:
        with self._name_thread_lock(name):
            path = self._instance_path(name)
            if path.is_symlink() or not path.is_dir():
                raise SandboxError(f"sandbox {name!r} does not exist")
            with self._file_lock(path / ".lock"):
                yield

    @contextlib.contextmanager
    def _index_lock(self, *, exclusive: bool) -> Iterator[None]:
        self._ensure_layout()
        lock_path = self.config.instances_dir.parent / ".index.lock"
        with lock_path.open("a+", encoding="utf-8") as handle:
            with contextlib.suppress(PermissionError):
                os.fchmod(handle.fileno(), 0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    @contextlib.contextmanager
    def _file_lock(path: Path) -> Iterator[None]:
        if path.is_symlink():
            raise SandboxError(f"refusing symlink lock file {path}")
        with path.open("a+", encoding="utf-8") as handle:
            with contextlib.suppress(PermissionError):
                os.fchmod(handle.fileno(), 0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            SandboxManager._fsync_directory(path.parent)
        except BaseException:
            with contextlib.suppress(OSError):
                os.close(fd)
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _atomic_write_text(path: Path, content: str, *, mode: int) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            os.fchmod(fd, mode)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.close(fd)
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _atomic_probe(path: Path) -> None:
        fd, name = tempfile.mkstemp(prefix=".sandbox-doctor.", dir=path)
        temporary = Path(name)
        replacement = path / f"{temporary.name}.ok"
        try:
            os.write(fd, b"ok")
            os.fsync(fd)
            os.close(fd)
            fd = -1
            os.replace(temporary, replacement)
            SandboxManager._fsync_directory(path)
        finally:
            if fd >= 0:
                os.close(fd)
            temporary.unlink(missing_ok=True)
            replacement.unlink(missing_ok=True)

    @staticmethod
    def _append_log(path: Path, message: str) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message)
            if not message.endswith("\n"):
                handle.write("\n")

    @staticmethod
    def _log_tail(path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "(no log)"
        return "\n".join(content[-12000:].splitlines()[-40:])

    def _process_command(self, name, metadata, args, cwd='/workspace'):
        if metadata.get('service'):
            self._normalize_mounts(metadata.get('mounts', []))
        return [sys.executable, str(Path(processes.__file__)), '--cwd', cwd, 'execute',
                str(self._instance_path(name) / 'bundle/config.json'), '--', *args]

def sandbox_info_dict(info: SandboxInfo) -> dict[str, Any]:
    """Serialize public sandbox information for tools and HTTP APIs."""
    result = dataclasses.asdict(info)
    for mount in result.get("mounts", []):
        mount["source"] = str(mount.get("source") or "")
    return result
