from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from helpers import files, plugins

from plugins._sandboxing.helpers.images import (
    SandboxImageConfig,
    SandboxImageError,
    SandboxImageManager,
)
from plugins._sandboxing.helpers.manager import (
    SandboxConfig,
    SandboxError,
    SandboxManager,
    validate_name,
)


PLUGIN_NAME = "_sandboxing"
_manager_lock = threading.RLock()
_manager: SandboxManager | None = None
_manager_config: tuple[SandboxConfig, SandboxImageConfig] | None = None


def normalize_config(value: dict[str, Any] | None) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    default_type = str(raw.get("default_type", "temporary")).strip().lower()
    default_network = str(raw.get("default_network", "host")).strip().lower()
    default_sandbox = str(raw.get("default_sandbox") or "default").strip()
    try:
        validate_name(default_sandbox)
    except SandboxError:
        default_sandbox = "default"
    return {
        "runsc_path": str(raw.get("runsc_path") or "/usr/bin/runsc").strip(),
        "skopeo_path": str(raw.get("skopeo_path") or "/usr/bin/skopeo").strip(),
        "umoci_path": str(raw.get("umoci_path") or "/usr/bin/umoci").strip(),
        "default_image": str(
            raw.get("default_image") or "docker.io/library/python:3.13-slim-bookworm"
        ).strip(),
        "registry_auth_file": str(raw.get("registry_auth_file") or "").strip(),
        "image_cache_dir": str(
            raw.get("image_cache_dir") or "usr/plugins/_sandboxing/images"
        ).strip(),
        "state_dir": str(
            raw.get("state_dir") or "usr/plugins/_sandboxing/runtime"
        ).strip(),
        "runsc_root": str(
            raw.get("runsc_root") or "/dev/shm/agent-zero-runsc"
        ).strip(),
        "shared_dir": str(raw.get("shared_dir") or "usr/sandbox-shared").strip(),
        "default_sandbox": default_sandbox,
        "default_type": default_type
        if default_type in {"temporary", "permanent"}
        else "temporary",
        "default_network": default_network
        if default_network in {"host", "none"}
        else "host",
        "temporary_lifetime_days": _positive_float(
            raw.get("temporary_lifetime_days"), 7.0
        ),
        "image_lifetime_days": _positive_float(raw.get("image_lifetime_days"), 30.0),
        "image_pull_timeout": _positive_float(raw.get("image_pull_timeout"), 900.0),
        "image_unpack_timeout": _positive_float(
            raw.get("image_unpack_timeout"), 900.0
        ),
        "max_image_bytes": max(
            1_048_576, _integer(raw.get("max_image_bytes"), 17_179_869_184)
        ),
        "start_timeout": _positive_float(raw.get("start_timeout"), 8.0),
        "stop_timeout": _positive_float(raw.get("stop_timeout"), 3.0),
        "snapshot_timeout": _positive_float(raw.get("snapshot_timeout"), 300.0),
        "exec_timeout": _positive_float(raw.get("exec_timeout"), 600.0),
        "max_output_bytes": max(4096, _integer(raw.get("max_output_bytes"), 1_048_576)),
    }


def manager_config(
    *, agent: object | None = None
) -> tuple[SandboxConfig, SandboxImageConfig]:
    raw = normalize_config(plugins.get_plugin_config(PLUGIN_NAME, agent=agent) or {})
    state_dir = _absolute_path(raw["state_dir"])
    sandbox = SandboxConfig(
        runsc=_absolute_path(raw["runsc_path"]),
        instances_dir=state_dir / "instances",
        runsc_root=_absolute_path(raw["runsc_root"]),
        shared_dir=_absolute_path(raw["shared_dir"]),
        default_image=str(raw["default_image"]),
        temporary_lifetime_days=float(raw["temporary_lifetime_days"]),
        start_timeout=float(raw["start_timeout"]),
        stop_timeout=float(raw["stop_timeout"]),
        snapshot_timeout=float(raw["snapshot_timeout"]),
        exec_timeout=float(raw["exec_timeout"]),
        max_output_bytes=int(raw["max_output_bytes"]),
    )
    auth_file = str(raw["registry_auth_file"] or "")
    images = SandboxImageConfig(
        skopeo=_absolute_path(raw["skopeo_path"]),
        umoci=_absolute_path(raw["umoci_path"]),
        cache_dir=_absolute_path(raw["image_cache_dir"]),
        default_image=str(raw["default_image"]),
        auth_file=_absolute_path(auth_file) if auth_file else None,
        cleanup_days=float(raw["image_lifetime_days"]),
        pull_timeout=float(raw["image_pull_timeout"]),
        unpack_timeout=float(raw["image_unpack_timeout"]),
        max_output_bytes=int(raw["max_output_bytes"]),
        max_image_bytes=int(raw["max_image_bytes"]),
    )
    return sandbox, images


def get_manager(*, agent: object | None = None) -> SandboxManager:
    global _manager, _manager_config
    sandbox_config, image_config = manager_config(agent=agent)
    config = (sandbox_config, image_config)
    with _manager_lock:
        if _manager is None or _manager_config != config:
            try:
                images = SandboxImageManager(image_config)
            except SandboxImageError as exc:
                raise SandboxError(str(exc)) from exc
            _manager = SandboxManager(sandbox_config, images)
            _manager_config = config
        return _manager


def reset_manager() -> None:
    global _manager, _manager_config
    with _manager_lock:
        _manager = None
        _manager_config = None


def defaults(*, agent: object | None = None) -> tuple[str, str, str]:
    config = normalize_config(plugins.get_plugin_config(PLUGIN_NAME, agent=agent) or {})
    return (
        str(config["default_sandbox"]),
        str(config["default_type"]),
        str(config["default_network"]),
    )


def resolve_sandbox_name(destination: str, *, agent: object | None = None) -> str:
    destination = str(destination or "default").strip()
    default_name, _, _ = defaults(agent=agent)
    if destination == "default":
        return default_name
    if destination.startswith("sandbox:"):
        return destination.split(":", 1)[1]
    return destination


def _absolute_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path(files.get_abs_path(str(path)))
    return path.resolve(strict=False)


def _positive_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _integer(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
