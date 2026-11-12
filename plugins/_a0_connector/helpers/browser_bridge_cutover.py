"""Versioned, read-only legacy Chrome bridge cutover primitives.

This foundation module deliberately detects and describes legacy installations
without importing their state or performing migration side effects. Runtime
quarantine, draining, persistence, pairing, and browser actions belong to later
vertical slices.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping


CUTOVER_CONTRACT = "a0.browser-bridge.cutover.v1"
CUTOVER_SCHEMA_VERSION = 1
LEGACY_PLUGIN_NAME = "chrome_extension"
LEGACY_PLUGIN_VERSION = "1.0.0"
MINIMUM_STRUCTURAL_MARKERS = 2
MAX_FINGERPRINT_FILE_BYTES = 64 * 1024


class LegacyDetectionState(str, Enum):
    """Safe public classification for a possible prototype installation."""

    ABSENT = "absent"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    CONFIRMED = "confirmed"


class CutoverState(str, Enum):
    """Server/operator states frozen by ``a0.browser-bridge.cutover.v1``."""

    NOT_DETECTED = "not_detected"
    LEGACY_DETECTED = "legacy_detected"
    V1_PAIRED_INACTIVE = "v1_paired_inactive"
    DRAINING_LEGACY = "draining_legacy"
    LEGACY_DISABLED = "legacy_disabled"
    LEGACY_LOCAL_PURGE_REQUIRED = "legacy_local_purge_required"
    READY_TO_ACTIVATE = "ready_to_activate"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    CANCELED = "canceled"


_NORMAL_TRANSITIONS: Mapping[CutoverState, frozenset[CutoverState]] = MappingProxyType(
    {
        CutoverState.NOT_DETECTED: frozenset({CutoverState.LEGACY_DETECTED}),
        CutoverState.LEGACY_DETECTED: frozenset({CutoverState.V1_PAIRED_INACTIVE}),
        CutoverState.V1_PAIRED_INACTIVE: frozenset({CutoverState.DRAINING_LEGACY}),
        CutoverState.DRAINING_LEGACY: frozenset({CutoverState.LEGACY_DISABLED}),
        CutoverState.LEGACY_DISABLED: frozenset(
            {
                CutoverState.LEGACY_LOCAL_PURGE_REQUIRED,
                CutoverState.READY_TO_ACTIVATE,
            }
        ),
        CutoverState.LEGACY_LOCAL_PURGE_REQUIRED: frozenset(
            {CutoverState.READY_TO_ACTIVATE}
        ),
        CutoverState.READY_TO_ACTIVATE: frozenset({CutoverState.VERIFYING}),
        CutoverState.VERIFYING: frozenset({CutoverState.COMPLETE}),
        CutoverState.COMPLETE: frozenset(),
        CutoverState.BLOCKED: frozenset(),
        CutoverState.CANCELED: frozenset(),
    }
)


@dataclass(frozen=True)
class LegacyBridgeDetection:
    """Redacted result of structurally fingerprinting a plugin directory."""

    state: LegacyDetectionState
    reason_code: str
    manifest_matched: bool
    matched_markers: tuple[str, ...] = ()
    inspected_marker_count: int = 0

    @property
    def confirmed(self) -> bool:
        return self.state is LegacyDetectionState.CONFIRMED

    def to_public_dict(self) -> dict[str, Any]:
        """Return the complete allowlisted public projection.

        No caller-provided path, manifest value, file content, exception, URL,
        token, or identifier can enter this projection.
        """

        return {
            "contract": CUTOVER_CONTRACT,
            "schema_version": CUTOVER_SCHEMA_VERSION,
            "state": self.state.value,
            "reason_code": self.reason_code,
            "manifest_matched": self.manifest_matched,
            "matched_marker_count": len(self.matched_markers),
            "inspected_marker_count": self.inspected_marker_count,
        }


@dataclass(frozen=True)
class _BoundedFileRead:
    exists: bool
    data: bytes = b""
    unavailable: bool = False


@dataclass(frozen=True)
class _MarkerInspection:
    matched: bool
    unavailable: bool = False


def can_transition_cutover(current: CutoverState, target: CutoverState) -> bool:
    """Return whether a normal or safe terminal transition is allowed."""

    if current == target:
        return True
    if current in {CutoverState.COMPLETE, CutoverState.BLOCKED, CutoverState.CANCELED}:
        return False
    if target in {CutoverState.BLOCKED, CutoverState.CANCELED}:
        return True
    return target in _NORMAL_TRANSITIONS[current]


def cutover_contract_schema() -> dict[str, Any]:
    """Return the versioned, mutation-independent public schema descriptor."""

    return {
        "contract": CUTOVER_CONTRACT,
        "schema_version": CUTOVER_SCHEMA_VERSION,
        "legacy_detection_states": [state.value for state in LegacyDetectionState],
        "cutover_states": [state.value for state in CutoverState],
        "minimum_structural_markers": MINIMUM_STRUCTURAL_MARKERS,
        "projection_fields": [
            "contract",
            "schema_version",
            "state",
            "reason_code",
            "manifest_matched",
            "matched_marker_count",
            "inspected_marker_count",
        ],
    }


def detect_legacy_browser_bridge(plugin_root: str | Path | None) -> LegacyBridgeDetection:
    """Fingerprint a possible legacy plugin without returning any raw values.

    Confirmation requires the exact legacy manifest identity plus at least two
    independent structural markers. Reads are bounded and symlinks are rejected
    so an untrusted plugin tree cannot redirect fingerprinting outside its root.
    """

    if plugin_root is None:
        return _result(LegacyDetectionState.ABSENT, "legacy_bridge_absent", False, (), 0)

    try:
        raw_root = Path(plugin_root)
        root_stat = raw_root.lstat()
    except FileNotFoundError:
        return _result(LegacyDetectionState.ABSENT, "legacy_bridge_absent", False, (), 0)
    except (OSError, RuntimeError, TypeError, ValueError):
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_detection_unavailable",
            False,
            (),
            0,
        )
    if stat.S_ISLNK(root_stat.st_mode):
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_root_untrusted",
            False,
            (),
            0,
        )
    if not stat.S_ISDIR(root_stat.st_mode):
        return _result(
            LegacyDetectionState.PARTIAL,
            "legacy_bridge_fingerprint_incomplete",
            False,
            (),
            0,
        )

    root_fd: int | None = None
    try:
        root_fd = os.open(
            raw_root,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        opened_root_stat = os.fstat(root_fd)
    except (OSError, RuntimeError, TypeError, ValueError):
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_detection_unavailable",
            False,
            (),
            0,
        )
    if (
        not stat.S_ISDIR(opened_root_stat.st_mode)
        or opened_root_stat.st_dev != root_stat.st_dev
        or opened_root_stat.st_ino != root_stat.st_ino
    ):
        os.close(root_fd)
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_root_changed",
            False,
            (),
            0,
        )

    try:
        manifest, manifest_unavailable = _read_yaml_mapping(root_fd, "plugin.yaml")
        manifest_matched = bool(
            manifest
            and manifest.get("name") == LEGACY_PLUGIN_NAME
            and str(manifest.get("version") or "") == LEGACY_PLUGIN_VERSION
        )

        marker_inspections = {
            name: predicate(root_fd) for name, predicate in _STRUCTURAL_MARKERS.items()
        }
    except (OSError, RuntimeError, TypeError, ValueError):
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_detection_unavailable",
            False,
            (),
            0,
        )
    finally:
        os.close(root_fd)
    markers = tuple(
        name for name, inspection in marker_inspections.items() if inspection.matched
    )
    inspected = sum(
        not inspection.unavailable for inspection in marker_inspections.values()
    )
    if manifest_unavailable or any(
        inspection.unavailable for inspection in marker_inspections.values()
    ):
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_detection_unavailable",
            manifest_matched,
            markers,
            inspected,
        )
    if manifest_matched and len(markers) >= MINIMUM_STRUCTURAL_MARKERS:
        return _result(
            LegacyDetectionState.CONFIRMED,
            "legacy_bridge_detected",
            True,
            markers,
            inspected,
        )
    return _result(
        LegacyDetectionState.PARTIAL,
        "legacy_bridge_fingerprint_incomplete",
        manifest_matched,
        markers,
        inspected,
    )


def detect_legacy_browser_bridge_roots(
    plugin_roots: Iterable[str | Path],
) -> LegacyBridgeDetection:
    """Inspect roots in runtime precedence order and return the first present one."""

    strongest = _result(
        LegacyDetectionState.ABSENT,
        "legacy_bridge_absent",
        False,
        (),
        0,
    )
    for plugin_root in plugin_roots:
        candidate = detect_legacy_browser_bridge(plugin_root)
        if candidate.state is not LegacyDetectionState.ABSENT:
            return candidate
    return strongest


def detect_installed_legacy_browser_bridge() -> LegacyBridgeDetection:
    """Inspect canonical Agent Zero roots without changing plugin state."""

    try:
        return detect_legacy_browser_bridge_roots(_installed_legacy_plugin_roots())
    except Exception:
        return _result(
            LegacyDetectionState.UNKNOWN,
            "legacy_bridge_detection_unavailable",
            False,
            (),
            0,
        )


def _installed_legacy_plugin_roots() -> Iterable[str | Path]:
    from helpers import plugins

    return plugins.get_plugin_roots(LEGACY_PLUGIN_NAME)


def build_cutover_foundation_status(
    detection: LegacyBridgeDetection,
) -> dict[str, Any]:
    """Describe detection and quarantine truth without claiming side effects."""

    if detection.confirmed:
        state = CutoverState.LEGACY_DETECTED.value
        quarantine_reason = "foundation_detection_only"
    elif detection.state is LegacyDetectionState.ABSENT:
        state = CutoverState.NOT_DETECTED.value
        quarantine_reason = detection.reason_code
    else:
        state = CutoverState.BLOCKED.value
        quarantine_reason = detection.reason_code
    return {
        "contract": CUTOVER_CONTRACT,
        "schema_version": CUTOVER_SCHEMA_VERSION,
        "state": state,
        "legacy": detection.to_public_dict(),
        "quarantine": {
            "state": "not_applied",
            "reason_code": quarantine_reason,
        },
    }


def _result(
    state: LegacyDetectionState,
    reason_code: str,
    manifest_matched: bool,
    markers: tuple[str, ...],
    inspected: int,
) -> LegacyBridgeDetection:
    return LegacyBridgeDetection(
        state=state,
        reason_code=reason_code,
        manifest_matched=manifest_matched,
        matched_markers=tuple(sorted(markers)),
        inspected_marker_count=inspected,
    )


def _read_bounded_file(root_fd: int, relative_path: str) -> _BoundedFileRead:
    """Read one regular file through a no-follow descriptor walk rooted at ``root``."""

    parts = tuple(part for part in relative_path.split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        return _BoundedFileRead(exists=False)

    opened_fds: list[int] = []
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_fd = os.dup(root_fd)
        opened_fds.append(directory_fd)
        for part in parts[:-1]:
            entry_stat = os.stat(part, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(entry_stat.st_mode) or not stat.S_ISDIR(entry_stat.st_mode):
                return _BoundedFileRead(exists=False)
            directory_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            opened_fds.append(directory_fd)
            opened_directory_stat = os.fstat(directory_fd)
            if (
                opened_directory_stat.st_dev != entry_stat.st_dev
                or opened_directory_stat.st_ino != entry_stat.st_ino
            ):
                return _BoundedFileRead(exists=False, unavailable=True)

        entry_stat = os.stat(parts[-1], dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode) or not stat.S_ISREG(entry_stat.st_mode):
            return _BoundedFileRead(exists=False)
        file_fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
        opened_fds.append(file_fd)
        opened_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_dev != entry_stat.st_dev
            or opened_stat.st_ino != entry_stat.st_ino
        ):
            return _BoundedFileRead(exists=False, unavailable=True)

        chunks: list[bytes] = []
        remaining = MAX_FINGERPRINT_FILE_BYTES + 1
        while remaining:
            chunk = os.read(file_fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > MAX_FINGERPRINT_FILE_BYTES:
            return _BoundedFileRead(exists=False)
        final_stat = os.fstat(file_fd)
        if (
            final_stat.st_size != opened_stat.st_size
            or final_stat.st_mtime_ns != opened_stat.st_mtime_ns
            or final_stat.st_ctime_ns != opened_stat.st_ctime_ns
        ):
            return _BoundedFileRead(exists=False, unavailable=True)
        return _BoundedFileRead(exists=True, data=data)
    except FileNotFoundError:
        return _BoundedFileRead(exists=False)
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return _BoundedFileRead(exists=False, unavailable=True)
    finally:
        for file_descriptor in reversed(opened_fds):
            try:
                os.close(file_descriptor)
            except OSError:
                pass


def _read_text(root_fd: int, relative_path: str) -> tuple[str, bool]:
    result = _read_bounded_file(root_fd, relative_path)
    if not result.exists or result.unavailable:
        return "", result.unavailable
    try:
        return result.data.decode("utf-8"), False
    except UnicodeError:
        return "", False


def _read_yaml_mapping(root_fd: int, relative_path: str) -> tuple[dict[str, Any], bool]:
    text, unavailable = _read_text(root_fd, relative_path)
    if not text:
        return {}, unavailable
    # The legacy fingerprints use only top-level scalar keys. A deliberately
    # small parser avoids constructing arbitrary YAML objects from a third-party
    # plugin merely to identify those keys.
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (
            not separator
            or not key
            or any(
                ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                for ch in key
            )
        ):
            continue
        if value.startswith(("[", "{", "&", "*", "!", "|", ">")):
            continue
        parsed[key] = value.strip("\"'")
    return parsed, unavailable


def _tool_marker(root_fd: int) -> _MarkerInspection:
    text, unavailable = _read_text(root_fd, "tools/chrome_bridge.py")
    return _MarkerInspection(
        matched="class ChromeBridge" in text and "enqueue_command" in text,
        unavailable=unavailable,
    )


def _route_marker(root_fd: int) -> _MarkerInspection:
    required = {
        "api/session_upsert.py",
        "api/command_pull.py",
        "api/command_result.py",
    }
    results = [_read_bounded_file(root_fd, relative_path) for relative_path in required]
    return _MarkerInspection(
        matched=all(result.exists and not result.unavailable for result in results),
        unavailable=any(result.unavailable for result in results),
    )


def _context_marker(root_fd: int) -> _MarkerInspection:
    text, unavailable = _read_text(root_fd, "helpers/constants.py")
    required = {
        'SOURCE_NAME = "chrome_extension"',
        'CTX_BROWSER_SESSION_ID = "chrome_browser_session_id"',
        'CTX_CHROME_CAPABILITIES = "chrome_extension_capabilities"',
    }
    return _MarkerInspection(
        matched=all(value in text for value in required),
        unavailable=unavailable,
    )


def _config_marker(root_fd: int) -> _MarkerInspection:
    config, unavailable = _read_yaml_mapping(root_fd, "default_config.yaml")
    required = {
        "command_timeout_seconds",
        "redelivery_seconds",
        "stale_session_seconds",
        "max_inspect_nodes",
        "prompt_guidance",
    }
    return _MarkerInspection(
        matched=required.issubset(config),
        unavailable=unavailable,
    )


def _prompt_marker(root_fd: int) -> _MarkerInspection:
    required = {
        "prompts/agent.system.tool.chrome_bridge.md",
        "prompts/fw.chrome.system_context.md",
    }
    results = [_read_bounded_file(root_fd, relative_path) for relative_path in required]
    return _MarkerInspection(
        matched=all(result.exists and not result.unavailable for result in results),
        unavailable=any(result.unavailable for result in results),
    )


_STRUCTURAL_MARKERS = MappingProxyType(
    {
        "legacy_command_routes": _route_marker,
        "legacy_context_keys": _context_marker,
        "legacy_polling_config": _config_marker,
        "legacy_prompt_pair": _prompt_marker,
        "legacy_tool": _tool_marker,
    }
)
