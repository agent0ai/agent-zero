import sys
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import pytest

# Direct import to avoid pulling in the full python.helpers package tree
_spec = importlib.util.spec_from_file_location(
    "metrics_collector",
    PROJECT_ROOT / "python" / "helpers" / "metrics_collector.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MetricsCollector = _mod.MetricsCollector


def _make_event(model="test-model", success=True, tokens_in=100, tokens_out=50,
                latency_ms=500, attempts=1, timestamp="2026-03-07T12:00:00Z"):
    return {
        "event_type": "llm_call",
        "model": model,
        "provider": "test-provider",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": latency_ms,
        "success": success,
        "error": None if success else "TestError: something failed",
        "stream": True,
        "attempts": attempts,
        "timestamp": timestamp,
    }


class TestMetricsCollectorEmpty:
    def test_empty_snapshot(self):
        c = MetricsCollector(maxlen=100)
        snap = c.snapshot()
        assert snap["total_calls"] == 0
        assert snap["success_calls"] == 0
        assert snap["failed_calls"] == 0
        assert snap["total_tokens_in"] == 0
        assert snap["total_tokens_out"] == 0
        assert snap["avg_latency_ms"] == 0
        assert snap["by_model"] == []
        assert snap["timeline"] == []
        assert snap["recent_events"] == []
        assert snap["recent_errors"] == []
        assert snap["buffer_size"] == 0
        assert snap["buffer_capacity"] == 100

    def test_uptime_positive(self):
        c = MetricsCollector()
        snap = c.snapshot()
        assert snap["uptime_seconds"] >= 0


class TestMetricsCollectorRecord:
    def test_single_event(self):
        c = MetricsCollector()
        c.record(_make_event())
        snap = c.snapshot()
        assert snap["total_calls"] == 1
        assert snap["success_calls"] == 1
        assert snap["failed_calls"] == 0
        assert snap["total_tokens_in"] == 100
        assert snap["total_tokens_out"] == 50
        assert snap["avg_latency_ms"] == 500
        assert snap["buffer_size"] == 1

    def test_multiple_events(self):
        c = MetricsCollector()
        c.record(_make_event(latency_ms=200))
        c.record(_make_event(latency_ms=800))
        snap = c.snapshot()
        assert snap["total_calls"] == 2
        assert snap["avg_latency_ms"] == 500

    def test_failed_event(self):
        c = MetricsCollector()
        c.record(_make_event(success=False, tokens_in=0, tokens_out=0))
        snap = c.snapshot()
        assert snap["total_calls"] == 1
        assert snap["success_calls"] == 0
        assert snap["failed_calls"] == 1
        assert len(snap["recent_errors"]) == 1
        assert "TestError" in snap["recent_errors"][0]["error"]

    def test_mixed_events(self):
        c = MetricsCollector()
        c.record(_make_event(success=True, latency_ms=100))
        c.record(_make_event(success=False, latency_ms=5000, tokens_in=0, tokens_out=0))
        c.record(_make_event(success=True, latency_ms=300))
        snap = c.snapshot()
        assert snap["total_calls"] == 3
        assert snap["success_calls"] == 2
        assert snap["failed_calls"] == 1
        assert snap["avg_latency_ms"] == 200  # only success events


class TestMetricsCollectorRingBuffer:
    def test_ring_overflow(self):
        c = MetricsCollector(maxlen=5)
        for i in range(10):
            c.record(_make_event(tokens_in=i))
        snap = c.snapshot()
        assert snap["buffer_size"] == 5
        assert snap["buffer_capacity"] == 5
        assert snap["total_calls"] == 5
        assert snap["total_tokens_in"] == 5 + 6 + 7 + 8 + 9


class TestMetricsCollectorByModel:
    def test_model_breakdown(self):
        c = MetricsCollector()
        c.record(_make_event(model="claude-sonnet", tokens_in=100))
        c.record(_make_event(model="claude-sonnet", tokens_in=200))
        c.record(_make_event(model="gpt-4o", tokens_in=50))
        snap = c.snapshot()
        assert len(snap["by_model"]) == 2
        models = {m["model"]: m for m in snap["by_model"]}
        assert models["claude-sonnet"]["calls"] == 2
        assert models["claude-sonnet"]["tokens_in"] == 300
        assert models["gpt-4o"]["calls"] == 1
        assert models["gpt-4o"]["tokens_in"] == 50

    def test_retries_tracked(self):
        c = MetricsCollector()
        c.record(_make_event(model="m1", attempts=3))
        c.record(_make_event(model="m1", attempts=1))
        snap = c.snapshot()
        models = {m["model"]: m for m in snap["by_model"]}
        assert models["m1"]["retries"] == 2  # 3-1 = 2 retries from first call


class TestMetricsCollectorClear:
    def test_clear(self):
        c = MetricsCollector()
        c.record(_make_event())
        c.record(_make_event())
        c.clear()
        snap = c.snapshot()
        assert snap["total_calls"] == 0
        assert snap["buffer_size"] == 0


class TestMetricsCollectorRecentEvents:
    def test_recent_events_order(self):
        c = MetricsCollector()
        c.record(_make_event(model="first", timestamp="2026-03-07T12:00:00Z"))
        c.record(_make_event(model="second", timestamp="2026-03-07T12:01:00Z"))
        snap = c.snapshot()
        assert snap["recent_events"][0]["model"] == "second"
        assert snap["recent_events"][1]["model"] == "first"

    def test_recent_events_capped_at_50(self):
        c = MetricsCollector(maxlen=200)
        for i in range(100):
            c.record(_make_event(model=f"m{i}"))
        snap = c.snapshot()
        assert len(snap["recent_events"]) == 50


class TestMetricsCollectorPercentiles:
    def test_percentiles(self):
        c = MetricsCollector()
        for ms in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
            c.record(_make_event(latency_ms=ms))
        snap = c.snapshot()
        assert snap["p50_latency_ms"] == 600
        assert snap["p95_latency_ms"] == 1000
        assert snap["p99_latency_ms"] == 1000

    def test_percentiles_single_event(self):
        c = MetricsCollector()
        c.record(_make_event(latency_ms=42))
        snap = c.snapshot()
        assert snap["p50_latency_ms"] == 42
        assert snap["p95_latency_ms"] == 42
        assert snap["p99_latency_ms"] == 42
