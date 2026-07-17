"""Retention for Time Travel shadow repositories.

Time Travel keeps one hidden git repository per workspace under
``/a0/usr/.time_travel/workspaces/<workspace_id>/repo.git`` and snapshots it on every file
change. Without retention those repositories accumulate unboundedly: a removed chat or project
leaves its shadow repository orphaned forever (nothing cleans it up), and a workspace whose
``git add`` ever exceeded ``GIT_TIMEOUT_SECONDS`` strands a ``repo.git/index.lock`` that makes
every later snapshot fail with "index.lock: File exists".

The sweep (driven from ``job_loop``, throttled by config) removes:

- ORPHANS — shadow directories whose id matches no live workspace path. Live paths are
  forward-enumerated (project folders, the configured workdir, per-chat workdirs) and hashed
  with the same ``workspace_id_for`` derivation; anything outside that set has no owner and can
  never be shown in the UI again. Deleted once last activity is past a grace window.
- AGED repositories — no snapshot in ``retention_max_age_days`` (0 = keep forever, the
  default).
- STALE LOCKS — ``repo.git/index.lock`` older than ``retention_stale_lock_minutes``; Time
  Travel kills its git subprocesses at ``GIT_TIMEOUT_SECONDS``, so no legitimate lock lives
  that long. Removing it un-wedges future snapshots.
- INVALID BACKUPS — ``repo.git.invalid*`` set-asides made for corrupt repositories, past the
  same grace window.

Deleting a live workspace's shadow repository is always safe for the feature itself: the next
snapshot lazily re-initializes an empty history. Deletion is refused for any path outside the
shadow root.

Durable state next to the workspaces dir: ``retention.json`` (running totals + last sweep
stamp) and ``retention.log`` (one JSON line per sweep with the names of everything removed,
tail-capped).
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import time
from typing import Any, Optional

PLUGIN_NAME = "_time_travel"

MARKER_FILE = "retention.json"
HISTORY_FILE = "retention.log"
HISTORY_MAX_LINES = 1000

DEFAULT_CONFIG: dict[str, Any] = {
    "retention_enabled": True,
    "retention_sweep_interval_hours": 6,
    "retention_max_age_days": 0,
    "retention_orphan_grace_hours": 24,
    "retention_stale_lock_minutes": 30,
}


def _int_at_least(value: Any, minimum: int, fallback: int) -> int:
    try:
        return max(int(value), minimum)
    except Exception:
        return fallback


def effective_config(cfg: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Plugin config with defaults filled in and values clamped to sane minimums."""
    if cfg is None:
        try:
            from helpers import plugins

            cfg = plugins.get_plugin_config(PLUGIN_NAME) or {}
        except Exception:
            cfg = {}
    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in cfg.items() if k in DEFAULT_CONFIG and v is not None})
    merged["retention_enabled"] = bool(merged["retention_enabled"])
    merged["retention_sweep_interval_hours"] = _int_at_least(
        merged["retention_sweep_interval_hours"], 1, 6
    )
    merged["retention_max_age_days"] = _int_at_least(merged["retention_max_age_days"], 0, 0)
    merged["retention_orphan_grace_hours"] = _int_at_least(
        merged["retention_orphan_grace_hours"], 1, 24
    )
    merged["retention_stale_lock_minutes"] = _int_at_least(
        merged["retention_stale_lock_minutes"], 5, 30
    )
    return merged


def _state_dir() -> str:
    from plugins._time_travel.helpers import time_travel

    return str(time_travel.real_path_for_display("/a0/usr/.time_travel"))


def _shadow_root() -> str:
    from plugins._time_travel.helpers import time_travel

    return str(time_travel.real_path_for_display(time_travel.SHADOW_DISPLAY_ROOT))


def live_workspace_ids() -> set[str]:
    """Every workspace id resolvable from a path that exists right now: project folders, the
    configured workdir, and per-chat workdirs (custom projects resolvers may mint workspaces
    there; including them only makes the sweep more conservative)."""
    from plugins._time_travel.helpers import time_travel

    ids: set[str] = set()

    projects_root = time_travel.real_path_for_display("/a0/usr/projects")
    try:
        for name in os.listdir(projects_root):
            if os.path.isdir(os.path.join(projects_root, name)):
                ids.add(time_travel.workspace_id_for(f"/a0/usr/projects/{name}"))
    except Exception:
        pass

    try:
        ids.add(time_travel.workspace_id_for(time_travel.configured_workdir_display_path()))
    except Exception:
        ids.add(time_travel.workspace_id_for("/a0/usr/workdir"))

    chats_root = time_travel.real_path_for_display("/a0/usr/chats")
    try:
        for name in os.listdir(chats_root):
            if os.path.isdir(os.path.join(chats_root, name, "workdir")):
                ids.add(time_travel.workspace_id_for(f"/a0/usr/chats/{name}/workdir"))
    except Exception:
        pass

    return ids


def _read_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_marker(state_dir: str, sweep_stats: dict[str, int], stamp: str) -> None:
    try:
        os.makedirs(state_dir, exist_ok=True)
        path = os.path.join(state_dir, MARKER_FILE)
        payload = _read_json(path)
        payload["sweeps"] = int(payload.get("sweeps", 0)) + 1
        for key, value in sweep_stats.items():
            payload[key] = int(payload.get(key, 0)) + int(value)
        payload["last_sweep_at"] = stamp
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except Exception:
        pass


