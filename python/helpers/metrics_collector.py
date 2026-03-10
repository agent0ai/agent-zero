"""
In-memory ring buffer for LLM usage metrics.
Collects events emitted by models.register_llm_callback and provides
aggregated snapshots for the metrics dashboard API.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any


_RING_SIZE = 2000  # max events in memory


class MetricsCollector:
    """Thread-safe ring buffer that stores LLM usage events."""

    def __init__(self, maxlen: int = _RING_SIZE):
        self._lock = threading.Lock()
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._started_at = time.time()

    # -- callback compatible with models.LLMUsageCallback --
    def record(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> dict[str, Any]:
        """Return aggregated metrics for the dashboard."""
        with self._lock:
            events = list(self._events)

        if not events:
            return self._empty_snapshot()

        total_calls = len(events)
        success_events = [e for e in events if e.get("success")]
        failed_events = [e for e in events if not e.get("success")]
        total_tokens_in = sum(e.get("tokens_in", 0) for e in events)
        total_tokens_out = sum(e.get("tokens_out", 0) for e in events)
        latencies = [e["latency_ms"] for e in success_events if "latency_ms" in e]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
        p50 = _percentile(latencies, 50)
        p95 = _percentile(latencies, 95)
        p99 = _percentile(latencies, 99)

        # per-model breakdown
        by_model: dict[str, dict] = {}
        for e in events:
            model = e.get("model", "unknown")
            entry = by_model.setdefault(model, {
                "model": model,
                "calls": 0,
                "success": 0,
                "failed": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "total_latency_ms": 0,
                "retries": 0,
            })
            entry["calls"] += 1
            if e.get("success"):
                entry["success"] += 1
            else:
                entry["failed"] += 1
            entry["tokens_in"] += e.get("tokens_in", 0)
            entry["tokens_out"] += e.get("tokens_out", 0)
            entry["total_latency_ms"] += e.get("latency_ms", 0)
            attempts = e.get("attempts", 1)
            if attempts > 1:
                entry["retries"] += attempts - 1

        model_stats = []
        for m in by_model.values():
            m["avg_latency_ms"] = int(m["total_latency_ms"] / m["calls"]) if m["calls"] else 0
            del m["total_latency_ms"]
            model_stats.append(m)
        model_stats.sort(key=lambda x: x["calls"], reverse=True)

        # timeline: bucket events into 1-minute windows (last 60 minutes)
        now = time.time()
        buckets: dict[int, dict] = {}
        for e in events:
            ts = e.get("timestamp", "")
            try:
                import datetime
                dt = datetime.datetime.fromisoformat(ts.rstrip("Z"))
                epoch = dt.timestamp()
            except Exception:
                epoch = now
            minute_key = int(epoch // 60) * 60
            b = buckets.setdefault(minute_key, {"ts": minute_key, "calls": 0, "tokens": 0, "errors": 0})
            b["calls"] += 1
            b["tokens"] += e.get("tokens_in", 0) + e.get("tokens_out", 0)
            if not e.get("success"):
                b["errors"] += 1

        timeline = sorted(buckets.values(), key=lambda x: x["ts"])[-60:]

        # recent errors
        recent_errors = []
        for e in reversed(failed_events[:20]):
            recent_errors.append({
                "model": e.get("model", "unknown"),
                "error": e.get("error", "unknown"),
                "timestamp": e.get("timestamp", ""),
                "attempts": e.get("attempts", 1),
            })

        # recent events (last 50)
        recent = []
        for e in reversed(events[-50:]):
            recent.append({
                "model": e.get("model", "unknown"),
                "provider": e.get("provider"),
                "tokens_in": e.get("tokens_in", 0),
                "tokens_out": e.get("tokens_out", 0),
                "latency_ms": e.get("latency_ms", 0),
                "success": e.get("success", False),
                "error": e.get("error"),
                "stream": e.get("stream", False),
                "attempts": e.get("attempts", 1),
                "timestamp": e.get("timestamp", ""),
            })

        return {
            "total_calls": total_calls,
            "success_calls": len(success_events),
            "failed_calls": len(failed_events),
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "by_model": model_stats,
            "timeline": timeline,
            "recent_errors": recent_errors,
            "recent_events": recent,
            "uptime_seconds": int(now - self._started_at),
            "buffer_size": len(events),
            "buffer_capacity": self._events.maxlen,
        }

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def _empty_snapshot(self) -> dict[str, Any]:
        return {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "avg_latency_ms": 0,
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0,
            "by_model": [],
            "timeline": [],
            "recent_errors": [],
            "recent_events": [],
            "uptime_seconds": int(time.time() - self._started_at),
            "buffer_size": 0,
            "buffer_capacity": self._events.maxlen,
        }


def _percentile(data: list[int], pct: int) -> int:
    if not data:
        return 0
    s = sorted(data)
    idx = int(len(s) * pct / 100)
    idx = min(idx, len(s) - 1)
    return s[idx]


# Singleton instance
collector = MetricsCollector()
