"""
Prometheus metrics for Agent Zero.

Provides comprehensive metrics collection for:
- Agent performance (latency, throughput)
- Tool execution (duration, success rate)
- Memory operations (search, insert, delete)
- LLM usage (calls, tokens, costs)
- System resources (memory, CPU)
"""

import time
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info, generate_latest,
        REGISTRY, CollectorRegistry, multiprocess
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not installed
    class _MockMetric:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
    Counter = Gauge = Histogram = Summary = Info = _MockMetric

from .settings import get_settings
from python.helpers import files

# Thread-safe metrics access
_metrics_lock = threading.RLock()

# Global registry (for multiprocess support if needed)
registry = REGISTRY

# Agent Metrics
AGENT_REQUESTS_TOTAL = Counter(
    'agent_zero_requests_total',
    'Total number of agent requests',
    ['agent_id', 'profile', 'endpoint'],
    registry=registry
)

AGENT_RESPONSE_DURATION = Histogram(
    'agent_zero_response_duration_seconds',
    'Agent response time distribution',
    ['agent_id', 'profile'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf')),
    registry=registry
)

AGENT_ITERATIONS_TOTAL = Counter(
    'agent_zero_iterations_total',
    'Total agent monologue iterations',
    ['agent_id', 'profile'],
    registry=registry
)

AGENT_ERRORS_TOTAL = Counter(
    'agent_zero_errors_total',
    'Total agent errors',
    ['agent_id', 'profile', 'error_type', 'severity'],
    registry=registry
)

ACTIVE_AGENTS = Gauge(
    'agent_zero_active_agents',
    'Currently active agent contexts',
    registry=registry
)

# Tool Metrics
TOOL_CALLS_TOTAL = Counter(
    'agent_zero_tool_calls_total',
    'Total tool invocations',
    ['tool_name', 'agent_id', 'profile', 'result'],
    registry=registry
)

TOOL_EXECUTION_DURATION = Histogram(
    'agent_zero_tool_execution_duration_seconds',
    'Tool execution time distribution',
    ['tool_name', 'agent_id'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')),
    registry=registry
)

# Memory Metrics
MEMORY_SEARCH_DURATION = Histogram(
    'agent_zero_memory_search_duration_seconds',
    'Vector search latency',
    ['memory_subdir', 'search_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf')),
    registry=registry
)

MEMORY_INSERT_DURATION = Histogram(
    'agent_zero_memory_insert_duration_seconds',
    'Document insertion latency',
    ['memory_subdir'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf')),
    registry=registry
)

MEMORY_ENTRIES_TOTAL = Gauge(
    'agent_zero_memory_entries_total',
    'Total entries in vector DB',
    ['memory_subdir'],
    registry=registry
)

MEMORY_OPERATIONS_TOTAL = Counter(
    'agent_zero_memory_operations_total',
    'Memory operations count',
    ['memory_subdir', 'operation'],  # operation: search, insert, delete, update
    registry=registry
)

# LLM Metrics
LLM_CALLS_TOTAL = Counter(
    'agent_zero_llm_calls_total',
    'Total LLM API calls',
    ['provider', 'model', 'endpoint', 'status'],
    registry=registry
)

LLM_TOKEN_GENERATION = Histogram(
    'agent_zero_llm_tokens_generated',
    'Tokens generated per LLM call',
    ['provider', 'model'],
    buckets=(10, 50, 100, 250, 500, 1000, 2000, 5000, 10000, float('inf')),
    registry=registry
)

LLM_COST_ESTIMATED_USD = Summary(
    'agent_zero_llm_cost_estimated_usd',
    'Estimated cost per LLM call (if pricing known)',
    ['provider', 'model'],
    registry=registry
)

# MCP Metrics
MCP_CONNECTIONS_TOTAL = Counter(
    'agent_zero_mcp_connections_total',
    'MCP server connection attempts',
    ['server_name', 'type', 'result'],
    registry=registry
)

MCP_TOOL_CALLS_TOTAL = Counter(
    'agent_zero_mcp_tool_calls_total',
    'MCP tool invocations',
    ['server_name', 'tool_name', 'result'],
    registry=registry
)

MCP_TOOL_DURATION = Histogram(
    'agent_zero_mcp_tool_duration_seconds',
    'MCP tool execution time',
    ['server_name', 'tool_name'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')),
    registry=registry
)

# System Metrics
SYSTEM_MEMORY_USAGE_BYTES = Gauge(
    'agent_zero_system_memory_bytes',
    'Process memory usage',
    ['type'],  # type: rss, vms, shared
    registry=registry
)

SYSTEM_CPU_PERCENT = Gauge(
    'agent_zero_system_cpu_percent',
    'Process CPU usage percentage',
    registry=registry
)

UPTIME_SECONDS = Gauge(
    'agent_zero_uptime_seconds',
    'Agent Zero process uptime',
    registry=registry
)

# Build Info
BUILD_INFO = Info(
    'agent_zero_build_info',
    'Build information',
    registry=registry
)

# Initialize build info
try:
    version = get_settings().get('version', 'unknown')
except Exception:
    version = 'unknown'
BUILD_INFO.info({
    'version': version,
    'build_date': files.read_file('docker/run/build.txt')[:100] if files.exists('docker/run/build.txt') else 'dev'
})


class MetricsManager:
    """Manager for collecting and exposing metrics."""

    _instance: Optional['MetricsManager'] = None
    _lock = threading.RLock()
    _start_time: float = time.time()
    _agent_active_counts: Dict[str, int] = defaultdict(int)

    def __init__(self):
        self._registry = registry
        self._lock = threading.RLock()
        self._setup_multiprocess()

    @classmethod
    def get_instance(cls) -> 'MetricsManager':
        """Singleton accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _setup_multiprocess(self):
        """Setup multiprocess mode if enabled."""
        # In Docker/K8s with multiple workers, use multiprocess mode
        # This writes metrics to a directory shared between processes
        mp_dir = files.get_abs_path('tmp/metrics')
        files.mkdir(mp_dir, exist_ok=True)
        # prometheus_client will use this automatically if env var set
        # We could set PROMETHEUS_MULTIPROC_DIR here if needed

    # Agent lifecycle
    def agent_started(self, agent_id: str, profile: str):
        """Track agent context creation."""
        with self._lock:
            self._agent_active_counts[agent_id] += 1
            ACTIVE_AGENTS.set(len(self._agent_active_counts))
            AGENT_REQUESTS_TOTAL.labels(agent_id=agent_id, profile=profile, endpoint='start').inc()

    def agent_finished(self, agent_id: str, profile: str, duration: float, success: bool = True):
        """Track agent request completion."""
        with self._lock:
            if agent_id in self._agent_active_counts:
                self._agent_active_counts[agent_id] -= 1
                if self._agent_active_counts[agent_id] <= 0:
                    del self._agent_active_counts[agent_id]
            ACTIVE_AGENTS.set(len(self._agent_active_counts))
            AGENT_RESPONSE_DURATION.labels(agent_id=agent_id, profile=profile).observe(duration)
            AGENT_REQUESTS_TOTAL.labels(agent_id=agent_id, profile=profile, endpoint='response').inc()

    def agent_error(self, agent_id: str, profile: str, error_type: str, severity: str = 'error'):
        """Track agent errors."""
        with self._lock:
            AGENT_ERRORS_TOTAL.labels(agent_id=agent_id, profile=profile, error_type=error_type, severity=severity).inc()

    def agent_iteration(self, agent_id: str, profile: str):
        """Track agent monologue iterations."""
        with self._lock:
            AGENT_ITERATIONS_TOTAL.labels(agent_id=agent_id, profile=profile).inc()

    # Tool metrics
    def tool_called(self, tool_name: str, agent_id: str, profile: str, result: str = 'success'):
        """Track tool invocation."""
        with self._lock:
            TOOL_CALLS_TOTAL.labels(tool_name=tool_name, agent_id=agent_id, profile=profile, result=result).inc()

    def tool_duration(self, tool_name: str, agent_id: str, duration: float):
        """Track tool execution time."""
        with self._lock:
            TOOL_EXECUTION_DURATION.labels(tool_name=tool_name, agent_id=agent_id).observe(duration)

    # Memory metrics
    def memory_search(self, memory_subdir: str, search_type: str = 'similarity', duration: float = 0.0):
        """Track memory search latency."""
        with self._lock:
            MEMORY_SEARCH_DURATION.labels(memory_subdir=memory_subdir, search_type=search_type).observe(duration)
            MEMORY_OPERATIONS_TOTAL.labels(memory_subdir=memory_subdir, operation='search').inc()

    def memory_insert(self, memory_subdir: str, duration: float = 0.0, count: int = 1):
        """Track memory insertion."""
        with self._lock:
            MEMORY_INSERT_DURATION.labels(memory_subdir=memory_subdir).observe(duration)
            MEMORY_OPERATIONS_TOTAL.labels(memory_subdir=memory_subdir, operation='insert').inc(count)
            # Update entry count gauge
            current = MEMORY_ENTRIES_TOTAL.labels(memory_subdir=memory_subdir)._value.get()
            MEMORY_ENTRIES_TOTAL.labels(memory_subdir=memory_subdir).set(current + count)

    def memory_delete(self, memory_subdir: str, count: int = 1):
        """Track memory deletion."""
        with self._lock:
            MEMORY_OPERATIONS_TOTAL.labels(memory_subdir=memory_subdir, operation='delete').inc(count)
            current = MEMORY_ENTRIES_TOTAL.labels(memory_subdir=memory_subdir)._value.get()
            MEMORY_ENTRIES_TOTAL.labels(memory_subdir=memory_subdir).set(max(0, current - count))

    # LLM metrics
    def llm_call(self, provider: str, model: str, endpoint: str = 'chat', status: str = 'success'):
        """Track LLM API call."""
        with self._lock:
            LLM_CALLS_TOTAL.labels(provider=provider, model=model, endpoint=endpoint, status=status).inc()

    def llm_tokens(self, provider: str, model: str, tokens: int):
        """Track token generation."""
        with self._lock:
            LLM_TOKEN_GENERATION.labels(provider=provider, model=model).observe(tokens)

    def llm_cost(self, provider: str, model: str, cost_usd: float):
        """Track LLM cost."""
        with self._lock:
            LLM_COST_ESTIMATED_USD.labels(provider=provider, model=model).observe(cost_usd)

    # MCP metrics
    def mcp_connection(self, server_name: str, mcp_type: str, success: bool = True):
        """Track MCP server connection."""
        with self._lock:
            result = 'success' if success else 'failed'
            MCP_CONNECTIONS_TOTAL.labels(server_name=server_name, type=mcp_type, result=result).inc()

    def mcp_tool_call(self, server_name: str, tool_name: str, duration: float, success: bool = True):
        """Track MCP tool execution."""
        with self._lock:
            result = 'success' if success else 'failed'
            MCP_TOOL_CALLS_TOTAL.labels(server_name=server_name, tool_name=tool_name, result=result).inc()
            MCP_TOOL_DURATION.labels(server_name=server_name, tool_name=tool_name).observe(duration)

    # System metrics
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            import psutil
            process = psutil.Process()
            with self._lock:
                mem_info = process.memory_info()
                SYSTEM_MEMORY_USAGE_BYTES.labels(type='rss').set(mem_info.rss)
                SYSTEM_MEMORY_USAGE_BYTES.labels(type='vms').set(mem_info.vms)
                if hasattr(mem_info, 'shared'):
                    SYSTEM_MEMORY_USAGE_BYTES.labels(type='shared').set(mem_info.shared)
                SYSTEM_CPU_PERCENT.set(process.cpu_percent(interval=0.1))
        except ImportError:
            pass

    def update_uptime(self):
        """Update uptime metric."""
        with self._lock:
            UPTIME_SECONDS.set(time.time() - self._start_time)

    # Metrics export
    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics output."""
        with self._lock:
            self.update_system_metrics()
            self.update_uptime()
            return generate_latest(self._registry)


def get_metrics_manager() -> MetricsManager:
    """Get the global metrics manager instance."""
    return MetricsManager.get_instance()
