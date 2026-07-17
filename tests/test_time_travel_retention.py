import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MOD_PATH = PROJECT_ROOT / "plugins" / "_time_travel" / "helpers" / "retention.py"
_spec = importlib.util.spec_from_file_location("time_travel_retention", MOD_PATH)
retention = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(retention)

DAY = 86400
HOUR = 3600
NOW = time.time()

CFG_AGING = {"retention_max_age_days": 30}


def _hex_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def _mk_repo(shadow_root, name, age_s, lock_age_s=None, invalid_age_s=None):
    entry = os.path.join(shadow_root, name)
    ref = os.path.join(entry, "repo.git", "refs", "heads")
    os.makedirs(ref, exist_ok=True)
    cur = os.path.join(ref, "current")
    with open(cur, "w") as f:
        f.write("deadbeef")
    stamp = NOW - age_s
    for path in (cur, os.path.join(entry, "repo.git"), entry):
        os.utime(path, (stamp, stamp))
    if lock_age_s is not None:
        lock = os.path.join(entry, "repo.git", "index.lock")
        with open(lock, "w") as f:
            f.write("")
        os.utime(lock, (NOW - lock_age_s, NOW - lock_age_s))
    if invalid_age_s is not None:
        backup = os.path.join(entry, "repo.git.invalid-20260101")
        os.makedirs(backup, exist_ok=True)
        with open(os.path.join(backup, "junk"), "w") as f:
            f.write("x" * 100)
        os.utime(backup, (NOW - invalid_age_s, NOW - invalid_age_s))
    return entry


def test_effective_config_defaults_and_clamps():
    cfg = retention.effective_config({})
    assert cfg["retention_enabled"] is True
    assert cfg["retention_max_age_days"] == 0
    assert cfg["retention_sweep_interval_hours"] == 6
    clamped = retention.effective_config(
        {
            "retention_sweep_interval_hours": 0,
            "retention_max_age_days": -5,
            "retention_orphan_grace_hours": 0,
            "retention_stale_lock_minutes": 1,
            "retention_enabled": 1,
        }
    )
    assert clamped["retention_sweep_interval_hours"] == 1
    assert clamped["retention_max_age_days"] == 0
    assert clamped["retention_orphan_grace_hours"] == 1
    assert clamped["retention_stale_lock_minutes"] == 5
    assert clamped["retention_enabled"] is True
    garbage = retention.effective_config({"retention_sweep_interval_hours": "nope"})
    assert garbage["retention_sweep_interval_hours"] == 6


def test_sweep_matrix(tmp_path):
    shadow = str(tmp_path / "workspaces")
    state = str(tmp_path / "state")
    os.makedirs(shadow)

    live_recent = _hex_id("alpha")
    live_aged = _hex_id("beta")
    live_locked = _hex_id("gamma")
    live_fresh_lock = _hex_id("delta")
    live_invalid = _hex_id("epsilon")
    live_ids = {live_recent, live_aged, live_locked, live_fresh_lock, live_invalid}

    _mk_repo(shadow, live_recent, age_s=1 * HOUR)
    _mk_repo(shadow, live_aged, age_s=40 * DAY)
    _mk_repo(shadow, live_locked, age_s=1 * HOUR, lock_age_s=1 * HOUR)
    _mk_repo(shadow, live_fresh_lock, age_s=1 * HOUR, lock_age_s=60)
    _mk_repo(shadow, live_invalid, age_s=1 * HOUR, invalid_age_s=48 * HOUR)
    _mk_repo(shadow, "0" * 32, age_s=48 * HOUR)  # orphan past grace
    _mk_repo(shadow, "1" * 32, age_s=1 * HOUR)  # orphan inside grace
    with open(os.path.join(shadow, "stray-file"), "w") as f:
        f.write("ignore me")

    stats = retention.sweep(
        cfg=CFG_AGING, shadow_root=shadow, live_ids=live_ids, now_ts=NOW, state_dir=state
    )

    assert os.path.isdir(os.path.join(shadow, live_recent))
    assert not os.path.exists(os.path.join(shadow, live_aged))
    assert stats["aged_removed"] == 1
    assert not os.path.exists(os.path.join(shadow, "0" * 32))
    assert os.path.isdir(os.path.join(shadow, "1" * 32))
    assert stats["orphans_removed"] == 1
    assert os.path.isdir(os.path.join(shadow, live_locked))
    assert not os.path.exists(os.path.join(shadow, live_locked, "repo.git", "index.lock"))
    assert os.path.exists(os.path.join(shadow, live_fresh_lock, "repo.git", "index.lock"))
    assert stats["stale_locks_removed"] == 1
    assert os.path.isdir(os.path.join(shadow, live_invalid))
    assert not os.path.exists(
        os.path.join(shadow, live_invalid, "repo.git.invalid-20260101")
    )
    assert stats["invalid_backups_removed"] == 1
    assert stats["bytes_reclaimed"] > 0
    assert os.path.isfile(os.path.join(shadow, "stray-file"))


