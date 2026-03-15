import sys
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

import pytest

_spec = importlib.util.spec_from_file_location(
    "metrics_collector",
    PROJECT_ROOT / "python" / "helpers" / "metrics_collector.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MetricsCollector = _mod.MetricsCollector


def _ev(model="test-model", success=True, tokens_in=100, tokens_out=50,
        latency_ms=500, attempts=1, timestamp="2026-03-07T12:00:00Z",
        ttft_ms=None, prompt_tps=0, response_tps=0,
        usage_type=None, agent_name=None, context_id=None, project=None, chat_name=None):
    return {
        "event_type": "llm_call",
        "model": model,
        "provider": "test",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_ms": latency_ms,
        "ttft_ms": ttft_ms,
        "prompt_tps": prompt_tps,
        "response_tps": response_tps,
        "success": success,
        "error": None if success else "TestError: fail",
        "stream": True,
        "attempts": attempts,
        "timestamp": timestamp,
        "usage_type": usage_type,
        "agent_name": agent_name,
        "context_id": context_id,
        "project": project,
        "chat_name": chat_name,
    }


class TestEmpty:
    def test_empty_snapshot_keys(self):
        c = MetricsCollector(maxlen=100)
        snap = c.snapshot()
        assert snap["total_calls"] == 0
        for key in ["by_model", "by_usage_type", "by_agent", "by_project",
                     "timeline", "recent_events", "recent_errors"]:
            assert snap[key] == [], f"{key} should be empty"
        assert snap["avg_ttft_ms"] == 0
        assert snap["avg_prompt_tps"] == 0
        assert snap["avg_response_tps"] == 0


class TestBasicRecording:
    def test_single_event(self):
        c = MetricsCollector()
        c.record(_ev())
        snap = c.snapshot()
        assert snap["total_calls"] == 1
        assert snap["success_calls"] == 1
        assert snap["total_tokens_in"] == 100

    def test_failed_event(self):
        c = MetricsCollector()
        c.record(_ev(success=False, tokens_in=0, tokens_out=0))
        snap = c.snapshot()
        assert snap["failed_calls"] == 1
        assert len(snap["recent_errors"]) == 1

    def test_mixed(self):
        c = MetricsCollector()
        c.record(_ev(latency_ms=100))
        c.record(_ev(success=False, latency_ms=5000, tokens_in=0, tokens_out=0))
        c.record(_ev(latency_ms=300))
        snap = c.snapshot()
        assert snap["total_calls"] == 3
        assert snap["success_calls"] == 2
        assert snap["avg_latency_ms"] == 200


class TestRingBuffer:
    def test_overflow(self):
        c = MetricsCollector(maxlen=5)
        for i in range(10):
            c.record(_ev(tokens_in=i))
        snap = c.snapshot()
        assert snap["buffer_size"] == 5
        assert snap["total_tokens_in"] == 5 + 6 + 7 + 8 + 9


class TestPercentiles:
    def test_latency_percentiles(self):
        c = MetricsCollector()
        for ms in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
            c.record(_ev(latency_ms=ms))
        snap = c.snapshot()
        assert snap["p50_latency_ms"] == 600
        assert snap["p95_latency_ms"] == 1000


class TestTTFT:
    def test_ttft_aggregation(self):
        c = MetricsCollector()
        c.record(_ev(ttft_ms=100))
        c.record(_ev(ttft_ms=200))
        c.record(_ev(ttft_ms=300))
        snap = c.snapshot()
        assert snap["avg_ttft_ms"] == 200

    def test_ttft_none_ignored(self):
        c = MetricsCollector()
        c.record(_ev(ttft_ms=None))
        c.record(_ev(ttft_ms=100))
        snap = c.snapshot()
        assert snap["avg_ttft_ms"] == 100


class TestThroughput:
    def test_tps_averages(self):
        c = MetricsCollector()
        c.record(_ev(prompt_tps=100, response_tps=50))
        c.record(_ev(prompt_tps=200, response_tps=100))
        snap = c.snapshot()
        assert snap["avg_prompt_tps"] == 150.0
        assert snap["avg_response_tps"] == 75.0


class TestByModel:
    def test_model_breakdown(self):
        c = MetricsCollector()
        c.record(_ev(model="claude", tokens_in=100))
        c.record(_ev(model="claude", tokens_in=200))
        c.record(_ev(model="gpt", tokens_in=50))
        snap = c.snapshot()
        models = {m["name"]: m for m in snap["by_model"]}
        assert models["claude"]["calls"] == 2
        assert models["claude"]["tokens_in"] == 300
        assert models["gpt"]["calls"] == 1

    def test_retries_tracked(self):
        c = MetricsCollector()
        c.record(_ev(model="m1", attempts=3))
        snap = c.snapshot()
        assert snap["by_model"][0]["retries"] == 2

    def test_ttft_per_model(self):
        c = MetricsCollector()
        c.record(_ev(model="m1", ttft_ms=100))
        c.record(_ev(model="m1", ttft_ms=200))
        snap = c.snapshot()
        assert snap["by_model"][0]["avg_ttft_ms"] == 150


class TestByUsageType:
    def test_usage_type_split(self):
        c = MetricsCollector()
        c.record(_ev(usage_type="chat", tokens_in=100))
        c.record(_ev(usage_type="chat", tokens_in=200))
        c.record(_ev(usage_type="utility", tokens_in=50))
        snap = c.snapshot()
        types = {t["name"]: t for t in snap["by_usage_type"]}
        assert types["chat"]["calls"] == 2
        assert types["utility"]["calls"] == 1

    def test_none_usage_type(self):
        c = MetricsCollector()
        c.record(_ev(usage_type=None))
        snap = c.snapshot()
        assert snap["by_usage_type"][0]["name"] == "unknown"


class TestByAgent:
    def test_agent_breakdown(self):
        c = MetricsCollector()
        c.record(_ev(agent_name="A0"))
        c.record(_ev(agent_name="A0"))
        c.record(_ev(agent_name="A1"))
        snap = c.snapshot()
        agents = {a["name"]: a for a in snap["by_agent"]}
        assert agents["A0"]["calls"] == 2
        assert agents["A1"]["calls"] == 1


class TestByProject:
    def test_project_with_chats(self):
        c = MetricsCollector()
        c.record(_ev(project="proj1", context_id="c1", chat_name="Chat 1", tokens_in=100))
        c.record(_ev(project="proj1", context_id="c1", chat_name="Chat 1", tokens_in=200))
        c.record(_ev(project="proj1", context_id="c2", chat_name="Chat 2", tokens_in=50))
        c.record(_ev(project="proj2", context_id="c3", chat_name="Chat 3", tokens_in=300))
        snap = c.snapshot()

        projs = {p["name"]: p for p in snap["by_project"]}
        assert projs["proj1"]["calls"] == 3
        assert projs["proj1"]["tokens_in"] == 350
        assert len(projs["proj1"]["chats"]) == 2

        chats = {ch["context_id"]: ch for ch in projs["proj1"]["chats"]}
        assert chats["c1"]["calls"] == 2
        assert chats["c1"]["tokens_in"] == 300
        assert chats["c2"]["calls"] == 1

        assert projs["proj2"]["calls"] == 1
        assert len(projs["proj2"]["chats"]) == 1

    def test_no_project(self):
        c = MetricsCollector()
        c.record(_ev(project=None, context_id="c1"))
        snap = c.snapshot()
        assert snap["by_project"][0]["name"] == "No Project"


class TestRecentEvents:
    def test_order_and_cap(self):
        c = MetricsCollector(maxlen=200)
        for i in range(100):
            c.record(_ev(model=f"m{i}"))
        snap = c.snapshot()
        assert len(snap["recent_events"]) == 50
        assert snap["recent_events"][0]["model"] == "m99"

    def test_context_fields_present(self):
        c = MetricsCollector()
        c.record(_ev(usage_type="chat", agent_name="A0", project="proj", chat_name="Test Chat"))
        ev = c.snapshot()["recent_events"][0]
        assert ev["usage_type"] == "chat"
        assert ev["agent_name"] == "A0"
        assert ev["project"] == "proj"
        assert ev["chat_name"] == "Test Chat"


class TestClear:
    def test_clear(self):
        c = MetricsCollector()
        c.record(_ev())
        c.clear()
        snap = c.snapshot()
        assert snap["total_calls"] == 0
