"""
LLM Router - Intelligent model selection and prioritization for Agent Jumbo

This module provides:
1. Auto-detection of available models (Ollama, cloud providers)
2. Prioritization rules based on cost, speed, capability
3. Fallback chains for model failures
4. Usage tracking and cost estimation
5. Context-aware model selection (USER, TASK, BACKGROUND)
"""

import asyncio
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from python.helpers.datetime_utils import isoformat_z, utc_now
from python.helpers.settings_core import get_default_ollama_base_url


class ModelCapability(Enum):
    """Model capabilities for routing decisions"""

    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    REASONING = "reasoning"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"
    FAST = "fast"
    CHEAP = "cheap"


class RoutingPriority(Enum):
    """Prioritization strategies"""

    COST = "cost"  # Minimize cost
    SPEED = "speed"  # Minimize latency
    QUALITY = "quality"  # Maximize capability
    BALANCED = "balanced"  # Balance all factors


@dataclass
class ModelInfo:
    """Information about an available model"""

    provider: str  # ollama, openai, anthropic, etc.
    name: str  # Model name/identifier
    display_name: str  # Human-readable name
    size_gb: float = 0.0  # Model size (for local models)
    context_length: int = 4096
    capabilities: list[str] = field(default_factory=list)
    cost_per_1k_input: float = 0.0  # USD per 1K input tokens
    cost_per_1k_output: float = 0.0  # USD per 1K output tokens
    avg_latency_ms: int = 0  # Average response latency
    is_local: bool = False
    is_available: bool = True
    last_checked: str | None = None
    priority_score: float = 0.0  # Computed routing score
    metadata: dict[str, Any] = field(default_factory=dict)
    # Prompt caching configuration
    supports_caching: bool = False  # Model supports prompt caching
    cache_enabled: bool = False  # Caching enabled for this model
    cache_ttl_seconds: int = 300  # Default cache TTL (5 minutes)
    # Advanced features
    supports_ptc: bool = False  # Programmatic Tool Calling
    supports_batch: bool = False  # Batch API support
    effort_levels: list[str] = field(default_factory=list)  # Available effort levels

    def to_dict(self) -> dict:
        return asdict(self)

    def to_camel_dict(self) -> dict:
        """Return dict with camelCase keys for JSON API responses."""
        d = asdict(self)
        _snake_to_camel = {
            "display_name": "displayName",
            "size_gb": "sizeGb",
            "context_length": "contextLength",
            "cost_per_1k_input": "costPer1kInput",
            "cost_per_1k_output": "costPer1kOutput",
            "avg_latency_ms": "avgLatencyMs",
            "is_local": "isLocal",
            "is_available": "isAvailable",
            "last_checked": "lastChecked",
            "priority_score": "priorityScore",
            "supports_caching": "supportsCaching",
            "cache_enabled": "cacheEnabled",
            "cache_ttl_seconds": "cacheTtlSeconds",
            "supports_ptc": "supportsPtc",
            "supports_batch": "supportsBatch",
            "effort_levels": "effortLevels",
        }
        return {_snake_to_camel.get(k, k): v for k, v in d.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "ModelInfo":
        return cls(**data)


@dataclass
class RoutingRule:
    """Rule for model selection"""

    name: str
    priority: int = 0  # Higher = more important
    condition: str = ""  # Python expression
    preferred_models: list[str] = field(default_factory=list)
    excluded_models: list[str] = field(default_factory=list)
    min_context_length: int = 0
    required_capabilities: list[str] = field(default_factory=list)
    max_cost_per_1k: float = 0.0  # 0 = no limit
    max_latency_ms: int = 0  # 0 = no limit
    enabled: bool = True


class LLMRouterDatabase:
    """SQLite database for router state and usage tracking"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            # Use data directory relative to project root
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "llm_router.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Available models registry
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY,
                    provider TEXT NOT NULL,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    size_gb REAL DEFAULT 0,
                    context_length INTEGER DEFAULT 4096,
                    capabilities TEXT DEFAULT '[]',
                    cost_per_1k_input REAL DEFAULT 0,
                    cost_per_1k_output REAL DEFAULT 0,
                    avg_latency_ms INTEGER DEFAULT 0,
                    is_local INTEGER DEFAULT 0,
                    is_available INTEGER DEFAULT 1,
                    last_checked TEXT,
                    priority_score REAL DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    UNIQUE(provider, name)
                );

                -- Usage tracking
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    context_type TEXT,
                    model_role TEXT
                );

                -- Routing rules
                CREATE TABLE IF NOT EXISTS routing_rules (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    priority INTEGER DEFAULT 0,
                    condition TEXT DEFAULT '',
                    preferred_models TEXT DEFAULT '[]',
                    excluded_models TEXT DEFAULT '[]',
                    min_context_length INTEGER DEFAULT 0,
                    required_capabilities TEXT DEFAULT '[]',
                    max_cost_per_1k REAL DEFAULT 0,
                    max_latency_ms INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1
                );

                -- Provider configuration
                CREATE TABLE IF NOT EXISTS provider_config (
                    id INTEGER PRIMARY KEY,
                    provider TEXT UNIQUE NOT NULL,
                    api_base TEXT,
                    is_enabled INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    last_health_check TEXT,
                    health_status TEXT DEFAULT 'unknown',
                    metadata TEXT DEFAULT '{}'
                );

                -- Model aliases (for easy switching)
                CREATE TABLE IF NOT EXISTS model_aliases (
                    id INTEGER PRIMARY KEY,
                    alias TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    description TEXT
                );

                -- Create indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage(timestamp);
                CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage(provider, model_name);
                CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
            """)

    def save_model(self, model: ModelInfo):
        """Save or update a model in the registry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO models
                (provider, name, display_name, size_gb, context_length, capabilities,
                 cost_per_1k_input, cost_per_1k_output, avg_latency_ms, is_local,
                 is_available, last_checked, priority_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    model.provider,
                    model.name,
                    model.display_name,
                    model.size_gb,
                    model.context_length,
                    json.dumps(model.capabilities),
                    model.cost_per_1k_input,
                    model.cost_per_1k_output,
                    model.avg_latency_ms,
                    1 if model.is_local else 0,
                    1 if model.is_available else 0,
                    model.last_checked,
                    model.priority_score,
                    json.dumps(model.metadata),
                ),
            )

    def get_models(self, provider: str | None = None, available_only: bool = True) -> list[ModelInfo]:
        """Get models from registry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM models WHERE 1=1"
            params = []

            if provider:
                query += " AND provider = ?"
                params.append(provider)
            if available_only:
                query += " AND is_available = 1"

            query += " ORDER BY priority_score DESC"

            rows = conn.execute(query, params).fetchall()
            return [
                ModelInfo(
                    provider=row["provider"],
                    name=row["name"],
                    display_name=row["display_name"] or row["name"],
                    size_gb=row["size_gb"],
                    context_length=row["context_length"],
                    capabilities=json.loads(row["capabilities"]),
                    cost_per_1k_input=row["cost_per_1k_input"],
                    cost_per_1k_output=row["cost_per_1k_output"],
                    avg_latency_ms=row["avg_latency_ms"],
                    is_local=bool(row["is_local"]),
                    is_available=bool(row["is_available"]),
                    last_checked=row["last_checked"],
                    priority_score=row["priority_score"],
                    metadata=json.loads(row["metadata"]),
                )
                for row in rows
            ]

    def mark_provider_models_unavailable(self, provider: str):
        """Mark all models for a provider as unavailable."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE models
                SET is_available = 0, last_checked = ?
                WHERE provider = ?
            """,
                (isoformat_z(utc_now()), provider),
            )

    def mark_all_models_unavailable(self, providers: list[str] | None = None):
        """Mark all models (or a provider subset) as unavailable before rediscovery."""
        with sqlite3.connect(self.db_path) as conn:
            if providers:
                placeholders = ",".join("?" for _ in providers)
                conn.execute(  # nosec B608 - placeholders are ? params, not user input
                    f"""
                    UPDATE models
                    SET is_available = 0, last_checked = ?
                    WHERE provider IN ({placeholders})
                """,
                    (isoformat_z(utc_now()), *providers),
                )
            else:
                conn.execute(
                    """
                    UPDATE models
                    SET is_available = 0, last_checked = ?
                """,
                    (isoformat_z(utc_now()),),
                )

    def record_usage(
        self,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error_message: str | None = None,
        context_type: str | None = None,
        model_role: str | None = None,
        cost_usd: float = 0,
    ):
        """Record model usage for tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO usage
                (provider, model_name, input_tokens, output_tokens, latency_ms,
                 cost_usd, success, error_message, context_type, model_role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    provider,
                    model_name,
                    input_tokens,
                    output_tokens,
                    latency_ms,
                    cost_usd,
                    1 if success else 0,
                    error_message,
                    context_type,
                    model_role,
                ),
            )

    def get_usage_stats(self, hours: int = 24) -> dict:
        """Get usage statistics for the past N hours"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            stats = conn.execute(
                """
                SELECT
                    provider,
                    model_name,
                    COUNT(*) as call_count,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
                FROM usage
                WHERE timestamp >= ?
                GROUP BY provider, model_name
            """,
                (cutoff,),
            ).fetchall()

            return {
                "periodHours": hours,
                "byModel": [
                    {
                        "provider": row["provider"],
                        "modelName": row["model_name"],
                        "callCount": row["call_count"],
                        "totalInputTokens": row["total_input_tokens"],
                        "totalOutputTokens": row["total_output_tokens"],
                        "totalCost": row["total_cost"],
                        "avgLatency": row["avg_latency"],
                        "successCount": row["success_count"],
                        "errorCount": row["error_count"],
                    }
                    for row in stats
                ],
                "totalCost": sum(row["total_cost"] or 0 for row in stats),
                "totalCalls": sum(row["call_count"] for row in stats),
            }

    def save_routing_rule(self, rule: RoutingRule):
        """Save a routing rule"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO routing_rules
                (name, priority, condition, preferred_models, excluded_models,
                 min_context_length, required_capabilities, max_cost_per_1k,
                 max_latency_ms, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rule.name,
                    rule.priority,
                    rule.condition,
                    json.dumps(rule.preferred_models),
                    json.dumps(rule.excluded_models),
                    rule.min_context_length,
                    json.dumps(rule.required_capabilities),
                    rule.max_cost_per_1k,
                    rule.max_latency_ms,
                    1 if rule.enabled else 0,
                ),
            )

    def get_routing_rules(self, enabled_only: bool = True) -> list[RoutingRule]:
        """Get routing rules"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM routing_rules"
            if enabled_only:
                query += " WHERE enabled = 1"
            query += " ORDER BY priority DESC"

            rows = conn.execute(query).fetchall()
            return [
                RoutingRule(
                    name=row["name"],
                    priority=row["priority"],
                    condition=row["condition"],
                    preferred_models=json.loads(row["preferred_models"]),
                    excluded_models=json.loads(row["excluded_models"]),
                    min_context_length=row["min_context_length"],
                    required_capabilities=json.loads(row["required_capabilities"]),
                    max_cost_per_1k=row["max_cost_per_1k"],
                    max_latency_ms=row["max_latency_ms"],
                    enabled=bool(row["enabled"]),
                )
                for row in rows
            ]

    def delete_routing_rule(self, name: str) -> bool:
        """Delete a routing rule by name. Returns True if a rule was deleted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM routing_rules WHERE name = ?", (name,))
            return cursor.rowcount > 0

    def toggle_routing_rule(self, name: str, enabled: bool) -> bool:
        """Enable or disable a routing rule by name. Returns True if a rule was updated."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE routing_rules SET enabled = ? WHERE name = ?",
                (1 if enabled else 0, name),
            )
            return cursor.rowcount > 0

    def set_model_alias(self, alias: str, provider: str, model_name: str, description: str = ""):
        """Set a model alias for easy switching"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO model_aliases (alias, provider, model_name, description)
                VALUES (?, ?, ?, ?)
            """,
                (alias, provider, model_name, description),
            )

    def get_model_alias(self, alias: str) -> tuple | None:
        """Get provider and model name for an alias"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT provider, model_name FROM model_aliases WHERE alias = ?", (alias,)).fetchone()
            return (row[0], row[1]) if row else None


class LLMRouter:
    """
    Intelligent LLM Router for Agent Jumbo

    Features:
    - Auto-discovery of available models
    - Priority-based model selection
    - Fallback chains for resilience
    - Usage tracking and cost estimation
    - Context-aware routing (USER, TASK, BACKGROUND)
    """

    # Known model capabilities and costs
    MODEL_CATALOG = {
        # Ollama models
        "ollama/qwen2.5-coder:3b": {
            "display_name": "Qwen 2.5 Coder 3B (Baseline)",
            "size_gb": 1.9,
            "context_length": 32768,
            "capabilities": ["chat", "code", "fast", "cheap", "baseline"],
            "cost_per_1k_input": 0,
            "cost_per_1k_output": 0,
            "avg_latency_ms": 500,
            "is_local": True,
            "priority_baseline": True,
            "supports_native_tools": False,
            "supports_hermes_tools": False,
            "supports_react_tools": True,
        },
        "ollama/qwen2.5-coder:7b": {
            "display_name": "Qwen 2.5 Coder 7B",
            "size_gb": 4.7,
            "context_length": 32768,
            "capabilities": ["chat", "code", "reasoning"],
            "cost_per_1k_input": 0,
            "cost_per_1k_output": 0,
            "avg_latency_ms": 1500,
            "is_local": True,
            "supports_native_tools": False,
            "supports_hermes_tools": True,
            "supports_react_tools": True,
            "tool_parser": "hermes",
        },
        "ollama/phi3:mini": {
            "display_name": "Phi-3 Mini",
            "size_gb": 2.2,
            "context_length": 4096,
            "capabilities": ["chat", "fast"],
            "cost_per_1k_input": 0,
            "cost_per_1k_output": 0,
            "avg_latency_ms": 400,
            "is_local": True,
        },
        # OpenAI models
        "openai/gpt-4o": {
            "display_name": "GPT-4o",
            "context_length": 128000,
            "capabilities": ["chat", "code", "vision", "reasoning", "function_calling", "long_context"],
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
            "avg_latency_ms": 2000,
        },
        "openai/gpt-4o-mini": {
            "display_name": "GPT-4o Mini",
            "context_length": 128000,
            "capabilities": ["chat", "code", "vision", "function_calling", "fast", "cheap"],
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.0006,
            "avg_latency_ms": 800,
        },
        "openai/gpt-3.5-turbo": {
            "display_name": "GPT-3.5 Turbo",
            "context_length": 16385,
            "capabilities": ["chat", "code", "function_calling", "fast", "cheap"],
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.0015,
            "avg_latency_ms": 500,
        },
        # OpenAI Reasoning/Codex models (o-series)
        "openai/o1": {
            "display_name": "OpenAI o1",
            "context_length": 200000,
            "capabilities": ["chat", "code", "reasoning", "function_calling", "long_context", "best_reasoning"],
            "cost_per_1k_input": 0.015,  # $15 per million
            "cost_per_1k_output": 0.060,  # $60 per million
            "avg_latency_ms": 5000,  # Reasoning takes longer
            "supports_reasoning": True,
        },
        "openai/o1-mini": {
            "display_name": "OpenAI o1-mini",
            "context_length": 128000,
            "capabilities": ["chat", "code", "reasoning", "function_calling", "fast"],
            "cost_per_1k_input": 0.003,  # $3 per million
            "cost_per_1k_output": 0.012,  # $12 per million
            "avg_latency_ms": 2000,
            "supports_reasoning": True,
        },
        "openai/o1-pro": {
            "display_name": "OpenAI o1-pro",
            "context_length": 200000,
            "capabilities": [
                "chat",
                "code",
                "reasoning",
                "function_calling",
                "long_context",
                "best_reasoning",
                "agent",
            ],
            "cost_per_1k_input": 0.150,  # $150 per million (premium)
            "cost_per_1k_output": 0.600,  # $600 per million
            "avg_latency_ms": 10000,  # Extended reasoning
            "supports_reasoning": True,
        },
        "openai/o3-mini": {
            "display_name": "OpenAI o3-mini",
            "context_length": 200000,
            "capabilities": ["chat", "code", "reasoning", "function_calling", "long_context", "fast"],
            "cost_per_1k_input": 0.0011,  # $1.10 per million
            "cost_per_1k_output": 0.0044,  # $4.40 per million
            "avg_latency_ms": 1500,
            "supports_reasoning": True,
            "effort_levels": ["low", "medium", "high"],
        },
        "openai/o4-mini": {
            "display_name": "OpenAI o4-mini (Codex)",
            "context_length": 200000,
            "capabilities": ["chat", "code", "reasoning", "function_calling", "long_context", "fast", "best_coding"],
            "cost_per_1k_input": 0.0011,  # $1.10 per million
            "cost_per_1k_output": 0.0044,  # $4.40 per million
            "avg_latency_ms": 1200,
            "supports_reasoning": True,
            "effort_levels": ["low", "medium", "high"],
            "quality_score": 9,  # Strong coding performance
        },
        # Google Gemini models
        "google/gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "context_length": 1048576,
            "capabilities": ["chat", "code", "vision", "reasoning", "function_calling", "fast", "long_context"],
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0004,
            "avg_latency_ms": 600,
        },
        "google/gemini-1.5-pro": {
            "display_name": "Gemini 1.5 Pro",
            "context_length": 2000000,
            "capabilities": ["chat", "code", "vision", "reasoning", "function_calling", "long_context"],
            "cost_per_1k_input": 0.00125,
            "cost_per_1k_output": 0.005,
            "avg_latency_ms": 1300,
        },
        # Anthropic models
        "anthropic/claude-opus-4-5-20251101": {
            "display_name": "Claude Opus 4.5",
            "context_length": 200000,
            "max_output_tokens": 64000,
            "capabilities": [
                "chat",
                "code",
                "vision",
                "reasoning",
                "function_calling",
                "long_context",
                "agent",
                "computer_use",
                "best_coding",
            ],
            "cost_per_1k_input": 0.005,  # $5 per million
            "cost_per_1k_output": 0.025,  # $25 per million
            "avg_latency_ms": 2500,
            "supports_caching": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 3600,  # 1 hour for extended thinking
            "supports_ptc": True,
            "supports_batch": True,
            "effort_levels": ["low", "medium", "high"],
            "quality_score": 10,  # SWE-bench 80.9%
        },
        "anthropic/claude-sonnet-4-5-20250929": {
            "display_name": "Claude Sonnet 4.5",
            "context_length": 200000,
            "max_output_tokens": 8192,
            "capabilities": ["chat", "code", "vision", "reasoning", "function_calling", "long_context", "agent"],
            "cost_per_1k_input": 0.003,  # $3 per million
            "cost_per_1k_output": 0.015,  # $15 per million
            "avg_latency_ms": 1800,
            "supports_caching": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 300,  # 5 minutes default
            "supports_ptc": True,
            "supports_batch": True,
            "quality_score": 9,
        },
        "anthropic/claude-3-5-sonnet-20241022": {
            "display_name": "Claude 3.5 Sonnet",
            "context_length": 200000,
            "capabilities": ["chat", "code", "vision", "reasoning", "function_calling", "long_context"],
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "avg_latency_ms": 1500,
            "supports_caching": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 300,
            "supports_ptc": True,
            "supports_batch": True,
        },
        "anthropic/claude-3-haiku-20240307": {
            "display_name": "Claude 3 Haiku",
            "context_length": 200000,
            "capabilities": ["chat", "code", "vision", "function_calling", "fast", "cheap", "long_context"],
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
            "avg_latency_ms": 600,
            "supports_caching": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 300,
            "supports_batch": True,
        },
    }

    def __init__(self, db_path: str | None = None):
        self.db = LLMRouterDatabase(db_path)
        self._ollama_base_url = get_default_ollama_base_url()
        self._last_discovery = None
        self._discovery_interval = 300  # 5 minutes

    async def discover_models(self, force: bool = False) -> list[ModelInfo]:
        """Discover all available models from configured providers"""
        now = time.time()
        if not force and self._last_discovery and (now - self._last_discovery) < self._discovery_interval:
            return self.db.get_models()

        # Reset availability so stale entries from previous successful probes
        # do not remain routable after providers go offline.
        self.db.mark_all_models_unavailable(["ollama", "openai", "anthropic", "google"])

        discovered = []

        # Discover Ollama models
        ollama_models = await self._discover_ollama_models()
        discovered.extend(ollama_models)

        # Add known cloud models (check API keys)
        cloud_models = self._get_available_cloud_models()
        discovered.extend(cloud_models)

        # Save to database
        for model in discovered:
            self.db.save_model(model)

        self._last_discovery = now
        return discovered

    async def _discover_ollama_models(self) -> list[ModelInfo]:
        """Discover models available in Ollama"""
        models = []
        try:
            # Use synchronous urllib in executor for async compatibility
            def fetch_ollama():
                url = f"{self._ollama_base_url}/api/tags"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310 - localhost Ollama URL only
                    return json.loads(response.read().decode())

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, fetch_ollama)

            for model_data in data.get("models", []):
                name = model_data.get("name", "")
                size_bytes = model_data.get("size", 0)
                size_gb = size_bytes / (1024**3)

                # Get catalog info if available
                catalog_key = f"ollama/{name}"
                catalog_info = self.MODEL_CATALOG.get(catalog_key, {})

                model = ModelInfo(
                    provider="ollama",
                    name=name,
                    display_name=catalog_info.get("display_name", name),
                    size_gb=round(size_gb, 2),
                    context_length=catalog_info.get("context_length", 4096),
                    capabilities=catalog_info.get("capabilities", ["chat"]),
                    cost_per_1k_input=0,
                    cost_per_1k_output=0,
                    avg_latency_ms=catalog_info.get("avg_latency_ms", 1000),
                    is_local=True,
                    is_available=True,
                    last_checked=isoformat_z(utc_now()),
                    metadata={"modified_at": model_data.get("modified_at")},
                )
                models.append(model)
        except urllib.error.URLError as e:
            print(f"[LLMRouter] Ollama not reachable: {e}")
        except Exception as e:
            print(f"[LLMRouter] Error discovering Ollama models: {e}")

        return models

    def _get_available_cloud_models(self) -> list[ModelInfo]:
        """Get cloud models based on available API keys"""
        if self._is_local_only_mode():
            return []

        models = []

        # Check OpenAI
        openai_key = os.getenv("API_KEY_OPENAI") or os.getenv("OPENAI_API_KEY")
        if openai_key:
            for key, info in self.MODEL_CATALOG.items():
                if key.startswith("openai/"):
                    model_name = key.split("/")[1]
                    models.append(
                        ModelInfo(
                            provider="openai",
                            name=model_name,
                            display_name=info["display_name"],
                            context_length=info["context_length"],
                            capabilities=info["capabilities"],
                            cost_per_1k_input=info["cost_per_1k_input"],
                            cost_per_1k_output=info["cost_per_1k_output"],
                            avg_latency_ms=info["avg_latency_ms"],
                            is_local=False,
                            is_available=True,
                            last_checked=isoformat_z(utc_now()),
                        )
                    )

        # Check Anthropic
        anthropic_key = os.getenv("API_KEY_ANTHROPIC") or os.getenv("ANTHROPIC_API_KEY")
        anthropic_caching_enabled = os.getenv("ANTHROPIC_ENABLE_CACHING", "true").lower() == "true"
        ttl_raw = (os.getenv("ANTHROPIC_CACHE_TTL_SECONDS", "300") or "300").strip()
        # Allow env values with inline comments, e.g. "3600  # one hour"
        ttl_token = ttl_raw.split()[0]
        try:
            anthropic_cache_ttl = int(ttl_token)
        except ValueError:
            anthropic_cache_ttl = 300

        if anthropic_key:
            for key, info in self.MODEL_CATALOG.items():
                if key.startswith("anthropic/"):
                    model_name = key.split("/")[1]
                    models.append(
                        ModelInfo(
                            provider="anthropic",
                            name=model_name,
                            display_name=info["display_name"],
                            context_length=info["context_length"],
                            capabilities=info["capabilities"],
                            cost_per_1k_input=info["cost_per_1k_input"],
                            cost_per_1k_output=info["cost_per_1k_output"],
                            avg_latency_ms=info["avg_latency_ms"],
                            is_local=False,
                            is_available=True,
                            last_checked=isoformat_z(utc_now()),
                            # Caching configuration
                            supports_caching=info.get("supports_caching", False),
                            cache_enabled=info.get("supports_caching", False) and anthropic_caching_enabled,
                            cache_ttl_seconds=info.get("cache_ttl_seconds", anthropic_cache_ttl),
                            # Advanced features
                            supports_ptc=info.get("supports_ptc", False),
                            supports_batch=info.get("supports_batch", False),
                            effort_levels=info.get("effort_levels", []),
                        )
                    )

        # Check Google Gemini
        google_key = os.getenv("API_KEY_GOOGLE") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if google_key:
            for key, info in self.MODEL_CATALOG.items():
                if key.startswith("google/"):
                    model_name = key.split("/")[1]
                    models.append(
                        ModelInfo(
                            provider="google",
                            name=model_name,
                            display_name=info["display_name"],
                            context_length=info["context_length"],
                            capabilities=info["capabilities"],
                            cost_per_1k_input=info["cost_per_1k_input"],
                            cost_per_1k_output=info["cost_per_1k_output"],
                            avg_latency_ms=info["avg_latency_ms"],
                            is_local=False,
                            is_available=True,
                            last_checked=isoformat_z(utc_now()),
                        )
                    )

        return models

    @staticmethod
    def _parse_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _is_local_only_mode(self) -> bool:
        # Environment variable has highest priority
        env_value = os.getenv("LOCAL_LLM_ONLY")
        if env_value is not None:
            return self._parse_bool(env_value, True)

        try:
            from python.helpers import settings as settings_helper

            current = settings_helper.get_settings()
            return self._parse_bool(current.get("llm_local_only_mode", True), True)
        except Exception:
            return True

    def _cloud_fallback_enabled(self) -> bool:
        env_value = os.getenv("ALLOW_CLOUD_LLM_FALLBACK")
        if env_value is not None:
            return self._parse_bool(env_value, False)

        try:
            from python.helpers import settings as settings_helper

            current = settings_helper.get_settings()
            return self._parse_bool(current.get("llm_cloud_fallback_enabled", False), False)
        except Exception:
            return False

    def select_model(
        self,
        role: str = "chat",
        context_type: str = "user",
        required_capabilities: list[str] | None = None,
        priority: RoutingPriority = RoutingPriority.BALANCED,
        min_context_length: int = 0,
        max_cost_per_1k: float = 0,
        preferred_provider: str | None = None,
        excluded_providers: list[str] | None = None,
    ) -> ModelInfo | None:
        """
        Select the best model based on criteria and active routing rules.

        Routing rules are loaded from the database and applied in priority order.
        Each rule can filter, constrain, or boost candidates.

        Args:
            role: Model role (chat, utility, browser, embedding)
            context_type: Agent context (user, task, background)
            required_capabilities: List of required capabilities
            priority: Routing priority strategy
            min_context_length: Minimum context window required
            max_cost_per_1k: Maximum cost per 1K tokens (0 = no limit)
            preferred_provider: Preferred provider (optional)
            excluded_providers: Providers to exclude

        Returns:
            Best matching ModelInfo or None
        """
        models = self.db.get_models(available_only=True)
        if not models:
            return None

        # Respect explicit per-role defaults if configured and still eligible.
        default = self.get_default_model(role)
        if default:
            def_provider, def_name = default
            default_model = next((m for m in models if m.provider == def_provider and m.name == def_name), None)
            if default_model:
                required_capabilities = required_capabilities or []
                excluded_providers = excluded_providers or []
                if default_model.provider not in excluded_providers:
                    if min_context_length <= 0 or default_model.context_length >= min_context_length:
                        if (
                            max_cost_per_1k <= 0
                            or max(default_model.cost_per_1k_input, default_model.cost_per_1k_output) <= max_cost_per_1k
                        ):
                            if not required_capabilities or all(
                                cap in default_model.capabilities for cap in required_capabilities
                            ):
                                return default_model

        candidates = []
        required_capabilities = required_capabilities or []
        excluded_providers = excluded_providers or []

        # Apply routing rules — merge constraints from all matching enabled rules.
        rule_context = {"role": role, "context_type": context_type}
        merged = self._merge_routing_rules(rule_context)

        # Augment filters with rule-derived constraints
        if merged["excluded_models"]:
            excluded_providers = list(excluded_providers)  # copy
        if merged["required_capabilities"]:
            required_capabilities = list(set(required_capabilities) | set(merged["required_capabilities"]))
        if merged["min_context_length"] > min_context_length:
            min_context_length = merged["min_context_length"]
        if merged["max_cost_per_1k"] > 0 and (max_cost_per_1k <= 0 or merged["max_cost_per_1k"] < max_cost_per_1k):
            max_cost_per_1k = merged["max_cost_per_1k"]

        for model in models:
            model_key = f"{model.provider}/{model.name}"

            # Filter by provider
            if model.provider in excluded_providers:
                continue

            # Filter by rule-excluded models (provider/name)
            if model_key in merged["excluded_models"] or model.name in merged["excluded_models"]:
                continue

            # Filter by context length
            if min_context_length > 0 and model.context_length < min_context_length:
                continue

            # Filter by cost
            if max_cost_per_1k > 0:
                model_cost = max(model.cost_per_1k_input, model.cost_per_1k_output)
                if model_cost > max_cost_per_1k:
                    continue

            # Filter by capabilities
            if required_capabilities:
                if not all(cap in model.capabilities for cap in required_capabilities):
                    continue

            # Filter by max latency from rules
            if merged["max_latency_ms"] > 0 and model.avg_latency_ms > 0:
                if model.avg_latency_ms > merged["max_latency_ms"]:
                    continue

            # Calculate priority score
            score = self._calculate_score(model, priority, context_type, preferred_provider)

            # Boost preferred models from rules
            if model_key in merged["preferred_models"] or model.name in merged["preferred_models"]:
                score += 50  # Significant boost for rule-preferred models

            model.priority_score = score
            candidates.append(model)

        if not candidates:
            # Try baseline model as last resort
            baseline = self.get_baseline_model()
            if baseline:
                # Check if baseline meets required capabilities
                if not required_capabilities or all(cap in baseline.capabilities for cap in required_capabilities):
                    print("[LLMRouter] No candidates matched, falling back to baseline model")
                    return baseline
            return None

        # Sort by score (descending)
        candidates.sort(key=lambda m: m.priority_score, reverse=True)
        return candidates[0]

    @staticmethod
    def evaluate_rule_condition(condition: str, context: dict[str, str]) -> bool:
        """
        Evaluate a routing rule condition against a context dict.

        Uses a safe key=value matching grammar (NO eval/exec). Supports:
          - Simple: ``role=chat``
          - AND:    ``role=chat AND context_type=user``
          - OR:     ``role=chat OR role=utility``
          - NOT:    ``role!=background``
          - Mixed:  ``role=chat AND context_type!=background``

        Keys are matched case-insensitively against *context* keys.
        Values are matched case-insensitively.
        An empty or whitespace-only condition always matches (returns True).
        """
        condition = (condition or "").strip()
        if not condition:
            return True

        # Normalise context keys to lower-case for matching
        ctx = {k.lower(): str(v).lower() for k, v in context.items()}

        def _eval_atom(atom: str) -> bool:
            atom = atom.strip()
            if "!=" in atom:
                key, _, val = atom.partition("!=")
                return ctx.get(key.strip().lower(), "") != val.strip().lower()
            elif "=" in atom:
                key, _, val = atom.partition("=")
                return ctx.get(key.strip().lower(), "") == val.strip().lower()
            # Bare key = truthy check
            return bool(ctx.get(atom.lower(), ""))

        # Split on OR first (lower precedence), then AND within each OR-branch
        or_branches = [b.strip() for b in condition.split(" OR ")]
        for branch in or_branches:
            and_atoms = [a.strip() for a in branch.split(" AND ")]
            if all(_eval_atom(a) for a in and_atoms):
                return True
        return False

    def _merge_routing_rules(self, context: dict[str, str]) -> dict:
        """
        Load enabled routing rules, evaluate conditions, and merge matching
        rules (ordered by priority descending) into a single constraints dict.
        """
        merged: dict[str, Any] = {
            "preferred_models": set(),
            "excluded_models": set(),
            "required_capabilities": set(),
            "min_context_length": 0,
            "max_cost_per_1k": 0.0,
            "max_latency_ms": 0,
        }

        try:
            rules = self.db.get_routing_rules(enabled_only=True)
        except Exception:
            return merged

        for rule in rules:
            if not self.evaluate_rule_condition(rule.condition, context):
                continue

            # Merge preferred / excluded
            merged["preferred_models"].update(rule.preferred_models)
            merged["excluded_models"].update(rule.excluded_models)
            merged["required_capabilities"].update(rule.required_capabilities)

            # Tightest constraint wins
            if rule.min_context_length > merged["min_context_length"]:
                merged["min_context_length"] = rule.min_context_length
            if rule.max_cost_per_1k > 0:
                if merged["max_cost_per_1k"] <= 0 or rule.max_cost_per_1k < merged["max_cost_per_1k"]:
                    merged["max_cost_per_1k"] = rule.max_cost_per_1k
            if rule.max_latency_ms > 0:
                if merged["max_latency_ms"] <= 0 or rule.max_latency_ms < merged["max_latency_ms"]:
                    merged["max_latency_ms"] = rule.max_latency_ms

        return merged

    def _calculate_score(
        self, model: ModelInfo, priority: RoutingPriority, context_type: str, preferred_provider: str | None = None
    ) -> float:
        """Calculate routing score for a model"""
        score = 0.0

        # Base score from capabilities
        score += len(model.capabilities) * 10

        # Priority-specific scoring
        if priority == RoutingPriority.COST:
            # Lower cost = higher score
            if model.is_local:
                score += 100  # Local models are free
            else:
                max_cost = max(model.cost_per_1k_input, model.cost_per_1k_output)
                score += max(0, 50 - (max_cost * 1000))  # Penalize expensive models

            if "cheap" in model.capabilities:
                score += 30

        elif priority == RoutingPriority.SPEED:
            # Lower latency = higher score
            if model.avg_latency_ms > 0:
                score += max(0, 100 - (model.avg_latency_ms / 50))

            if "fast" in model.capabilities:
                score += 50

            if model.is_local:
                score += 20  # Local models often faster (no network)

        elif priority == RoutingPriority.QUALITY:
            # More capabilities = higher score
            if "reasoning" in model.capabilities:
                score += 50
            if "code" in model.capabilities:
                score += 30
            if "vision" in model.capabilities:
                score += 20
            if "long_context" in model.capabilities:
                score += 20

            # Larger context = better quality potential
            score += min(50, model.context_length / 4000)

        else:  # BALANCED
            # Mix of all factors
            if model.is_local:
                score += 30

            if model.avg_latency_ms > 0:
                score += max(0, 30 - (model.avg_latency_ms / 100))

            score += min(30, len(model.capabilities) * 5)
            score += min(20, model.context_length / 10000)

        # Context-type adjustments
        if context_type == "background":
            # Background tasks prefer fast, cheap models
            if "fast" in model.capabilities:
                score += 20
            if model.is_local:
                score += 20

        elif context_type == "user":
            # User interactions prefer quality
            if "reasoning" in model.capabilities:
                score += 15

        # Preferred provider bonus
        if preferred_provider and model.provider == preferred_provider:
            score += 30

        return score

    def get_fallback_chain(
        self, primary_model: ModelInfo, required_capabilities: list[str] | None = None, max_fallbacks: int = 3
    ) -> list[ModelInfo]:
        """
        Build a fallback chain for a primary model

        Returns a list of models to try if the primary fails.
        Always includes baseline model as final fallback.
        """
        models = self.db.get_models(available_only=True)
        required_capabilities = required_capabilities or []

        candidates = []
        baseline_model = self.get_baseline_model()

        for model in models:
            # Skip primary model
            if model.provider == primary_model.provider and model.name == primary_model.name:
                continue

            # Skip baseline (will be added at end)
            if baseline_model and model.provider == baseline_model.provider and model.name == baseline_model.name:
                continue

            # Check required capabilities
            if required_capabilities and not all(cap in model.capabilities for cap in required_capabilities):
                continue

            candidates.append(model)

        # Sort by fallback score (local > cheap > fast)
        def fallback_score(m: ModelInfo) -> float:
            score = 0
            if m.is_local:
                score += 100
            if "cheap" in m.capabilities:
                score += 50
            if "fast" in m.capabilities:
                score += 30
            return score

        candidates.sort(key=fallback_score, reverse=True)

        # Take top N-1 candidates (reserve last spot for baseline)
        fallback_chain = candidates[: max_fallbacks - 1]

        # Always append baseline as final fallback (if available and meets requirements)
        if baseline_model:
            # Check if baseline meets required capabilities
            if not required_capabilities or all(cap in baseline_model.capabilities for cap in required_capabilities):
                fallback_chain.append(baseline_model)

        return fallback_chain

    def record_call(
        self,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error_message: str | None = None,
        context_type: str | None = None,
        model_role: str | None = None,
    ):
        """Record a model call for usage tracking"""
        # Calculate cost
        catalog_key = f"{provider}/{model_name}"
        info = self.MODEL_CATALOG.get(catalog_key, {})
        cost = (input_tokens / 1000) * info.get("cost_per_1k_input", 0) + (output_tokens / 1000) * info.get(
            "cost_per_1k_output", 0
        )

        self.db.record_usage(
            provider=provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            context_type=context_type,
            model_role=model_role,
            cost_usd=cost,
        )

    def get_baseline_model(self) -> ModelInfo | None:
        """
        Get the baseline model (always available fallback)

        Returns the configured baseline model (typically Qwen 2.5 3B)
        or the smallest available local model as last resort.
        """
        models = self.db.get_models(available_only=True)

        # First: explicitly marked baseline
        baseline = [m for m in models if m.metadata.get("priority_baseline", False)]
        if baseline:
            return baseline[0]

        # Second: smallest local model with "baseline" capability
        local_baseline = [m for m in models if m.is_local and "baseline" in m.capabilities]
        if local_baseline:
            local_baseline.sort(key=lambda m: m.size_gb or 0)
            return local_baseline[0]

        # Last resort: smallest available local model
        local_models = [m for m in models if m.is_local]
        if local_models:
            local_models.sort(key=lambda m: m.size_gb or 0)
            return local_models[0]

        return None

    def get_usage_stats(self, hours: int = 24) -> dict:
        """Get usage statistics"""
        return self.db.get_usage_stats(hours)

    def set_default_model(self, role: str, provider: str, model_name: str):
        """Set a default model for a role using aliases"""
        alias = f"default_{role}"
        self.db.set_model_alias(alias, provider, model_name, f"Default {role} model")

    def get_default_model(self, role: str) -> tuple | None:
        """Get the default model for a role"""
        alias = f"default_{role}"
        return self.db.get_model_alias(alias)

    def add_routing_rule(self, rule: RoutingRule):
        """Add a routing rule"""
        self.db.save_routing_rule(rule)

    def get_routing_rules(self) -> list[RoutingRule]:
        """Get all routing rules"""
        return self.db.get_routing_rules()

    async def health_check_models(self, providers: list[str] | None = None) -> dict:
        """
        Perform health check on model providers

        Returns dict with provider status and recommendations
        """
        results = {"healthy": [], "degraded": [], "unavailable": [], "baseline_available": False, "recommendations": []}

        # Check Ollama
        if not providers or "ollama" in providers:
            try:

                def check_ollama():
                    url = f"{self._ollama_base_url}/api/tags"
                    req = urllib.request.Request(url, headers={"Accept": "application/json"})
                    with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310 - URL is from controlled config
                        return json.loads(response.read().decode())

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, check_ollama)
                results["healthy"].append("ollama")

                # Check for baseline model
                model_names = [m.get("name", "") for m in data.get("models", [])]
                if "qwen2.5-coder:3b" in model_names:
                    results["baseline_available"] = True
            except Exception as e:
                results["unavailable"].append(f"ollama: {e!s}")
                results["recommendations"].append("Start Ollama: docker start ollama")

        # Check cloud providers
        if os.getenv("OPENAI_API_KEY"):
            results["healthy"].append("openai")
        if os.getenv("ANTHROPIC_API_KEY"):
            results["healthy"].append("anthropic")

        # Generate recommendations
        if not results["baseline_available"]:
            results["recommendations"].append("Pull baseline model: docker exec ollama ollama pull qwen2.5-coder:3b")

        if not results["healthy"]:
            results["recommendations"].append("No models available! Start Ollama or configure API providers.")

        return results


import threading as _threading

# Singleton instance
_router_instance: LLMRouter | None = None
_router_lock = _threading.Lock()


def get_router() -> LLMRouter:
    """Get the global LLM router instance (thread-safe)."""
    global _router_instance
    if _router_instance is None:
        with _router_lock:
            # Double-checked locking
            if _router_instance is None:
                _router_instance = LLMRouter()
    return _router_instance


async def auto_configure_models():
    """
    Auto-configure models based on available resources

    This function:
    1. Discovers available models
    2. Sets sensible defaults based on what's available
    3. Configures fallback chains
    """
    router = get_router()

    # Discover available models
    models = await router.discover_models(force=True)

    # Prefer explicit provider selections from settings when those models are available.
    settings_seeded_roles: set[str] = set()
    try:
        from python.helpers import settings as settings_helper

        current = settings_helper.get_settings()
        configured_defaults = [
            ("chat", current.get("chat_model_provider"), current.get("chat_model_name")),
            ("utility", current.get("util_model_provider"), current.get("util_model_name")),
            ("browser", current.get("browser_model_provider"), current.get("browser_model_name")),
        ]
        for role, provider, name in configured_defaults:
            if not provider or not name:
                continue
            match = next((m for m in models if m.provider == provider and m.name == name), None)
            if match:
                router.set_default_model(role, provider, name)
                settings_seeded_roles.add(role)
                print(f"[LLMRouter] Auto-configured {role} model from settings: {provider}/{name}")
    except Exception as e:
        print(f"[LLMRouter] Could not apply settings-based defaults: {e}")

    # Find best local model for chat
    local_models = [m for m in models if m.is_local and "chat" in m.capabilities]
    if local_models:
        # Prefer smaller models that fit in GPU
        local_models.sort(key=lambda m: m.size_gb)

        # Find the largest model under 4GB (typical GPU VRAM)
        gpu_limit_gb = float(os.getenv("GPU_VRAM_GB", "4"))
        suitable = [m for m in local_models if m.size_gb < gpu_limit_gb]

        if suitable:
            best_local = suitable[-1]  # Largest that fits
            if "chat" not in settings_seeded_roles:
                router.set_default_model("chat", best_local.provider, best_local.name)
                print(f"[LLMRouter] Auto-configured chat model: {best_local.provider}/{best_local.name}")
            if "utility" not in settings_seeded_roles:
                router.set_default_model("utility", best_local.provider, best_local.name)
                print(f"[LLMRouter] Auto-configured utility model: {best_local.provider}/{best_local.name}")

    # Set cloud fallbacks if available
    cloud_models = [m for m in models if not m.is_local]
    if cloud_models and not router._is_local_only_mode() and router._cloud_fallback_enabled():
        # Prefer cheap models for fallback
        cloud_models.sort(key=lambda m: m.cost_per_1k_output)
        router.set_default_model("fallback", cloud_models[0].provider, cloud_models[0].name)
        print(f"[LLMRouter] Auto-configured fallback model: {cloud_models[0].provider}/{cloud_models[0].name}")

    return models


async def ensure_baseline_model():
    """
    Ensure baseline model is available
    Auto-pulls Qwen 2.5 3B if enabled and Ollama is running

    Security: Uses subprocess.run() with list args (not shell=True)
    to prevent command injection vulnerabilities.
    """
    router = get_router()

    # Check if baseline is already available
    baseline = router.get_baseline_model()
    if baseline and baseline.is_available:
        print(f"[LLMRouter] Baseline model available: {baseline.display_name}")
        return True

    # Check if auto-pull enabled
    auto_pull = os.getenv("BASELINE_AUTO_PULL", "true").lower() == "true"
    if not auto_pull:
        print("[LLMRouter] Baseline model not available, auto-pull disabled")
        return False

    # Pull baseline model using subprocess.run (safe, no shell injection)
    baseline_name = os.getenv("BASELINE_MODEL_NAME", "qwen2.5-coder:3b")
    print(f"[LLMRouter] Pulling baseline model: {baseline_name}...")

    try:
        import subprocess

        # Using subprocess.run with list args - safe from injection
        # No shell=True, parameters passed as list elements
        result = subprocess.run(
            ["docker", "exec", "ollama", "ollama", "pull", baseline_name], capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            print(f"[LLMRouter] Successfully pulled baseline model: {baseline_name}")
            await router.discover_models(force=True)
            return True
        else:
            print(f"[LLMRouter] Failed to pull baseline model: {result.stderr}")
            return False
    except Exception as e:
        print(f"[LLMRouter] Error pulling baseline model: {e}")
        return False


# ============================================================================
# Failover-Aware Model Execution
# ============================================================================


class FailoverResult:
    """Result of a failover-aware model call"""

    def __init__(
        self,
        success: bool,
        response: str = "",
        reasoning: str = "",
        model_used: ModelInfo | None = None,
        attempts: list[dict] | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.response = response
        self.reasoning = reasoning
        self.model_used = model_used
        self.attempts = attempts or []
        self.error = error


async def call_with_failover(
    primary_model: ModelInfo,
    call_func,
    required_capabilities: list[str] | None = None,
    max_retries: int = 3,
    record_usage: bool = True,
) -> FailoverResult:
    """
    Execute an LLM call with automatic failover on failure.

    Args:
        primary_model: The primary ModelInfo to use
        call_func: Async function that takes (provider: str, model_name: str) and
                   returns (response, reasoning) tuple. Should raise on failure.
        required_capabilities: Capabilities required for fallback models
        max_retries: Maximum number of models to try (including primary)
        record_usage: Whether to record usage in router database

    Returns:
        FailoverResult with success status and response/error details
    """
    import logging
    import time

    router = get_router()
    attempts = []

    # Build model chain: primary + fallbacks
    models_to_try = [primary_model]
    fallbacks = router.get_fallback_chain(
        primary_model, required_capabilities=required_capabilities, max_fallbacks=max_retries - 1
    )
    models_to_try.extend(fallbacks)

    # Limit to max_retries
    models_to_try = models_to_try[:max_retries]

    for model in models_to_try:
        start_time = time.time()
        attempt = {
            "provider": model.provider,
            "model_name": model.name,
            "success": False,
            "error": None,
            "latency_ms": 0,
        }

        try:
            logging.info(f"[LLMRouter] Attempting call with {model.provider}/{model.name}")
            response, reasoning = await call_func(model.provider, model.name)

            latency_ms = int((time.time() - start_time) * 1000)
            attempt["success"] = True
            attempt["latency_ms"] = latency_ms
            attempts.append(attempt)

            # Record successful usage with estimated token counts
            if record_usage:
                from python.helpers.tokens import approximate_tokens

                output_tokens = approximate_tokens(response) + approximate_tokens(reasoning)
                router.record_call(
                    provider=model.provider,
                    model_name=model.name,
                    input_tokens=0,  # Input tokens not available from unified_call
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    success=True,
                    model_role="chat",
                )

            logging.info(f"[LLMRouter] Success with {model.provider}/{model.name} ({latency_ms}ms)")
            return FailoverResult(
                success=True, response=response, reasoning=reasoning, model_used=model, attempts=attempts
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            attempt["error"] = error_msg
            attempt["latency_ms"] = latency_ms
            attempts.append(attempt)

            logging.warning(f"[LLMRouter] Failed with {model.provider}/{model.name}: {error_msg}")

            # Record failed usage
            if record_usage:
                router.record_call(
                    provider=model.provider,
                    model_name=model.name,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=error_msg,
                    model_role="chat",
                )

            # Check if this is a blocking error (auth/billing) vs transient
            if _is_permanent_failure(e):
                logging.warning(
                    f"[LLMRouter] Permanent failure detected, marking {model.provider}/{model.name} unavailable"
                )
                router.db.mark_provider_models_unavailable(model.provider)

            continue

    # All models failed
    last_error = attempts[-1]["error"] if attempts else "No models available"
    return FailoverResult(
        success=False, attempts=attempts, error=f"All {len(attempts)} models failed. Last error: {last_error}"
    )


def _is_permanent_failure(exc: Exception) -> bool:
    """
    Determine if an exception indicates a permanent failure (auth, billing, blocked)
    vs a transient failure (rate limit, overload, timeout).

    Permanent failures should mark the provider as unavailable.
    """
    error_str = str(exc).lower()

    # Auth/billing/blocked indicators
    permanent_indicators = [
        "authentication",
        "unauthorized",
        "invalid api key",
        "invalid_api_key",
        "api key is invalid",
        "billing",
        "quota exceeded",
        "account",
        "forbidden",
        "access denied",
        "blocked",
        "suspended",
        "disabled",
    ]

    for indicator in permanent_indicators:
        if indicator in error_str:
            return True

    # Check status codes if available
    status_code = getattr(exc, "status_code", None)
    if status_code in (401, 403):
        return True

    return False


def mark_provider_unavailable(provider: str):
    """Mark all models from a provider as unavailable."""
    router = get_router()
    router.db.mark_provider_models_unavailable(provider)
    print(f"[LLMRouter] Marked provider '{provider}' as unavailable")


def get_available_providers() -> list[str]:
    """Get list of currently available providers."""
    router = get_router()
    models = router.db.get_models(available_only=True)
    return list({m.provider for m in models})
