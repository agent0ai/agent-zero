from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

_lock = threading.Lock()

_MAX_RECENT_STARTUP_PHASES = 32

_metrics: dict[str, Any] = {
    "booted_at": datetime.now(timezone.utc).isoformat(),
    "counters": {},
    "timers": {},
    "startup_phases": deque(maxlen=_MAX_RECENT_STARTUP_PHASES),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def increment(name: str, value: int = 1) -> None:
    if not name or value == 0:
        return
    try:
        with _lock:
            counters = _metrics["counters"]
            counters[name] = int(counters.get(name, 0)) + int(value)
    except Exception:
        # Fail-open by design.
        return


def observe_ms(name: str, duration_ms: float, *, status: str | None = None) -> None:
    if not name:
        return
    try:
        ms = max(0.0, float(duration_ms))
    except Exception:
        return

    try:
        with _lock:
            timers = _metrics["timers"]
            stat = timers.get(name) or {
                "count": 0,
                "error_count": 0,
                "total_ms": 0.0,
                "last_ms": 0.0,
                "max_ms": 0.0,
                "avg_ms": 0.0,
            }
            stat["count"] += 1
            stat["total_ms"] += ms
            stat["last_ms"] = ms
            stat["max_ms"] = max(float(stat["max_ms"]), ms)
            if status and status != "success":
                stat["error_count"] += 1
            stat["avg_ms"] = stat["total_ms"] / max(1, stat["count"])
            timers[name] = stat
    except Exception:
        # Fail-open by design.
        return


def record_startup_phase(name: str, duration_ms: float, *, status: str = "success", error: str | None = None) -> None:
    if not name:
        return
    try:
        with _lock:
            phases = _metrics["startup_phases"]
            payload = {
                "phase": name,
                "duration_ms": round(max(0.0, float(duration_ms)), 2),
                "status": status,
                "timestamp": _now_iso(),
            }
            if error:
                payload["error"] = str(error)
            phases.append(payload)
    except Exception:
        # Fail-open by design.
        return


def snapshot() -> dict[str, Any]:
    try:
        with _lock:
            timers = {
                key: {
                    "count": int(val.get("count", 0)),
                    "error_count": int(val.get("error_count", 0)),
                    "avg_ms": round(float(val.get("avg_ms", 0.0)), 2),
                    "last_ms": round(float(val.get("last_ms", 0.0)), 2),
                    "max_ms": round(float(val.get("max_ms", 0.0)), 2),
                }
                for key, val in (_metrics.get("timers") or {}).items()
            }
            return {
                "booted_at": _metrics.get("booted_at"),
                "counters": dict(_metrics.get("counters") or {}),
                "timers": timers,
                "startup_phases": list(_metrics.get("startup_phases") or []),
            }
    except Exception:
        return {"booted_at": _now_iso(), "counters": {}, "timers": {}, "startup_phases": []}


class Timer:
    def __init__(self, name: str):
        self.name = name
        self._started = 0.0

    def __enter__(self) -> Timer:
        self._started = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._started <= 0:
            return
        status = "error" if exc is not None else "success"
        elapsed_ms = (time.perf_counter() - self._started) * 1000.0
        observe_ms(self.name, elapsed_ms, status=status)


def timer(name: str) -> Timer:
    return Timer(name)