def test_max_age_zero_keeps_history_forever(tmp_path):
    shadow = str(tmp_path / "workspaces")
    state = str(tmp_path / "state")
    os.makedirs(shadow)
    ancient = _hex_id("ancient")
    _mk_repo(shadow, ancient, age_s=400 * DAY)

    stats = retention.sweep(
        cfg={"retention_max_age_days": 0},
        shadow_root=shadow,
        live_ids={ancient},
        now_ts=NOW,
        state_dir=state,
    )
    assert stats["aged_removed"] == 0
    assert os.path.isdir(os.path.join(shadow, ancient))


def test_disabled_sweep_is_noop(tmp_path):
    shadow = str(tmp_path / "workspaces")
    os.makedirs(shadow)
    _mk_repo(shadow, "0" * 32, age_s=48 * HOUR)
    stats = retention.sweep(
        cfg={"retention_enabled": False},
        shadow_root=shadow,
        live_ids=set(),
        now_ts=NOW,
        state_dir=str(shadow),
    )
    assert stats["orphans_removed"] == 0
    assert os.path.isdir(os.path.join(shadow, "0" * 32))


def test_remove_tree_refuses_outside_root(tmp_path):
    shadow = str(tmp_path / "workspaces")
    outside = str(tmp_path / "outside")
    os.makedirs(shadow)
    os.makedirs(outside)
    assert retention._remove_tree(outside, shadow) == 0
    assert os.path.isdir(outside)


def test_marker_and_history(tmp_path):
    shadow = str(tmp_path / "workspaces")
    state = str(tmp_path / "state")
    os.makedirs(shadow)
    _mk_repo(shadow, "0" * 32, age_s=48 * HOUR)
    retention.sweep(cfg={}, shadow_root=shadow, live_ids=set(), now_ts=NOW, state_dir=state)
    _mk_repo(shadow, "2" * 32, age_s=48 * HOUR)
    retention.sweep(cfg={}, shadow_root=shadow, live_ids=set(), now_ts=NOW, state_dir=state)

    marker = json.load(open(os.path.join(state, retention.MARKER_FILE)))
    assert marker["sweeps"] == 2
    assert marker["orphans_removed"] == 2
    assert marker["last_sweep_at"]

    history = retention.read_history(state_dir=state)
    assert len(history) == 2
    assert history[0]["removed"]["orphans"] == ["0" * 32]
    assert history[1]["removed"]["orphans"] == ["2" * 32]
    assert history[0]["at"]


def test_history_tail_cap(tmp_path):
    state = str(tmp_path / "state")
    os.makedirs(state)
    with open(os.path.join(state, retention.HISTORY_FILE), "w") as f:
        for i in range(retention.HISTORY_MAX_LINES + 20):
            f.write('{"at": "old-%d"}\n' % i)
    retention._append_history(state, {"at": "newest"})
    history = retention.read_history(limit=retention.HISTORY_MAX_LINES + 100, state_dir=state)
    assert len(history) == retention.HISTORY_MAX_LINES
    assert history[-1]["at"] == "newest"
    assert history[0]["at"] != "old-0"


def test_due_throttle(tmp_path):
    state = str(tmp_path / "state")
    shadow = str(tmp_path / "workspaces")
    os.makedirs(shadow)
    assert retention.due(cfg={}, state_dir=state)
    assert not retention.due(cfg={"retention_enabled": False}, state_dir=state)

    retention.sweep(cfg={}, shadow_root=shadow, live_ids=set(), now_ts=NOW, state_dir=state)
    assert not retention.due(cfg={}, now_ts=time.time(), state_dir=state)
    assert retention.due(cfg={}, now_ts=time.time() + 7 * HOUR, state_dir=state)
    assert not retention.due(
        cfg={"retention_sweep_interval_hours": 12},
        now_ts=time.time() + 7 * HOUR,
        state_dir=state,
    )


def test_workspace_id_parity_with_time_travel():
    time_travel = pytest.importorskip(
        "plugins._time_travel.helpers.time_travel",
        reason="requires the full runtime environment",
    )
    path = "/a0/usr/projects/example"
    expected = hashlib.sha256(
        time_travel.canonical_workspace_display_path(path).rstrip("/").encode("utf-8")
    ).hexdigest()[:32]
    assert time_travel.workspace_id_for(path) == expected