def _append_history(state_dir: str, entry: dict[str, Any]) -> None:
    try:
        os.makedirs(state_dir, exist_ok=True)
        path = os.path.join(state_dir, HISTORY_FILE)
        lines: list[str] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [ln for ln in f.read().splitlines() if ln.strip()]
        except Exception:
            lines = []
        lines.append(json.dumps(entry, sort_keys=True))
        if len(lines) > HISTORY_MAX_LINES:
            lines = lines[-HISTORY_MAX_LINES:]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, path)
    except Exception:
        pass


def read_history(limit: int = 50, state_dir: Optional[str] = None) -> list[dict[str, Any]]:
    try:
        base = state_dir if state_dir is not None else _state_dir()
        with open(os.path.join(base, HISTORY_FILE), "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        return [json.loads(ln) for ln in lines[-limit:]]
    except Exception:
        return []


def _last_activity(entry_path: str) -> float:
    candidates = [
        os.path.join(entry_path, "repo.git", "refs", "heads", "current"),
        os.path.join(entry_path, "repo.git", "packed-refs"),
        os.path.join(entry_path, "repo.git", "HEAD"),
        os.path.join(entry_path, "repo.git"),
        entry_path,
    ]
    newest = 0.0
    for candidate in candidates:
        try:
            newest = max(newest, os.stat(candidate).st_mtime)
        except Exception:
            continue
    return newest


def _tree_bytes(path: str) -> int:
    total = 0
    try:
        for root, _dirs, names in os.walk(path):
            for name in names:
                try:
                    total += os.stat(os.path.join(root, name)).st_size
                except Exception:
                    pass
    except Exception:
        pass
    return total


def _remove_tree(path: str, shadow_root: str) -> int:
    """rmtree guarded to the shadow root; returns bytes reclaimed (0 on refusal/failure)."""
    real = os.path.realpath(path)
    root = os.path.realpath(shadow_root)
    if not real.startswith(root + os.sep):
        return 0
    size = _tree_bytes(real)
    try:
        shutil.rmtree(real)
        return size
    except Exception:
        return 0


def sweep(
    cfg: Optional[dict[str, Any]] = None,
    shadow_root: Optional[str] = None,
    live_ids: Optional[set[str]] = None,
    now_ts: Optional[float] = None,
    state_dir: Optional[str] = None,
) -> dict[str, int]:
    """One retention pass. All inputs are injectable for tests; production callers pass
    nothing and everything resolves from the plugin runtime."""
    stats = {
        "orphans_removed": 0,
        "aged_removed": 0,
        "stale_locks_removed": 0,
        "invalid_backups_removed": 0,
        "bytes_reclaimed": 0,
    }
    config = effective_config(cfg)
    if not config["retention_enabled"]:
        return stats
    root = shadow_root if shadow_root is not None else _shadow_root()
    if not os.path.isdir(root):
        return stats
    ids = live_ids if live_ids is not None else live_workspace_ids()
    base = state_dir if state_dir is not None else _state_dir()
    now = time.time() if now_ts is None else now_ts

    max_age_s = config["retention_max_age_days"] * 86400
    grace_s = config["retention_orphan_grace_hours"] * 3600
    lock_s = config["retention_stale_lock_minutes"] * 60

    detail: dict[str, list[str]] = {"orphans": [], "aged": [], "locks": [], "invalid": []}

    try:
        entries = os.listdir(root)
    except Exception:
        return stats

    for name in entries:
        entry = os.path.join(root, name)
        if not os.path.isdir(entry):
            continue
        last = _last_activity(entry)

        if name not in ids:
            if now - last > grace_s:
                stats["bytes_reclaimed"] += _remove_tree(entry, root)
                stats["orphans_removed"] += 1
                detail["orphans"].append(name)
            continue

        if max_age_s and now - last > max_age_s:
            stats["bytes_reclaimed"] += _remove_tree(entry, root)
            stats["aged_removed"] += 1
            detail["aged"].append(name)
            continue

        lock = os.path.join(entry, "repo.git", "index.lock")
        try:
            if os.path.isfile(lock) and now - os.stat(lock).st_mtime > lock_s:
                os.remove(lock)
                stats["stale_locks_removed"] += 1
                detail["locks"].append(name)
        except Exception:
            pass

        try:
            for sub in os.listdir(entry):
                if sub.startswith("repo.git.invalid"):
                    backup = os.path.join(entry, sub)
                    if now - os.stat(backup).st_mtime > grace_s:
                        stats["bytes_reclaimed"] += _remove_tree(backup, root)
                        stats["invalid_backups_removed"] += 1
                        detail["invalid"].append(f"{name}/{sub}")
        except Exception:
            pass

    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _write_marker(base, stats, stamp)
    _append_history(base, {"at": stamp, **stats, "removed": detail})
    return stats


def due(
    cfg: Optional[dict[str, Any]] = None,
    now_ts: Optional[float] = None,
    state_dir: Optional[str] = None,
) -> bool:
    """True when retention is enabled and the configured interval has elapsed since the last
    sweep (or no sweep ever ran)."""
    config = effective_config(cfg)
    if not config["retention_enabled"]:
        return False
    base = state_dir if state_dir is not None else _state_dir()
    marker = _read_json(os.path.join(base, MARKER_FILE))
    last = str(marker.get("last_sweep_at") or "")
    if not last:
        return True
    try:
        last_dt = datetime.datetime.fromisoformat(last)
        now = (
            datetime.datetime.now(datetime.timezone.utc)
            if now_ts is None
            else datetime.datetime.fromtimestamp(now_ts, datetime.timezone.utc)
        )
        interval_s = config["retention_sweep_interval_hours"] * 3600
        return (now - last_dt).total_seconds() >= interval_s
    except Exception:
        return True
