from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from plugins._sandboxing.helpers import builtin_image


ImageStatus = Literal["ready", "broken"]

IMAGE_SCHEMA_VERSION = 1
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SandboxImageError(RuntimeError):
    """A safe, user-facing sandbox image management error."""


@dataclass(frozen=True, slots=True)
class SandboxImageConfig:
    skopeo: Path
    umoci: Path
    cache_dir: Path
    default_image: str
    runsc: Path = Path("/usr/bin/runsc")
    auth_file: Path | None = None
    cleanup_days: float = 30.0
    pull_timeout: float = 900.0
    unpack_timeout: float = 900.0
    max_output_bytes: int = 1_048_576
    max_image_bytes: int = 17_179_869_184


@dataclass(frozen=True, slots=True)
class SandboxImageInfo:
    digest: str
    reference: str
    references: tuple[str, ...]
    status: ImageStatus
    created_at: str
    last_used_at: str
    size_bytes: int | None
    os: str = ""
    architecture: str = ""
    used_by: tuple[str, ...] = ()
    runtime_error: str | None = None
    rootfs: Path | None = field(default=None, repr=False, compare=False)
    environment: tuple[str, ...] = field(default=(), repr=False, compare=False)


def validate_digest(value: str) -> str:
    digest = str(value or "").strip().lower()
    if not _DIGEST_RE.fullmatch(digest):
        raise SandboxImageError(f"invalid OCI image digest {value!r}")
    return digest


def normalize_image_reference(value: str) -> str:
    reference = str(value or "").strip()
    if reference.startswith("docker://"):
        reference = reference[9:]
    if (
        not reference
        or len(reference) > 512
        or any(char.isspace() or ord(char) < 32 for char in reference)
        or "://" in reference
        or reference.startswith(("/", "."))
    ):
        raise SandboxImageError(f"invalid Docker image reference {value!r}")
    return reference


def image_info_dict(info: SandboxImageInfo) -> dict[str, Any]:
    """Serialize image information without private cache paths or image env."""
    return {
        "digest": info.digest,
        "reference": info.reference,
        "references": list(info.references),
        "status": info.status,
        "created_at": info.created_at,
        "last_used_at": info.last_used_at,
        "size_bytes": info.size_bytes,
        "os": info.os,
        "architecture": info.architecture,
        "used_by": list(info.used_by),
        "runtime_error": info.runtime_error,
    }


