"""Private, bounded artifact receiver for the frozen browser bridge protocol.

The receiver is process-only and inactive without an injected current-route
authorizer.  It does not reuse the legacy connector chunk assembler, expose
spool paths, wire Socket.IO events, or advertise browser runtime readiness.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time
from typing import Any, BinaryIO, Callable, Generic, TypeVar

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_transport_principal_identity,
)


CONTRACT_VERSION = 1
ARTIFACT_CHUNK_EVENT = "connector_browser_artifact_chunk"
MAX_ARTIFACT_BYTES = 25 * 1024 * 1024
MAX_CHUNK_BYTES = 192 * 1024
MAX_IDENTIFIER_BYTES = 256
MAX_MIME_TYPE_BYTES = 256
MAX_PURPOSE_BYTES = 128
DEFAULT_TTL_MS = 120_000
DEFAULT_TOMBSTONE_TTL_MS = 300_000
DEFAULT_MAX_ARTIFACTS = 16
DEFAULT_MAX_TOTAL_SPOOL_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_TOMBSTONES = 2_048
HARD_MAX_ARTIFACTS = 128
HARD_MAX_TOTAL_SPOOL_BYTES = 256 * 1024 * 1024
HARD_MAX_TOMBSTONES = 8_192
HARD_MAX_TTL_MS = 10 * 60 * 1_000

ARTIFACT_DIRECTIONS = frozenset({"output", "input"})
OUTPUT_PURPOSES = frozenset({"screenshot", "download"})
INPUT_PURPOSES = frozenset({"upload_file"})
ARTIFACT_PURPOSES = OUTPUT_PURPOSES | INPUT_PURPOSES

_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}")
_PURPOSE_RE = re.compile(r"[a-z][a-z0-9._-]{0,127}")
_MIME_TYPE_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/"
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}"
)


class BrowserBridgeArtifactError(RuntimeError):
    """Typed, redacted artifact failure suitable for a transport abort."""

    def __init__(self, code: str, *, aborted: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.aborted = aborted


@dataclass(frozen=True, slots=True)
class ArtifactBinding:
    """Every authority and operation dimension for one artifact transfer."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    bridge_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str
    artifact_id: str
    direction: str
    purpose: str
    contract_version: int = CONTRACT_VERSION
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    )

    def __post_init__(self) -> None:
        if type(self.contract_version) is not int or self.contract_version != 1:
            raise BrowserBridgeArtifactError("VERSION_MISMATCH")
        principal = self.principal
        try:
            profile = require_browser_bridge_transport_profile(
                self.transport_profile
            )
            require_transport_principal_identity(principal, profile)
        except ValueError:
            raise BrowserBridgeArtifactError("SCOPE_DENIED") from None
        if "browser.artifact" not in principal.scopes:
            raise BrowserBridgeArtifactError("SCOPE_DENIED")
        for field in (
            "connector_sid",
            "load_generation_id",
            "bridge_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "action_id",
            "op_id",
            "artifact_id",
        ):
            _identifier(getattr(self, field))
        if self.bridge_id != principal.principal_id:
            raise BrowserBridgeArtifactError("SCOPE_DENIED")
        if self.direction not in ARTIFACT_DIRECTIONS:
            raise BrowserBridgeArtifactError("INVALID_DIRECTION")
        purpose = _bounded_ascii_token(
            self.purpose,
            max_bytes=MAX_PURPOSE_BYTES,
            pattern=_PURPOSE_RE,
            code="INVALID_PURPOSE",
        )
        if purpose not in ARTIFACT_PURPOSES:
            raise BrowserBridgeArtifactError("INVALID_PURPOSE")
        if (
            self.direction == "output"
            and purpose not in OUTPUT_PURPOSES
        ) or (
            self.direction == "input"
            and purpose not in INPUT_PURPOSES
        ):
            raise BrowserBridgeArtifactError("INVALID_PURPOSE")
        permits_event = (
            principal.permits_inbound(ARTIFACT_CHUNK_EVENT, principal.handler_id)
            if self.direction == "output"
            else principal.permits_outbound(
                ARTIFACT_CHUNK_EVENT, principal.handler_id
            )
        )
        if not permits_event:
            raise BrowserBridgeArtifactError("SCOPE_DENIED")


