from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import fcntl
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from plugins._sandboxing.helpers.images import (
    SandboxImageError,
    SandboxImageInfo,
    SandboxImageManager,
    validate_digest,
)


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
SCHEMA_VERSION = 2
CAPABILITIES = (
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_FOWNER",
    "CAP_FSETID",
    "CAP_KILL",
    "CAP_SETGID",
    "CAP_SETUID",
    "CAP_SETPCAP",
    "CAP_NET_BIND_SERVICE",
    "CAP_SYS_CHROOT",
    "CAP_MKNOD",
    "CAP_AUDIT_WRITE",
    "CAP_SETFCAP",
)
_ABSENT_MARKERS = (
    "file does not exist",
    "no such file",
    "not found",
    "container does not exist",
)
_PROTECTED_MOUNT_ROOTS = ("/proc", "/dev", "/sys", "/etc", "/shared")
_OWNERSHIP_KEYS = ("chat_id", "project_id", "agent_id")


class SandboxError(RuntimeError):
    """A safe, user-facing sandbox management error."""


@dataclass(frozen=True, slots=True)
class SandboxMount:
    source: Path
    destination: str
    read_only: bool = True


@dataclass(frozen=True, slots=True)
class SandboxConfig:
    runsc: Path
    instances_dir: Path
    runsc_root: Path
    shared_dir: Path
    default_image: str
    temporary_lifetime_days: float = 7.0
    start_timeout: float = 8.0
    stop_timeout: float = 3.0
    snapshot_timeout: float = 300.0
    exec_timeout: float = 600.0
    state_timeout: float = 3.0
    delete_timeout: float = 5.0
    max_output_bytes: int = 1_048_576


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
    size_bytes: int = 0
    mounts: tuple[SandboxMount, ...] = ()
    ownership: Mapping[str, str | None] = field(default_factory=dict)
    runtime_error: str | None = None


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
            stat = current.lstat()
        except OSError:
            continue
        identity = (stat.st_dev, stat.st_ino)
        if identity in seen:
            continue
        seen.add(identity)
        total += getattr(stat, "st_blocks", (stat.st_size + 511) // 512) * 512
        if current.is_dir() and not current.is_symlink():
            with contextlib.suppress(OSError):
                pending.extend(current.iterdir())
    return total


class SandboxManager:
    """Manage Agent Zero-owned OCI sandboxes directly through gVisor runsc."""

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

    @staticmethod
    def _validated_config(config: SandboxConfig) -> SandboxConfig:
        paths = {
            "runsc": config.runsc,
            "instances_dir": config.instances_dir,
            "runsc_root": config.runsc_root,
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
        diagnostics: list[str] = []
        if platform.system() != "Linux":
            diagnostics.append("ERROR: gVisor sandboxes require Linux")
        else:
            diagnostics.append(f"OK: Linux {platform.machine()}")

        if not self.config.runsc.is_file() or not os.access(self.config.runsc, os.X_OK):
            diagnostics.append(f"ERROR: runsc is not executable at {self.config.runsc}")
        else:
            try:
                result = subprocess.run(
                    [str(self.config.runsc), "--version"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                    shell=False,
                    timeout=5,
                )
                version = " ".join(result.stdout.split())
                if result.returncode:
                    diagnostics.append(
                        f"ERROR: runsc --version exited {result.returncode}: {version}"
                    )
                else:
                    diagnostics.append(f"OK: {version or 'runsc available'}")
            except (OSError, subprocess.TimeoutExpired) as exc:
                diagnostics.append(f"ERROR: runsc version check failed: {exc}")

        diagnostics.extend(self.images.doctor())

        try:
            self._ensure_layout()
            self._atomic_probe(self.config.instances_dir.parent)
            diagnostics.append(f"OK: sandbox state at {self.config.instances_dir}")
        except OSError as exc:
            diagnostics.append(f"ERROR: sandbox state is not writable: {exc}")
        try:
            self._ensure_shared_directory()
            self._atomic_probe(self.config.shared_dir)
            diagnostics.append(f"OK: shared exchange at {self.config.shared_dir}")
        except OSError as exc:
            diagnostics.append(f"ERROR: shared exchange is not writable: {exc}")

        instances = self.config.instances_dir.resolve(strict=False)
        shared = self.config.shared_dir.resolve(strict=False)
        if instances == shared or instances in shared.parents or shared in instances.parents:
            diagnostics.append("ERROR: private sandbox state and shared exchange must be separate")

        status = self._proc_status()
        try:
            caps = int(status.get("CapEff", "0"), 16)
        except ValueError:
            caps = 0
        if platform.system() == "Linux" and not caps & (1 << 18):
            diagnostics.append(
                "ERROR: CAP_SYS_CHROOT is unavailable; use the documented native or Docker launch policy"
            )
        if status.get("Seccomp") == "2":
            diagnostics.append(
                "WARNING: an outer seccomp filter is active; nested systrap requires the documented profile"
            )
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
                error = f"unexpected runsc status {observed!r}"
        elif runtime_is_absent(error):
            if snapshot is None:
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
    ) -> SandboxInfo:
        name = validate_name(name)
        network = self._validate_network(network)
        sandbox_type = self._validate_type(sandbox_type)
        normalized_mounts = self._normalize_mounts(mounts)
        normalized_owner = self._normalize_ownership(ownership)
        self._ensure_layout()
        with self._index_lock(exclusive=False):
            path = self._instance_path(name)
            if path.exists() or path.is_symlink():
                raise SandboxError(f"sandbox {name!r} already exists")
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
            overlay = path / "overlay"
            logs = path / "logs"
            for directory in (path, bundle, overlay, logs):
                directory.mkdir(mode=0o700)
            (path / ".lock").touch(mode=0o600, exist_ok=True)
            now = self._now()
            metadata: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
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
                self._refresh_bundle(name, metadata)
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
            command = self._runsc_command(
                name,
                metadata,
                "exec",
                f"--cwd={cwd}",
                "--user=0:0",
                name,
                *args,
            )
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

    def interactive_command(self, name: str, *, cwd: str = "/workspace") -> list[str]:
        name = validate_name(name)
        cwd = self._validate_guest_path(cwd, label="cwd")
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
            self._require_running(name, metadata)
            self._touch_locked(name, metadata)
            return self._runsc_command(
                name,
                metadata,
                "exec",
                f"--cwd={cwd}",
                "--user=0:0",
                name,
                "/bin/bash",
                "--login",
            )

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
            if state is None:
                if runtime_is_absent(error) and snapshot is not None:
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
            elif snapshot is None:
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
        self._require_runtime_artifacts()
        self._ensure_shared_directory()
        with self._operation_lock(name):
            metadata = self._read_metadata(name)
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
            if snapshot is None:
                raise SandboxError(f"sandbox {name!r} has no valid restart snapshot")
            self._refresh_bundle(name, metadata, snapshot=snapshot)
            self._launch(name, metadata)
            self._touch_locked(name, metadata)
        return self.inspect(name)

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
        if not self.config.instances_dir.exists():
            return usage
        for entry in self.config.instances_dir.iterdir():
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
            usage.setdefault(digest, set()).add(entry.name)
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
            raise SandboxError(f"runsc could not delete sandbox {name!r}")
        shutil.rmtree(path)
        self._fsync_directory(self.config.instances_dir)

    def runsc_command_for_test(
        self,
        name: str,
        network: NetworkMode,
        sandbox_type: SandboxType,
        *arguments: str,
    ) -> list[str]:
        metadata = {"network": network, "sandbox_type": sandbox_type}
        return self._runsc_command(validate_name(name), metadata, *arguments)

    def oci_config_for_test(
        self,
        name: str,
        network: NetworkMode,
        sandbox_type: SandboxType,
        mounts: Sequence[SandboxMount | Mapping[str, Any]] = (),
        snapshot: Path | None = None,
    ) -> dict[str, Any]:
        try:
            image = self.images.ensure(self.config.default_image)
        except SandboxImageError as exc:
            raise SandboxError(str(exc)) from exc
        metadata = {
            "network": self._validate_network(network),
            "sandbox_type": self._validate_type(sandbox_type),
            "image_ref": image.reference,
            "image_digest": image.digest,
            "mounts": [self._mount_json(m) for m in self._normalize_mounts(mounts)],
        }
        bundle = self._instance_path(validate_name(name)) / "bundle"
        return self._oci_config(name, metadata, bundle, snapshot=snapshot)

    def _validated_metadata(self, name: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise SandboxError(f"sandbox {name!r} metadata is not an object")
        if value.get("schema_version") != SCHEMA_VERSION or value.get("name") != name:
            raise SandboxError(f"sandbox {name!r} has incompatible metadata")
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
        mounts = value.get("mounts", [])
        if not isinstance(mounts, list):
            raise SandboxError(f"sandbox {name!r} has invalid mount metadata")
        self._normalize_mounts(mounts)
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
        mounts = tuple(self._normalize_mounts(metadata.get("mounts", [])))
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
            size_bytes=allocated_bytes(self._instance_path(name)),
            mounts=mounts,
            ownership=dict(self._normalize_ownership(metadata.get("ownership"))),
            runtime_error=runtime_error,
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
            size_bytes=allocated_bytes(self._instance_path(name)),
            ownership={key: None for key in _OWNERSHIP_KEYS},
            runtime_error=error,
        )

    def _runtime_state(
        self, name: str, metadata: Mapping[str, Any]
    ) -> tuple[dict[str, Any] | None, str | None]:
        try:
            result = subprocess.run(
                self._runsc_command(name, metadata, "state", name),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                shell=False,
                timeout=self.config.state_timeout,
            )
        except subprocess.TimeoutExpired:
            return None, "runsc state timed out"
        except OSError as exc:
            return None, str(exc)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            return None, detail or f"runsc state exited {result.returncode}"
        try:
            state = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return None, f"invalid JSON from runsc state: {exc}"
        if not isinstance(state, dict) or not isinstance(state.get("status"), str):
            return None, "runsc state returned an invalid object"
        return state, None

    def _runsc_command(
        self, name: str, metadata: Mapping[str, Any], *arguments: str
    ) -> list[str]:
        network = self._validate_network(metadata.get("network"))
        sandbox_type = self._validate_type(metadata.get("sandbox_type"))
        path = self._instance_path(name)
        command_name = arguments[0] if arguments else "unknown"
        overlay = (
            "--overlay2=root:memory"
            if sandbox_type == "temporary"
            else f"--overlay2=root:dir={path / 'overlay'}"
        )
        return [
            str(self.config.runsc),
            "--allow-rootfs-tar-annotation",
            f"--root={self.config.runsc_root}",
            "--rootless=true",
            "--platform=systrap",
            "--directfs=false",
            "--file-access=exclusive",
            "--file-access-mounts=shared",
            f"--network={network}",
            overlay,
            f"--log={path / 'logs' / f'runsc-{command_name}.log'}",
            *arguments,
        ]

    def _oci_config(
        self,
        name: str,
        metadata: Mapping[str, Any],
        bundle: Path,
        *,
        snapshot: Path | None = None,
    ) -> dict[str, Any]:
        network = self._validate_network(metadata.get("network"))
        try:
            image = self.images.inspect(str(metadata.get("image_digest") or ""))
        except SandboxImageError as exc:
            raise SandboxError(f"base image is unavailable: {exc}") from exc
        if image.rootfs is None:
            raise SandboxError(f"base image {image.digest} has no usable root filesystem")
        environment: dict[str, str] = {}
        for item in image.environment:
            key, separator, value = item.partition("=")
            if separator:
                environment[key] = value
        environment.setdefault(
            "PATH",
            "/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        )
        environment.update(
            {
                "HOME": "/root",
                "LANG": environment.get("LANG", "C.UTF-8"),
                "TERM": "xterm-256color",
                "PAGER": "cat",
                "GIT_PAGER": "cat",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1",
                "PIP_ROOT_USER_ACTION": "ignore",
                "PIPX_HOME": "/root/.local/share/pipx",
                "PIPX_BIN_DIR": "/root/.local/bin",
                "UV_TOOL_BIN_DIR": "/root/.local/bin",
            }
        )
        namespaces = [
            {"type": "pid"},
            {"type": "ipc"},
            {"type": "uts"},
            {"type": "mount"},
        ]
        if network == "none":
            namespaces.append({"type": "network"})
        mounts: list[dict[str, Any]] = [
            {"destination": "/proc", "type": "proc", "source": "proc", "options": ["nosuid", "noexec", "nodev"]},
            {"destination": "/dev", "type": "tmpfs", "source": "tmpfs", "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]},
            {"destination": "/dev/pts", "type": "devpts", "source": "devpts", "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620", "gid=5"]},
            {"destination": "/dev/shm", "type": "tmpfs", "source": "shm", "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=65536k"]},
            {"destination": "/dev/mqueue", "type": "mqueue", "source": "mqueue", "options": ["nosuid", "noexec", "nodev"]},
            {"destination": "/sys", "type": "sysfs", "source": "sysfs", "options": ["nosuid", "noexec", "nodev", "ro"]},
            {"destination": "/tmp", "type": "tmpfs", "source": "tmpfs", "options": ["nosuid", "nodev", "mode=1777"]},
            {"destination": "/run", "type": "tmpfs", "source": "tmpfs", "options": ["nosuid", "nodev", "mode=755"]},
            {"destination": "/etc/resolv.conf", "type": "bind", "source": str(bundle / "resolv.conf"), "options": ["bind", "ro", "nosuid", "nodev", "noexec"]},
            {"destination": "/etc/hosts", "type": "bind", "source": str(bundle / "hosts"), "options": ["bind", "ro", "nosuid", "nodev", "noexec"]},
            {"destination": "/shared", "type": "bind", "source": str(self.config.shared_dir), "options": ["rbind", "rw", "nosuid", "nodev"]},
        ]
        for item in self._normalize_mounts(metadata.get("mounts", [])):
            options = ["rbind", "ro" if item.read_only else "rw", "nosuid", "nodev"]
            mounts.append(
                {
                    "destination": item.destination,
                    "type": "bind",
                    "source": str(item.source),
                    "options": options,
                }
            )
        config: dict[str, Any] = {
            "ociVersion": "1.0.2",
            "process": {
                "terminal": False,
                "user": {"uid": 0, "gid": 0},
                "args": ["/bin/sh", "-c", "trap 'exit 0' TERM INT; while :; do sleep 3600; done"],
                "env": [f"{key}={value}" for key, value in environment.items()],
                "cwd": "/workspace",
                "capabilities": {
                    "bounding": list(CAPABILITIES),
                    "effective": list(CAPABILITIES),
                    "inheritable": [],
                    "permitted": list(CAPABILITIES),
                    "ambient": [],
                },
                "noNewPrivileges": False,
                "rlimits": [{"type": "RLIMIT_NOFILE", "hard": 65535, "soft": 65535}],
            },
            "root": {"path": str(image.rootfs), "readonly": False},
            "hostname": name,
            "mounts": mounts,
            "linux": {
                "namespaces": namespaces,
                "maskedPaths": [
                    "/proc/acpi", "/proc/kcore", "/proc/keys", "/proc/latency_stats",
                    "/proc/timer_list", "/proc/timer_stats", "/proc/sched_debug", "/sys/firmware",
                ],
                "readonlyPaths": [
                    "/proc/asound", "/proc/bus", "/proc/fs", "/proc/irq",
                    "/proc/sys", "/proc/sysrq-trigger",
                ],
            },
        }
        if snapshot is not None:
            config["annotations"] = {"dev.gvisor.tar.rootfs.upper": str(snapshot)}
        return config

    def _refresh_bundle(
        self,
        name: str,
        metadata: Mapping[str, Any],
        *,
        snapshot: Path | None = None,
    ) -> None:
        bundle = self._instance_path(name) / "bundle"
        for source, target_name in (
            (Path("/etc/resolv.conf"), "resolv.conf"),
            (Path("/etc/hosts"), "hosts"),
        ):
            try:
                content = source.read_text(encoding="utf-8")
            except OSError as exc:
                raise SandboxError(f"cannot read outer {source}: {exc}") from exc
            self._atomic_write_text(bundle / target_name, content, mode=0o644)
        self._atomic_write_json(
            bundle / "config.json",
            self._oci_config(name, metadata, bundle, snapshot=snapshot),
        )

    def _launch(self, name: str, metadata: dict[str, Any]) -> None:
        path = self._instance_path(name)
        bundle = path / "bundle"
        logs = path / "logs"
        launcher_log = logs / "launcher.log"
        detached = self._runsc_command(
            name,
            metadata,
            "run",
            "--detach",
            f"--bundle={bundle}",
            f"--user-log={logs / 'user.log'}",
            name,
        )
        detached_result: subprocess.CompletedProcess[bytes] | None = None
        with launcher_log.open("ab", buffering=0) as output:
            output.write(b"== detached launch ==\n")
            try:
                detached_result = subprocess.run(
                    detached,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    check=False,
                    shell=False,
                    timeout=self.config.start_timeout,
                )
            except subprocess.TimeoutExpired:
                output.write(b"detached run command timed out\n")
        state = None
        error = "detached run command timed out"
        if detached_result is not None and detached_result.returncode == 0:
            state, error = self._wait_for_status(name, metadata, {"running"}, self.config.start_timeout)
        elif detached_result is not None:
            error = f"detached run exited {detached_result.returncode}"
        if state is None or state.get("status") != "running":
            self._append_log(
                launcher_log,
                f"detached launch unavailable ({error}); trying attached fallback",
            )
            if not self._force_runtime_delete(name, metadata):
                raise SandboxError(
                    f"could not clean failed launch for {name!r}; state retained at {path}"
                )
            with launcher_log.open("ab", buffering=0) as output:
                output.write(b"== attached fallback launch ==\n")
                launcher = subprocess.Popen(
                    self._runsc_command(
                        name,
                        metadata,
                        "run",
                        f"--bundle={bundle}",
                        f"--user-log={logs / 'user.log'}",
                        name,
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    shell=False,
                )
            metadata["launch_mode"] = "attached-fallback"
            metadata["launcher_pid"] = launcher.pid
            self._atomic_write_json(path / "metadata.json", metadata)
            state, error = self._wait_for_status(
                name,
                metadata,
                {"running"},
                self.config.start_timeout,
                launcher=launcher,
            )
            if state is None or state.get("status") != "running":
                with contextlib.suppress(ProcessLookupError):
                    launcher.terminate()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    launcher.wait(timeout=1)
                if launcher.poll() is None:
                    with contextlib.suppress(ProcessLookupError):
                        launcher.kill()
                raise SandboxError(
                    f"sandbox {name!r} did not reach running state: {error}; "
                    f"launcher log: {self._log_tail(launcher_log)}"
                )
        else:
            metadata["launch_mode"] = "detached"
            metadata["launcher_pid"] = None
        metadata["last_known_status"] = "running"
        self._atomic_write_json(path / "metadata.json", metadata)

    def _save_locked(self, name: str, metadata: dict[str, Any]) -> None:
        path = self._instance_path(name)
        snapshot = path / ROOTFS_SNAPSHOT
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{ROOTFS_SNAPSHOT}.", dir=path)
        os.close(descriptor)
        temporary = Path(temp_name)
        temporary.unlink()
        try:
            result = subprocess.run(
                self._runsc_command(
                    name,
                    metadata,
                    "tar",
                    "rootfs-upper",
                    f"--file={temporary}",
                    name,
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                shell=False,
                timeout=self.config.snapshot_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            temporary.unlink(missing_ok=True)
            raise SandboxError(
                f"filesystem snapshot timed out for {name!r}; sandbox remains running"
            ) from exc
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise SandboxError(f"could not snapshot filesystem for {name!r}: {exc}") from exc
        if result.stdout:
            self._append_log(path / "logs" / "snapshot.log", result.stdout)
        if result.returncode or not temporary.is_file() or temporary.is_symlink():
            temporary.unlink(missing_ok=True)
            detail = result.stdout.strip() or f"runsc tar exited {result.returncode}"
            raise SandboxError(
                f"could not snapshot filesystem for {name!r}: {detail}; sandbox remains running"
            )
        temporary.chmod(0o600)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, snapshot)
        self._fsync_directory(path)
        metadata["rootfs_snapshot"] = ROOTFS_SNAPSHOT
        metadata["snapshot_at"] = self._now()
        self._atomic_write_json(path / "metadata.json", metadata)

    def _stop_runtime(self, name: str, metadata: Mapping[str, Any]) -> None:
        state, error = self._runtime_state(name, metadata)
        if state is None and runtime_is_absent(error):
            return
        if state is not None and state.get("status") == "stopped":
            return
        self._run_quiet(
            self._runsc_command(name, metadata, "kill", "--all", name, "TERM"),
            timeout=3,
        )
        state, error = self._wait_for_status(
            name, metadata, {"stopped"}, self.config.stop_timeout
        )
        if state is not None and state.get("status") == "stopped":
            return
        if state is None and runtime_is_absent(error):
            return
        self._run_quiet(
            self._runsc_command(name, metadata, "kill", "--all", name, "KILL"),
            timeout=3,
        )
        state, error = self._wait_for_status(
            name, metadata, {"stopped"}, self.config.stop_timeout
        )
        if state is None and runtime_is_absent(error):
            return
        if state is not None and state.get("status") == "stopped":
            return
        # Some runsc versions keep reporting "running" after both kill calls
        # while the init process is being reaped. Forced runtime deletion is
        # the final bounded stop operation and is confirmed by missing state.
        if self._force_runtime_delete(name, metadata):
            return
        raise SandboxError(f"could not confirm sandbox {name!r} stopped: {error}")

    def _force_runtime_delete(self, name: str, metadata: Mapping[str, Any]) -> bool:
        path = self._instance_path(name)
        try:
            result = subprocess.run(
                self._runsc_command(name, metadata, "delete", "--force", name),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                shell=False,
                timeout=self.config.delete_timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._append_log(path / "logs" / "launcher.log", f"runsc delete failed: {exc}")
            return False
        if result.stdout:
            self._append_log(path / "logs" / "launcher.log", result.stdout)
        state, error = self._runtime_state(name, metadata)
        return state is None and (result.returncode == 0 or runtime_is_absent(error))

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
                return last_state, f"runsc launcher exited {launcher.returncode}"
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
            process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
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

    @staticmethod
    def _run_quiet(argv: Sequence[str], *, timeout: float) -> None:
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                shell=False,
                timeout=timeout,
            )

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
        self, mounts: Sequence[SandboxMount | Mapping[str, Any]]
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
            if not source.is_absolute():
                raise SandboxError(f"mount source must be absolute: {source}")
            if source.is_symlink():
                raise SandboxError(f"mount source must not be a symlink: {source}")
            source = source.resolve(strict=False)
            if not source.is_dir():
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

    def _require_runtime_artifacts(self) -> None:
        if not self.config.runsc.is_file() or not os.access(self.config.runsc, os.X_OK):
            raise SandboxError(f"runsc not found at {self.config.runsc}; run sandbox doctor")

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

    def _instance_path(self, name: str) -> Path:
        validate_name(name)
        path = self.config.instances_dir / name
        if path.parent != self.config.instances_dir:
            raise SandboxError("sandbox path escaped the instances directory")
        return path

    def _ensure_layout(self) -> None:
        for path in (
            self.config.instances_dir.parent,
            self.config.instances_dir,
            self.config.runsc_root,
        ):
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            with contextlib.suppress(PermissionError):
                path.chmod(0o700)

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

    @staticmethod
    def _proc_status() -> dict[str, str]:
        result: dict[str, str] = {}
        with contextlib.suppress(OSError):
            for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    result[key] = value.strip()
        return result


def sandbox_info_dict(info: SandboxInfo) -> dict[str, Any]:
    """Serialize public sandbox information for tools and HTTP APIs."""
    result = dataclasses.asdict(info)
    for mount in result.get("mounts", []):
        mount["source"] = str(mount.get("source") or "")
    return result