class SandboxImageManager:
    """Pull, unpack, cache, and remove immutable Docker/OCI image roots."""

    def __init__(self, config: SandboxImageConfig) -> None:
        self.config = self._validated_config(config)
        self._thread_lock = threading.RLock()

    @staticmethod
    def _validated_config(config: SandboxImageConfig) -> SandboxImageConfig:
        for label, path in (
            ("skopeo", config.skopeo),
            ("umoci", config.umoci),
            ("image cache", config.cache_dir),
            ("runsc", config.runsc),
        ):
            if not path.is_absolute():
                raise SandboxImageError(f"{label} path must be absolute: {path}")
        if config.auth_file is not None and not config.auth_file.is_absolute():
            raise SandboxImageError(
                f"registry auth file path must be absolute: {config.auth_file}"
            )
        if config.cleanup_days <= 0:
            raise SandboxImageError("image cleanup days must be positive")
        if config.max_output_bytes < 4096:
            raise SandboxImageError("image command output limit must be at least 4096")
        if config.max_image_bytes < 1_048_576:
            raise SandboxImageError("maximum unpacked image size must be at least 1 MiB")
        if config.default_image:
            normalize_image_reference(config.default_image)
        return config

    def doctor(self) -> list[str]:
        diagnostics: list[str] = []
        for label, executable in (
            ("skopeo", self.config.skopeo),
            ("umoci", self.config.umoci),
        ):
            if not executable.is_file() or not os.access(executable, os.X_OK):
                diagnostics.append(f"ERROR: {label} is not executable at {executable}")
                continue
            try:
                result = self._run(
                    [str(executable), "--version"],
                    timeout=5,
                    operation=f"check {label} version",
                    check=False,
                )
                detail = " ".join((result[1] or result[2]).split())
                if result[0]:
                    diagnostics.append(
                        f"ERROR: {label} --version exited {result[0]}: {detail}"
                    )
                else:
                    diagnostics.append(f"OK: {detail or f'{label} available'}")
            except SandboxImageError as exc:
                diagnostics.append(f"ERROR: {exc}")
        try:
            self._ensure_layout()
            self._atomic_probe(self.config.cache_dir)
            diagnostics.append(f"OK: sandbox image cache at {self.config.cache_dir}")
        except (OSError, SandboxImageError) as exc:
            diagnostics.append(f"ERROR: sandbox image cache is not writable: {exc}")
        if not self.config.default_image:
            diagnostics.append("ERROR: no default sandbox image is configured")
        else:
            diagnostics.append(f"OK: default sandbox image {self.config.default_image}")
        auth_file = self.config.auth_file
        if auth_file is not None:
            if auth_file.is_symlink() or not auth_file.is_file():
                diagnostics.append(
                    f"ERROR: registry auth file is not a regular non-symlink file: {auth_file}"
                )
            else:
                diagnostics.append(f"OK: registry auth file configured at {auth_file}")
        return diagnostics

    def list(self) -> list[SandboxImageInfo]:
        self._ensure_layout()
        results: list[SandboxImageInfo] = []
        with self._cache_lock():
            for entry in sorted(self.config.cache_dir.iterdir(), key=lambda path: path.name):
                digest = self._digest_from_directory(entry.name)
                if digest is None or entry.is_symlink() or not entry.is_dir():
                    continue
                try:
                    results.append(self._read_info_locked(digest))
                except SandboxImageError as exc:
                    results.append(self._broken_info(digest, entry, str(exc)))
        return results

    def inspect(self, identifier: str) -> SandboxImageInfo:
        self._ensure_layout()
        with self._cache_lock():
            digest = self._resolve_identifier_locked(identifier)
            return self._read_info_locked(digest)

    def ensure(
        self,
        reference: str = "",
        *,
        digest: str | None = None,
        refresh: bool = False,
    ) -> SandboxImageInfo:
        requested = normalize_image_reference(reference or self.config.default_image)
        expected = validate_digest(digest) if digest else None
        self._ensure_layout()
        with self._cache_lock():
            if expected is not None and self._image_path(expected).is_dir():
                try:
                    return self._touch_reference_locked(expected, requested)
                except SandboxImageError:
                    self._delete_path_locked(expected, self._image_path(expected))
            if expected is None and not refresh:
                cached = self._find_reference_locked(requested)
                if cached is not None:
                    return self._touch_reference_locked(cached, requested)
            if requested == builtin_image.BUILTIN_IMAGE:
                return self._builtin_locked(expected)
            pull_reference = (
                self._pinned_reference(requested, expected) if expected else requested
            )
            return self._pull_locked(
                pull_reference,
                expected_digest=expected,
                display_reference=requested,
                update_alias=expected is None,
            )

    def pull(self, reference: str = "") -> SandboxImageInfo:
        return self.ensure(reference, refresh=True)

    def import_archive(self, archive: Path, reference: str) -> SandboxImageInfo:
        """Import a local `docker save` archive under a cache reference."""
        reference = normalize_image_reference(reference)
        if archive.is_symlink() or not archive.is_file():
            raise SandboxImageError("image archive must be a regular non-symlink file")
        if archive.stat().st_size > self.config.max_image_bytes:
            raise SandboxImageError("image archive exceeds the configured size limit")
        self._ensure_layout()
        with self._cache_lock(), tempfile.TemporaryDirectory(
            prefix=".pull-", dir=self.config.cache_dir
        ) as temporary:
            # Inspect and copy the same private archive even if the source is replaced.
            snapshot = Path(temporary) / "image.tar"
            shutil.copyfile(archive, snapshot)
            if snapshot.stat().st_size > self.config.max_image_bytes:
                raise SandboxImageError("image archive exceeds the configured size limit")
            return self._pull_locked(
                reference,
                expected_digest=None,
                display_reference=reference,
                update_alias=True,
                source=f"docker-archive:{snapshot}",
            )

    def _builtin_locked(self, expected: str | None) -> SandboxImageInfo:
        def load(layout: Path) -> SandboxImageInfo:
            return self._pull_locked(
                builtin_image.BUILTIN_IMAGE,
                expected_digest=expected,
                display_reference=builtin_image.BUILTIN_IMAGE,
                update_alias=expected is None,
                source=f"oci:{layout}:image",
            )

        if builtin_image.BUNDLE_PATH.is_dir():
            try:
                return load(builtin_image.BUNDLE_PATH)
            except SandboxImageError:
                # A damaged or incompatible bundle can be rebuilt on first use.
                pass
        with tempfile.TemporaryDirectory(prefix=".pull-", dir=self.config.cache_dir) as temporary:
            return load(builtin_image.build_image(self, Path(temporary)))

    def touch(self, digest: str) -> None:
        digest = validate_digest(digest)
        self._ensure_layout()
        with self._cache_lock():
            info = self._read_info_locked(digest)
            self._write_info_locked(dataclasses.replace(info, last_used_at=self._now()))

    def delete(self, digest: str, *, missing_ok: bool = False) -> bool:
        digest = validate_digest(digest)
        self._ensure_layout()
        with self._cache_lock():
            path = self._image_path(digest)
            if not path.exists() and not path.is_symlink():
                if missing_ok:
                    return False
                raise SandboxImageError(f"sandbox image {digest} is not cached")
            self._delete_path_locked(digest, path)
            return True

    def cleanup(
        self,
        *,
        used_digests: set[str],
        now: dt.datetime | None = None,
    ) -> list[str]:
        current = now or dt.datetime.now(dt.timezone.utc)
        cutoff = current - dt.timedelta(days=self.config.cleanup_days)
        removed: list[str] = []
        self._ensure_layout()
        with self._cache_lock():
            for entry in sorted(self.config.cache_dir.iterdir(), key=lambda path: path.name):
                digest = self._digest_from_directory(entry.name)
                if digest is None:
                    if (
                        re.fullmatch(r"\.pull-[A-Za-z0-9_-]+", entry.name)
                        and not entry.is_symlink()
                        and entry.is_dir()
                    ):
                        with contextlib.suppress(OSError):
                            modified = dt.datetime.fromtimestamp(
                                entry.stat().st_mtime, tz=dt.timezone.utc
                            )
                            if modified <= cutoff:
                                shutil.rmtree(entry)
                    continue
                if digest in used_digests:
                    continue
                try:
                    info = self._read_info_locked(digest)
                    last_used = self._parse_timestamp(info.last_used_at, "last_used_at")
                except SandboxImageError:
                    try:
                        last_used = self._read_cleanup_timestamp_locked(digest)
                    except SandboxImageError:
                        continue
                if last_used > cutoff:
                    continue
                self._delete_path_locked(digest, entry)
                removed.append(digest)
        return removed

    def _read_cleanup_timestamp_locked(self, digest: str) -> dt.datetime:
        path = self._image_path(digest)
        metadata_path = path / "metadata.json"
        if (
            path.is_symlink()
            or not path.is_dir()
            or metadata_path.is_symlink()
            or not metadata_path.is_file()
        ):
            raise SandboxImageError(f"sandbox image {digest} has unsafe cache content")
        try:
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SandboxImageError(f"cannot read sandbox image {digest}: {exc}") from exc
        if not isinstance(value, dict) or value.get("digest") != digest:
            raise SandboxImageError(f"sandbox image {digest} has invalid metadata")
        return self._parse_timestamp(value.get("last_used_at"), "last_used_at")

    def _pull_locked(
        self,
        reference: str,
        *,
        expected_digest: str | None,
        display_reference: str,
        update_alias: bool,
        source: str | None = None,
    ) -> SandboxImageInfo:
        self._require_tools()
        inspect_argv = [
            *self._skopeo_command("inspect"),
            "--no-tags",
            source or f"docker://{reference}",
        ]
        _, output, _, _ = self._run(
            inspect_argv,
            timeout=self.config.pull_timeout,
            operation=f"inspect sandbox image {reference!r}",
        )
        try:
            inspected = json.loads(output)
        except json.JSONDecodeError as exc:
            raise SandboxImageError(
                f"image returned invalid metadata for {reference!r}: {exc}"
            ) from exc
        if not isinstance(inspected, dict):
            raise SandboxImageError(f"image returned invalid metadata for {reference!r}")
        digest = validate_digest(str(inspected.get("Digest") or expected_digest or ""))
        if expected_digest is not None and digest != expected_digest:
            raise SandboxImageError(
                f"image {reference!r} resolved to {digest}, expected {expected_digest}"
            )
        layers = inspected.get("LayersData")
        if isinstance(layers, list):
            compressed_bytes = 0
            for layer in layers:
                if not isinstance(layer, dict):
                    continue
                with contextlib.suppress(TypeError, ValueError):
                    compressed_bytes += max(0, int(layer.get("Size") or 0))
            if compressed_bytes > self.config.max_image_bytes:
                raise SandboxImageError(
                    f"compressed image is {compressed_bytes} bytes, above the configured "
                    f"{self.config.max_image_bytes}-byte limit"
                )
        target = self._image_path(digest)
        if target.is_dir():
            try:
                info = self._touch_reference_locked(digest, display_reference)
            except SandboxImageError:
                self._delete_path_locked(digest, target)
            else:
                if update_alias:
                    self._set_alias_locked(display_reference, digest)
                return info
        source = source or f"docker://{self._pinned_reference(reference, digest)}"
        temporary = Path(tempfile.mkdtemp(prefix=".pull-", dir=self.config.cache_dir))
        try:
            layout = temporary / "layout"
            bundle = temporary / "bundle"
            self._run(
                [
                    *self._skopeo_command("copy"),
                    source,
                    f"oci:{layout}:image",
                ],
                timeout=self.config.pull_timeout,
                operation=f"pull sandbox image {reference!r}",
            )
            self._run(
                [
                    str(self.config.umoci),
                    "unpack",
                    "--rootless",
                    "--image",
                    f"{layout}:image",
                    str(bundle),
                ],
                timeout=self.config.unpack_timeout,
                operation=f"unpack sandbox image {reference!r}",
            )
            rootfs = bundle / "rootfs"
            environment = self._validate_unpacked_rootfs(bundle, rootfs)
            size_bytes = self._allocated_bytes(rootfs)
            if size_bytes > self.config.max_image_bytes:
                raise SandboxImageError(
                    f"unpacked image is {size_bytes} bytes, above the configured "
                    f"{self.config.max_image_bytes}-byte limit"
                )
            record = temporary / "record"
            record.mkdir(mode=0o700)
            os.replace(rootfs, record / "rootfs")
            now = self._now()
            info = SandboxImageInfo(
                digest=digest,
                reference=display_reference,
                references=(display_reference,),
                status="ready",
                created_at=now,
                last_used_at=now,
                size_bytes=size_bytes,
                os=str(inspected.get("Os") or ""),
                architecture=str(inspected.get("Architecture") or ""),
                rootfs=record / "rootfs",
                environment=environment,
            )
            self._write_info_path(record / "metadata.json", info)
            os.replace(record, target)
            self._fsync_directory(self.config.cache_dir)
            if update_alias:
                self._set_alias_locked(display_reference, digest)
            return dataclasses.replace(info, rootfs=target / "rootfs")
        except BaseException:
            if target.exists() and not target.is_symlink():
                with contextlib.suppress(OSError):
                    shutil.rmtree(target)
            raise
        finally:
            if temporary.exists() and not temporary.is_symlink():
                shutil.rmtree(temporary, ignore_errors=True)

    def _validate_unpacked_rootfs(
        self, bundle: Path, rootfs: Path
    ) -> tuple[str, ...]:
        if rootfs.is_symlink() or not rootfs.is_dir():
            raise SandboxImageError("unpacked OCI image has no safe root filesystem")
        self._validate_required_commands(rootfs)
        for relative in ("workspace", "shared"):
            path = rootfs / relative
            if path.is_symlink():
                raise SandboxImageError(f"sandbox image /{relative} must not be a symlink")
            path.mkdir(mode=0o777, parents=True, exist_ok=True)
            with contextlib.suppress(PermissionError):
                path.chmod(0o777)
        etc = rootfs / "etc"
        if etc.is_symlink():
            raise SandboxImageError("sandbox image /etc must not be a symlink")
        etc.mkdir(mode=0o755, parents=True, exist_ok=True)
        for name in ("hosts", "resolv.conf"):
            path = etc / name
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise SandboxImageError(f"sandbox image /etc/{name} must be a regular file")
            path.touch(mode=0o644, exist_ok=True)
        config_path = bundle / "config.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SandboxImageError(f"cannot read unpacked OCI configuration: {exc}") from exc
        raw_env = config.get("process", {}).get("env", []) if isinstance(config, dict) else []
        return self._normalize_environment(raw_env)

    @staticmethod
    def _validate_required_commands(rootfs: Path) -> None:
        for required in ("bin/sh", "bin/bash"):
            path = rootfs / required
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(rootfs.resolve(strict=True))
            except (OSError, ValueError):
                raise SandboxImageError(
                    f"sandbox image is missing safe required /{required}"
                )
            if not resolved.is_file():
                raise SandboxImageError(f"sandbox image /{required} is not a file")

    @staticmethod
    def _normalize_environment(raw: Any) -> tuple[str, ...]:
        if not isinstance(raw, list):
            return ()
        result: list[str] = []
        for item in raw[:256]:
            value = str(item)
            if len(value) > 8192 or "\x00" in value or "=" not in value:
                continue
            key = value.split("=", 1)[0]
            if _ENV_KEY_RE.fullmatch(key):
                result.append(value)
        return tuple(result)

    def _read_info_locked(self, digest: str) -> SandboxImageInfo:
        digest = validate_digest(digest)
        path = self._image_path(digest)
        if path.is_symlink() or not path.is_dir():
            raise SandboxImageError(f"sandbox image {digest} is not cached safely")
        metadata_path = path / "metadata.json"
        rootfs = path / "rootfs"
        if metadata_path.is_symlink() or rootfs.is_symlink() or not rootfs.is_dir():
            raise SandboxImageError(f"sandbox image {digest} has unsafe cache content")
        self._validate_required_commands(rootfs)
        workspace = rootfs / "workspace"
        if workspace.is_symlink() or not workspace.is_dir():
            raise SandboxImageError(f"sandbox image {digest} has no safe /workspace")
        try:
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SandboxImageError(f"cannot read sandbox image {digest}: {exc}") from exc
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != IMAGE_SCHEMA_VERSION
            or value.get("digest") != digest
        ):
            raise SandboxImageError(f"sandbox image {digest} has incompatible metadata")
        references = value.get("references")
        if not isinstance(references, list) or not references:
            raise SandboxImageError(f"sandbox image {digest} has invalid references")
        normalized_references = tuple(normalize_image_reference(item) for item in references)
        reference = normalize_image_reference(str(value.get("reference") or references[0]))
        created = self._parse_timestamp(value.get("created_at"), "created_at").isoformat()
        last_used = self._parse_timestamp(value.get("last_used_at"), "last_used_at").isoformat()
        environment = self._normalize_environment(value.get("environment", []))
        try:
            size_bytes = max(0, int(value.get("size_bytes")))
        except (TypeError, ValueError):
            size_bytes = None
        return SandboxImageInfo(
            digest=digest,
            reference=reference,
            references=normalized_references,
            status="ready",
            created_at=created,
            last_used_at=last_used,
            size_bytes=size_bytes,
            os=str(value.get("os") or ""),
            architecture=str(value.get("architecture") or ""),
            rootfs=rootfs,
            environment=environment,
        )

    def _write_info_locked(self, info: SandboxImageInfo) -> None:
        self._write_info_path(self._image_path(info.digest) / "metadata.json", info)

    def _write_info_path(self, path: Path, info: SandboxImageInfo) -> None:
        self._atomic_write_json(
            path,
            {
                "schema_version": IMAGE_SCHEMA_VERSION,
                "digest": info.digest,
                "reference": info.reference,
                "references": list(info.references),
                "created_at": info.created_at,
                "last_used_at": info.last_used_at,
                "os": info.os,
                "architecture": info.architecture,
                "size_bytes": info.size_bytes,
                "environment": list(info.environment),
            },
        )

    def _touch_reference_locked(
        self, digest: str, reference: str
    ) -> SandboxImageInfo:
        info = self._read_info_locked(digest)
        references = tuple(dict.fromkeys((*info.references, reference)))
        updated = dataclasses.replace(
            info,
            reference=reference,
            references=references,
            last_used_at=self._now(),
        )
        self._write_info_locked(updated)
        return updated

    def _find_reference_locked(self, reference: str) -> str | None:
        requested_digest = None
        if "@" in reference:
            with contextlib.suppress(SandboxImageError):
                requested_digest = validate_digest(reference.rsplit("@", 1)[1])
        if requested_digest and self._image_path(requested_digest).is_dir():
            return requested_digest
        aliases = self._read_aliases_locked()
        aliased = aliases.get(reference)
        if aliased:
            with contextlib.suppress(SandboxImageError):
                info = self._read_info_locked(aliased)
                if reference in info.references:
                    return aliased
        matches: list[tuple[dt.datetime, str]] = []
        for entry in self.config.cache_dir.iterdir():
            digest = self._digest_from_directory(entry.name)
            if digest is None or entry.is_symlink() or not entry.is_dir():
                continue
            with contextlib.suppress(SandboxImageError):
                info = self._read_info_locked(digest)
                if reference in info.references:
                    matches.append(
                        (self._parse_timestamp(info.created_at, "created_at"), digest)
                    )
        if not matches:
            return None
        digest = max(matches)[1]
        self._set_alias_locked(reference, digest)
        return digest

    def _read_aliases_locked(self) -> dict[str, str]:
        path = self.config.cache_dir / "aliases.json"
        if not path.exists():
            return {}
        if path.is_symlink() or not path.is_file():
            raise SandboxImageError(f"sandbox image alias index is unsafe: {path}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(value, dict):
            return {}
        result: dict[str, str] = {}
        for raw_reference, raw_digest in value.items():
            try:
                reference = normalize_image_reference(str(raw_reference))
                digest = validate_digest(str(raw_digest))
            except SandboxImageError:
                continue
            result[reference] = digest
        return result

    def _set_alias_locked(self, reference: str, digest: str) -> None:
        reference = normalize_image_reference(reference)
        digest = validate_digest(digest)
        aliases = self._read_aliases_locked()
        if aliases.get(reference) == digest:
            return
        aliases[reference] = digest
        self._atomic_write_json(self.config.cache_dir / "aliases.json", aliases)

    def _resolve_identifier_locked(self, identifier: str) -> str:
        raw = str(identifier or "").strip()
        with contextlib.suppress(SandboxImageError):
            digest = validate_digest(raw)
            if self._image_path(digest).is_dir():
                return digest
        reference = normalize_image_reference(raw)
        digest = self._find_reference_locked(reference)
        if digest is None:
            raise SandboxImageError(f"sandbox image {identifier!r} is not cached")
        return digest

    def _delete_path_locked(self, digest: str, path: Path) -> None:
        expected = self._image_path(digest)
        if path != expected or path.is_symlink() or not path.is_dir():
            raise SandboxImageError(f"refusing unsafe sandbox image deletion at {path}")
        aliases = {
            reference: target
            for reference, target in self._read_aliases_locked().items()
            if target != digest
        }
        self._atomic_write_json(self.config.cache_dir / "aliases.json", aliases)
        shutil.rmtree(path)
        self._fsync_directory(self.config.cache_dir)

    def _broken_info(self, digest: str, path: Path, error: str) -> SandboxImageInfo:
        return SandboxImageInfo(
            digest=digest,
            reference="",
            references=(),
            status="broken",
            created_at="",
            last_used_at="",
            size_bytes=None,
            runtime_error=error,
        )

    def _skopeo_command(self, command: str) -> list[str]:
        if command not in {"inspect", "copy"}:
            raise SandboxImageError(f"unsupported skopeo command {command!r}")
        result = [str(self.config.skopeo), command]
        if self.config.auth_file is not None:
            auth_file = self.config.auth_file
            if auth_file.is_symlink() or not auth_file.is_file():
                raise SandboxImageError(
                    f"registry auth file is not a regular non-symlink file: {auth_file}"
                )
            option = "--src-authfile" if command == "copy" else "--authfile"
            result.extend([option, str(auth_file)])
        return result

    def _require_tools(self) -> None:
        for label, executable in (
            ("skopeo", self.config.skopeo),
            ("umoci", self.config.umoci),
        ):
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise SandboxImageError(
                    f"{label} not found at {executable}; run sandbox doctor"
                )

    def _run(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        operation: str,
        check: bool = True,
    ) -> tuple[int, str, str, bool]:
        try:
            process = subprocess.Popen(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError as exc:
            raise SandboxImageError(f"could not {operation}: {exc}") from exc
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
                if len(chunk) > max(remaining, 0):
                    truncated[index] = True

        threads = [
            threading.Thread(target=drain, args=(process.stdout, 0), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, 1), daemon=True),
        ]
        for thread in threads:
            thread.start()
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=2)
            raise SandboxImageError(f"timed out after {timeout:g}s while trying to {operation}") from exc
        finally:
            for thread in threads:
                thread.join(timeout=2)
        stdout = bytes(buffers[0]).decode("utf-8", "replace")
        stderr = bytes(buffers[1]).decode("utf-8", "replace")
        if check and returncode:
            detail = (stderr or stdout).strip()
            if truncated[0] or truncated[1]:
                detail += " [output truncated]"
            raise SandboxImageError(
                f"could not {operation}: {detail or f'exited {returncode}'}"
            )
        return returncode, stdout, stderr, any(truncated)

    @staticmethod
    def _pinned_reference(reference: str, digest: str) -> str:
        digest = validate_digest(digest)
        base = reference.rsplit("@", 1)[0]
        slash = base.rfind("/")
        colon = base.rfind(":")
        if colon > slash:
            base = base[:colon]
        return f"{base}@{digest}"

    def _image_path(self, digest: str) -> Path:
        digest = validate_digest(digest)
        path = self.config.cache_dir / digest.replace(":", "-")
        if path.parent != self.config.cache_dir:
            raise SandboxImageError("sandbox image path escaped the cache directory")
        return path

    @staticmethod
    def _digest_from_directory(name: str) -> str | None:
        if not re.fullmatch(r"sha256-[0-9a-f]{64}", name):
            return None
        return name.replace("-", ":", 1)

    def _ensure_layout(self) -> None:
        self.config.cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.config.cache_dir.is_symlink() or not self.config.cache_dir.is_dir():
            raise SandboxImageError(
                f"sandbox image cache is not a safe directory: {self.config.cache_dir}"
            )
        with contextlib.suppress(PermissionError):
            self.config.cache_dir.chmod(0o700)

    @contextlib.contextmanager
    def _cache_lock(self) -> Iterator[None]:
        self._ensure_layout()
        with self._thread_lock:
            lock_path = self.config.cache_dir / ".lock"
            if lock_path.is_symlink():
                raise SandboxImageError(f"refusing symlink image lock file {lock_path}")
            with lock_path.open("a+", encoding="utf-8") as handle:
                with contextlib.suppress(PermissionError):
                    os.fchmod(handle.fileno(), 0o600)
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _parse_timestamp(value: Any, label: str) -> dt.datetime:
        if not isinstance(value, str):
            raise SandboxImageError(f"image metadata {label} must be an ISO timestamp")
        try:
            parsed = dt.datetime.fromisoformat(value)
        except ValueError as exc:
            raise SandboxImageError(f"image metadata {label} is invalid") from exc
        if parsed.tzinfo is None:
            raise SandboxImageError(f"image metadata {label} must include a timezone")
        return parsed

    @staticmethod
    def _now() -> str:
        return dt.datetime.now(dt.timezone.utc).isoformat()

    @staticmethod
    def _allocated_bytes(path: Path) -> int:
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

    @staticmethod
    def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            SandboxImageManager._fsync_directory(path.parent)
        except BaseException:
            with contextlib.suppress(OSError):
                os.close(descriptor)
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
        descriptor, name = tempfile.mkstemp(prefix=".sandbox-image-doctor.", dir=path)
        temporary = Path(name)
        replacement = path / f"{temporary.name}.ok"
        try:
            os.write(descriptor, b"ok")
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, replacement)
            SandboxImageManager._fsync_directory(path)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)
            replacement.unlink(missing_ok=True)