@dataclass(frozen=True, slots=True)
class ArtifactProgress:
    artifact_id: str
    status: str
    next_chunk_index: int
    received_bytes: int


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    """Verified public result metadata. It intentionally has no spool path."""

    artifact_id: str
    mime_type: str
    byte_count: int
    sha256: str
    purpose: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "mime_type": self.mime_type,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
            "purpose": self.purpose,
        }


@dataclass(frozen=True, slots=True)
class ArtifactCleanupSummary:
    artifacts: int
    reserved_bytes: int


@dataclass(slots=True)
class _Transfer:
    binding: ArtifactBinding
    byte_count: int
    sha256: str
    mime_type: str
    path: Path
    writer: BinaryIO | None
    reader: BinaryIO | None
    digest: Any
    received_bytes: int
    next_chunk_index: int
    state: str
    expires_at_ms: int
    descriptor: ArtifactDescriptor | None = None


@dataclass(frozen=True, slots=True)
class _Tombstone:
    binding: ArtifactBinding
    status: str
    expires_at_ms: int


T = TypeVar("T")
CurrentRouteAuthorizer = Callable[[ArtifactBinding], bool]
ArtifactConsumer = Callable[[BinaryIO, ArtifactDescriptor], T]


class BrowserBridgeArtifactReceiver(Generic[T]):
    """Strict artifact state machine with private single-use spools."""

    def __init__(
        self,
        *,
        spool_parent: str | os.PathLike[str] | None = None,
        authorizer: CurrentRouteAuthorizer | None = None,
        clock_ms: Callable[[], int] | None = None,
        ttl_ms: int = DEFAULT_TTL_MS,
        tombstone_ttl_ms: int = DEFAULT_TOMBSTONE_TTL_MS,
        max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
        max_total_spool_bytes: int = DEFAULT_MAX_TOTAL_SPOOL_BYTES,
        max_tombstones: int = DEFAULT_MAX_TOMBSTONES,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        _constructor_bound(ttl_ms, 1, HARD_MAX_TTL_MS, "ttl_ms")
        _constructor_bound(
            tombstone_ttl_ms, 1, HARD_MAX_TTL_MS, "tombstone_ttl_ms"
        )
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        _constructor_bound(
            max_artifacts, 1, HARD_MAX_ARTIFACTS, "max_artifacts"
        )
        _constructor_bound(
            max_total_spool_bytes,
            1,
            HARD_MAX_TOTAL_SPOOL_BYTES,
            "max_total_spool_bytes",
        )
        _constructor_bound(
            max_tombstones, 1, HARD_MAX_TOMBSTONES, "max_tombstones"
        )
        parent = None if spool_parent is None else Path(spool_parent)
        if parent is not None:
            try:
                metadata = os.lstat(parent)
            except OSError:
                raise ValueError("spool_parent must be an existing directory") from None
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ValueError("spool_parent must be a non-symlink directory")
            parent = parent.resolve(strict=True)
        self._root = Path(
            tempfile.mkdtemp(prefix="a0-browser-artifacts-", dir=parent)
        )
        os.chmod(self._root, 0o700)
        self._authorizer = authorizer or (lambda _binding: False)
        self._clock_ms = clock_ms or (lambda: time.monotonic_ns() // 1_000_000)
        self._ttl_ms = ttl_ms
        self._tombstone_ttl_ms = tombstone_ttl_ms
        self._max_artifacts = max_artifacts
        self._max_total_spool_bytes = max_total_spool_bytes
        self._max_tombstones = max_tombstones
        self._transfers: dict[str, _Transfer] = {}
        self._tombstones: dict[str, _Tombstone] = {}
        self._tombstone_order: deque[str] = deque()
        self._reserved_bytes = 0
        self._closed = False
        self._lock = threading.RLock()

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._transfers)

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    @property
    def reserved_bytes(self) -> int:
        with self._lock:
            return self._reserved_bytes

    def begin(
        self,
        binding: ArtifactBinding,
        *,
        byte_count: int,
        sha256: str,
        mime_type: str,
    ) -> ArtifactProgress:
        binding = self._binding(binding)
        byte_count = _byte_count(byte_count)
        sha256 = _sha256(sha256)
        mime_type = _mime_type(mime_type)
        with self._lock:
            now = self._now_locked()
            self._ensure_open_locked()
            self._authorize_request_locked(binding, now)
            tombstone = self._tombstones.get(binding.artifact_id)
            if tombstone is not None:
                raise BrowserBridgeArtifactError("ARTIFACT_ID_REUSED")
            existing = self._transfers.get(binding.artifact_id)
            if existing is not None:
                if (
                    existing.byte_count != byte_count
                    or existing.sha256 != sha256
                    or existing.mime_type != mime_type
                ):
                    raise BrowserBridgeArtifactError("IDEMPOTENCY_CONFLICT")
                return self._progress(existing, "duplicate")
            if len(self._transfers) >= self._max_artifacts:
                raise BrowserBridgeArtifactError("ARTIFACT_REGISTRY_FULL")
            if self._reserved_bytes + byte_count > self._max_total_spool_bytes:
                raise BrowserBridgeArtifactError("ARTIFACT_SPOOL_FULL")

            try:
                descriptor, raw_path = tempfile.mkstemp(
                    prefix=".artifact-", suffix=".spool", dir=self._root
                )
                os.chmod(raw_path, 0o600)
                writer = os.fdopen(descriptor, "wb", buffering=0)
            except Exception:
                try:
                    if "descriptor" in locals():
                        os.close(descriptor)
                except OSError:
                    pass
                try:
                    if "raw_path" in locals():
                        os.unlink(raw_path)
                except OSError:
                    pass
                raise BrowserBridgeArtifactError("SPOOL_UNAVAILABLE") from None

            transfer = _Transfer(
                binding=binding,
                byte_count=byte_count,
                sha256=sha256,
                mime_type=mime_type,
                path=Path(raw_path),
                writer=writer,
                reader=None,
                digest=hashlib.sha256(),
                received_bytes=0,
                next_chunk_index=0,
                state="receiving",
                expires_at_ms=now + self._ttl_ms,
            )
            self._transfers[binding.artifact_id] = transfer
            self._reserved_bytes += byte_count
            return self._progress(transfer, "accepted")

    def append(
        self,
        binding: ArtifactBinding,
        *,
        chunk_index: int,
        data: bytes,
    ) -> ArtifactProgress:
        binding = self._binding(binding)
        with self._lock:
            now = self._now_locked()
            self._ensure_open_locked()
            self._authorize_request_locked(binding, now)
            transfer = self._transfer_locked(binding)
            if transfer.state != "receiving":
                raise BrowserBridgeArtifactError("ARTIFACT_ALREADY_COMPLETE")
            if (
                type(chunk_index) is not int
                or chunk_index < 0
                or chunk_index != transfer.next_chunk_index
            ):
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError("CHUNK_OUT_OF_ORDER", aborted=True)
            if not isinstance(data, bytes) or not data or len(data) > MAX_CHUNK_BYTES:
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError("CHUNK_SIZE_INVALID", aborted=True)
            if transfer.received_bytes + len(data) > transfer.byte_count:
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError("ARTIFACT_SIZE_MISMATCH", aborted=True)
            try:
                if transfer.writer is None:
                    raise OSError("closed writer")
                written = transfer.writer.write(data)
                if written != len(data):
                    raise OSError("short spool write")
            except Exception:
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError("SPOOL_UNAVAILABLE", aborted=True) from None
            transfer.digest.update(data)
            transfer.received_bytes += len(data)
            transfer.next_chunk_index += 1
            return self._progress(transfer, "accepted")

    def complete(self, binding: ArtifactBinding) -> ArtifactDescriptor:
        binding = self._binding(binding)
        with self._lock:
            now = self._now_locked()
            self._ensure_open_locked()
            self._authorize_request_locked(binding, now)
            transfer = self._transfer_locked(binding)
            if (
                transfer.state in {"complete", "consuming"}
                and transfer.descriptor is not None
            ):
                return transfer.descriptor
            actual_digest = f"sha256:{transfer.digest.hexdigest()}"
            if (
                transfer.received_bytes != transfer.byte_count
                or actual_digest != transfer.sha256
            ):
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError(
                    "ARTIFACT_INTEGRITY_MISMATCH", aborted=True
                )
            try:
                if transfer.writer is None:
                    raise OSError("closed writer")
                transfer.writer.flush()
                file_descriptor = transfer.writer.fileno()
                metadata = os.fstat(file_descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    raise OSError("spool is not a regular file")
                if metadata.st_size != transfer.byte_count:
                    self._abort_locked(transfer, "aborted", now)
                    raise BrowserBridgeArtifactError(
                        "ARTIFACT_INTEGRITY_MISMATCH", aborted=True
                    )
                os.fsync(file_descriptor)
                transfer.writer.close()
            except BrowserBridgeArtifactError:
                raise
            except Exception:
                self._abort_locked(transfer, "aborted", now)
                raise BrowserBridgeArtifactError("SPOOL_UNAVAILABLE", aborted=True) from None
            transfer.writer = None
            transfer.state = "complete"
            transfer.expires_at_ms = now + self._ttl_ms
            transfer.descriptor = ArtifactDescriptor(
                artifact_id=binding.artifact_id,
                mime_type=transfer.mime_type,
                byte_count=transfer.byte_count,
                sha256=transfer.sha256,
                purpose=binding.purpose,
            )
            return transfer.descriptor

    def abort(self, binding: ArtifactBinding) -> bool:
        binding = self._binding(binding)
        with self._lock:
            now = self._now_locked()
            self._ensure_open_locked()
            self._expire_locked(now)
            transfer = self._transfers.get(binding.artifact_id)
            if transfer is None:
                tombstone = self._tombstones.get(binding.artifact_id)
                if tombstone is not None and not _same_binding(
                    tombstone.binding, binding
                ):
                    raise BrowserBridgeArtifactError("SCOPE_DENIED")
                return False
            if not _same_binding(transfer.binding, binding):
                raise BrowserBridgeArtifactError("SCOPE_DENIED")
            self._abort_locked(transfer, "aborted", now)
            return True

    def consume(
        self,
        binding: ArtifactBinding,
        consumer: ArtifactConsumer[T],
    ) -> T:
        binding = self._binding(binding)
        if not callable(consumer):
            raise BrowserBridgeArtifactError("INVALID_CONSUMER")
        with self._lock:
            now = self._now_locked()
            self._ensure_open_locked()
            self._authorize_request_locked(binding, now)
            transfer = self._transfer_locked(binding)
            if transfer.state != "complete" or transfer.descriptor is None:
                raise BrowserBridgeArtifactError("ARTIFACT_NOT_COMPLETE")
            transfer.state = "consuming"
            path = transfer.path
            descriptor = transfer.descriptor

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        stream: BinaryIO | None = None
        file_descriptor: int | None = None
        exposed = False
        try:
            file_descriptor = os.open(path, flags)
            metadata = os.fstat(file_descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size != descriptor.byte_count
            ):
                os.close(file_descriptor)
                file_descriptor = None
                raise BrowserBridgeArtifactError(
                    "ARTIFACT_INTEGRITY_MISMATCH", aborted=True
                )
            stream = os.fdopen(file_descriptor, "rb", buffering=0)
            file_descriptor = None
            with self._lock:
                self._ensure_open_locked()
                if self._transfers.get(binding.artifact_id) is not transfer:
                    raise BrowserBridgeArtifactError("ARTIFACT_TERMINAL")
                transfer.reader = stream
                now = self._now_locked()
                # Opening the private file can race with credential revocation;
                # authorize again at the final boundary before exposing bytes.
                self._authorize_request_locked(binding, now)
                if self._transfers.get(binding.artifact_id) is not transfer:
                    raise BrowserBridgeArtifactError("ARTIFACT_TERMINAL")
                exposed = True
            return consumer(stream, descriptor)
        except BrowserBridgeArtifactError:
            raise
        except Exception:
            if not exposed:
                raise BrowserBridgeArtifactError("SPOOL_UNAVAILABLE") from None
            raise
        finally:
            with self._lock:
                if self._transfers.get(binding.artifact_id) is transfer:
                    try:
                        finished_at = self._now_locked()
                    except BrowserBridgeArtifactError:
                        finished_at = transfer.expires_at_ms
                    self._abort_locked(
                        transfer,
                        "consumed" if exposed else "aborted",
                        finished_at,
                    )
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass
            elif file_descriptor is not None:
                try:
                    os.close(file_descriptor)
                except OSError:
                    pass
            _unlink(path)

    def expire(self, now_ms: int | None = None) -> ArtifactCleanupSummary:
        with self._lock:
            self._ensure_open_locked()
            now = self._now_locked() if now_ms is None else _timestamp(now_ms)
            return self._expire_locked(now)

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
    ) -> ArtifactCleanupSummary:
        _identifier(connector_sid)
        _identifier(load_generation_id)
        with self._lock:
            self._ensure_open_locked()
            now = self._now_locked()
            transfers = [
                transfer
                for transfer in self._transfers.values()
                if transfer.binding.principal is principal
                and transfer.binding.connector_sid == connector_sid
                and transfer.binding.load_generation_id == load_generation_id
            ]
            return self._cleanup_locked(transfers, "disconnected", now)

    def revoke_bridge(
        self, *, bridge_id: str, key_generation: int
    ) -> ArtifactCleanupSummary:
        bridge_id = _identifier(bridge_id)
        if type(key_generation) is not int or key_generation < 1:
            raise BrowserBridgeArtifactError("INVALID_KEY_GENERATION")
        with self._lock:
            self._ensure_open_locked()
            now = self._now_locked()
            transfers = [
                transfer
                for transfer in self._transfers.values()
                if transfer.binding.bridge_id == bridge_id
                and transfer.binding.principal.key_generation == key_generation
            ]
            return self._cleanup_locked(transfers, "revoked", now)

    def close(self) -> ArtifactCleanupSummary:
        with self._lock:
            if self._closed:
                return ArtifactCleanupSummary(0, 0)
            try:
                now = self._now_locked()
            except BrowserBridgeArtifactError:
                now = 0
            summary = self._cleanup_locked(
                list(self._transfers.values()), "closed", now
            )
            self._closed = True
            self._tombstones.clear()
            self._tombstone_order.clear()
            try:
                for child in self._root.iterdir():
                    metadata = os.lstat(child)
                    if stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                        _unlink(child)
                os.rmdir(self._root)
            except Exception:
                # Every known spool has already been unlinked. Cleanup failure
                # must not resurrect state or leak a host path through errors.
                pass
            return summary

    def __enter__(self) -> BrowserBridgeArtifactReceiver[T]:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def _binding(self, binding: ArtifactBinding) -> ArtifactBinding:
        if (
            not isinstance(binding, ArtifactBinding)
            or binding.transport_profile is not self._transport_profile
        ):
            raise BrowserBridgeArtifactError("INVALID_BINDING")
        return binding

    def _authorize_locked(
        self,
        binding: ArtifactBinding,
        *,
        transfer: _Transfer | None = None,
        now: int | None = None,
    ) -> None:
        try:
            allowed = self._authorizer(binding) is True
        except Exception:
            allowed = False
        if allowed:
            return
        if transfer is not None and _same_binding(transfer.binding, binding):
            self._abort_locked(
                transfer,
                "authorization_lost",
                self._now_locked() if now is None else now,
            )
            raise BrowserBridgeArtifactError("SCOPE_DENIED", aborted=True)
        raise BrowserBridgeArtifactError("SCOPE_DENIED")

    def _authorize_request_locked(
        self, binding: ArtifactBinding, now: int
    ) -> None:
        """Authorize one exact request before observing or advancing its state."""

        transfer = self._transfers.get(binding.artifact_id)
        if transfer is not None and not _same_binding(transfer.binding, binding):
            raise BrowserBridgeArtifactError("SCOPE_DENIED")
        tombstone = self._tombstones.get(binding.artifact_id)
        if tombstone is not None and not _same_binding(tombstone.binding, binding):
            raise BrowserBridgeArtifactError("SCOPE_DENIED")
        self._authorize_locked(binding, transfer=transfer, now=now)
        self._expire_locked(now)

    def _transfer_locked(self, binding: ArtifactBinding) -> _Transfer:
        transfer = self._transfers.get(binding.artifact_id)
        if transfer is None:
            tombstone = self._tombstones.get(binding.artifact_id)
            if tombstone is not None:
                if not _same_binding(tombstone.binding, binding):
                    raise BrowserBridgeArtifactError("SCOPE_DENIED")
                raise BrowserBridgeArtifactError("ARTIFACT_TERMINAL")
            raise BrowserBridgeArtifactError("ARTIFACT_NOT_FOUND")
        if not _same_binding(transfer.binding, binding):
            raise BrowserBridgeArtifactError("SCOPE_DENIED")
        return transfer

    def _abort_locked(self, transfer: _Transfer, status: str, now: int) -> None:
        current = self._transfers.get(transfer.binding.artifact_id)
        if current is not transfer:
            return
        self._transfers.pop(transfer.binding.artifact_id, None)
        self._reserved_bytes -= transfer.byte_count
        if transfer.writer is not None:
            try:
                transfer.writer.close()
            except Exception:
                pass
            transfer.writer = None
        if transfer.reader is not None:
            try:
                transfer.reader.close()
            except Exception:
                pass
            transfer.reader = None
        _unlink(transfer.path)
        self._remember_locked(transfer.binding, status, now)

    def _cleanup_locked(
        self, transfers: list[_Transfer], status: str, now: int
    ) -> ArtifactCleanupSummary:
        count = 0
        reserved = 0
        for transfer in transfers:
            if self._transfers.get(transfer.binding.artifact_id) is not transfer:
                continue
            count += 1
            reserved += transfer.byte_count
            self._abort_locked(transfer, status, now)
        return ArtifactCleanupSummary(count, reserved)

    def _expire_locked(self, now: int) -> ArtifactCleanupSummary:
        expired = [
            transfer
            for transfer in self._transfers.values()
            if transfer.expires_at_ms <= now
        ]
        summary = self._cleanup_locked(expired, "expired", now)
        self._prune_tombstones_locked(now)
        return summary

    def _remember_locked(
        self, binding: ArtifactBinding, status: str, now: int
    ) -> None:
        artifact_id = binding.artifact_id
        if artifact_id not in self._tombstones:
            self._tombstone_order.append(artifact_id)
        self._tombstones[artifact_id] = _Tombstone(
            binding=binding,
            status=status,
            expires_at_ms=now + self._tombstone_ttl_ms,
        )
        self._prune_tombstones_locked(now)
        while len(self._tombstone_order) > self._max_tombstones:
            stale_id = self._tombstone_order.popleft()
            self._tombstones.pop(stale_id, None)

    def _prune_tombstones_locked(self, now: int) -> None:
        while self._tombstone_order:
            artifact_id = self._tombstone_order[0]
            tombstone = self._tombstones.get(artifact_id)
            if tombstone is not None and tombstone.expires_at_ms > now:
                break
            self._tombstone_order.popleft()
            self._tombstones.pop(artifact_id, None)

    def _now_locked(self) -> int:
        try:
            return _timestamp(self._clock_ms())
        except Exception:
            raise BrowserBridgeArtifactError("CLOCK_UNAVAILABLE") from None

    def _ensure_open_locked(self) -> None:
        if self._closed:
            raise BrowserBridgeArtifactError("RECEIVER_CLOSED")

    @staticmethod
    def _progress(transfer: _Transfer, status: str) -> ArtifactProgress:
        return ArtifactProgress(
            artifact_id=transfer.binding.artifact_id,
            status=status,
            next_chunk_index=transfer.next_chunk_index,
            received_bytes=transfer.received_bytes,
        )


def _same_binding(left: ArtifactBinding, right: ArtifactBinding) -> bool:
    return left.principal is right.principal and all(
        getattr(left, field) == getattr(right, field)
        for field in (
            "connector_sid",
            "load_generation_id",
            "bridge_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "action_id",
            "op_id",
            "artifact_id",
            "direction",
            "purpose",
            "contract_version",
            "transport_profile",
        )
    )


def _identifier(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > MAX_IDENTIFIER_BYTES
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise BrowserBridgeArtifactError("INVALID_BINDING")
    return value


def _bounded_ascii_token(
    value: Any,
    *,
    max_bytes: int,
    pattern: re.Pattern[str],
    code: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > max_bytes
        or pattern.fullmatch(value) is None
    ):
        raise BrowserBridgeArtifactError(code)
    return value


def _byte_count(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= MAX_ARTIFACT_BYTES:
        raise BrowserBridgeArtifactError("ARTIFACT_SIZE_INVALID")
    return value


def _sha256(value: Any) -> str:
    return _bounded_ascii_token(
        value,
        max_bytes=71,
        pattern=_SHA256_RE,
        code="ARTIFACT_DIGEST_INVALID",
    )


def _mime_type(value: Any) -> str:
    return _bounded_ascii_token(
        value,
        max_bytes=MAX_MIME_TYPE_BYTES,
        pattern=_MIME_TYPE_RE,
        code="ARTIFACT_MIME_INVALID",
    )


def _timestamp(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise BrowserBridgeArtifactError("CLOCK_UNAVAILABLE")
    return value


def _constructor_bound(value: Any, minimum: int, maximum: int, field: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{field} is outside its hard bound")
    return value


def _unlink(path: Path | str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError:
        pass
