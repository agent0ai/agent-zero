"""
Cache Metrics Tracking for Anthropic Prompt Caching

Tracks cache hits, misses, cost savings, and latency improvements
from Anthropic's prompt caching feature.
"""

import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional

from python.helpers.datetime_utils import isoformat_z, utc_now


@dataclass
class CacheMetrics:
    """Metrics for a single API call with caching"""

    timestamp: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0  # Tokens written to cache
    cache_read_input_tokens: int = 0  # Tokens read from cache
    cache_hit: bool = False  # Did we get a cache hit?
    cost_without_cache: float = 0.0  # What it would have cost without caching
    cost_with_cache: float = 0.0  # Actual cost with caching
    cost_savings: float = 0.0  # Savings from caching
    latency_ms: int = 0  # Response latency


class CacheMetricsTracker:
    """SQLite-based cache metrics tracker"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "cache_metrics.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_creation_input_tokens INTEGER DEFAULT 0,
                    cache_read_input_tokens INTEGER DEFAULT 0,
                    cache_hit INTEGER DEFAULT 0,
                    cost_without_cache REAL DEFAULT 0.0,
                    cost_with_cache REAL DEFAULT 0.0,
                    cost_savings REAL DEFAULT 0.0,
                    latency_ms INTEGER DEFAULT 0
                )
            """)
            # Index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_metrics_timestamp
                ON cache_metrics(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_metrics_model
                ON cache_metrics(model)
            """)
            conn.commit()

    def track_usage(
        self,
        model: str,
        provider: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        cost_per_1k_cache_write: float = 0.0,  # Usually 1.25x input cost
        cost_per_1k_cache_read: float = 0.0,  # Usually 0.1x input cost
        latency_ms: int = 0,
    ) -> CacheMetrics:
        """
        Track a single API call with cache metrics.

        Args:
            model: Model name (e.g., "claude-opus-4-5-20251101")
            provider: Provider name (e.g., "anthropic")
            input_tokens: Regular input tokens
            output_tokens: Output tokens
            cache_creation_input_tokens: Tokens written to cache
            cache_read_input_tokens: Tokens read from cache
            cost_per_1k_input: Cost per 1K input tokens
            cost_per_1k_output: Cost per 1K output tokens
            cost_per_1k_cache_write: Cost per 1K cache write (default 1.25x input)
            cost_per_1k_cache_read: Cost per 1K cache read (default 0.1x input)
            latency_ms: Response latency in milliseconds

        Returns:
            CacheMetrics object with computed savings
        """
        # Default cache pricing (Anthropic's model)
        if cost_per_1k_cache_write == 0.0:
            cost_per_1k_cache_write = cost_per_1k_input * 1.25
        if cost_per_1k_cache_read == 0.0:
            cost_per_1k_cache_read = cost_per_1k_input * 0.1

        cache_hit = cache_read_input_tokens > 0

        # Calculate costs
        total_input_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens

        # Cost with caching
        cost_with_cache = (
            (input_tokens / 1000.0) * cost_per_1k_input
            + (cache_creation_input_tokens / 1000.0) * cost_per_1k_cache_write
            + (cache_read_input_tokens / 1000.0) * cost_per_1k_cache_read
            + (output_tokens / 1000.0) * cost_per_1k_output
        )

        # Cost without caching (all tokens at full price)
        cost_without_cache = (total_input_tokens / 1000.0) * cost_per_1k_input + (
            output_tokens / 1000.0
        ) * cost_per_1k_output

        cost_savings = max(0.0, cost_without_cache - cost_with_cache)

        metrics = CacheMetrics(
            timestamp=isoformat_z(utc_now()),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_hit=cache_hit,
            cost_without_cache=cost_without_cache,
            cost_with_cache=cost_with_cache,
            cost_savings=cost_savings,
            latency_ms=latency_ms,
        )

        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache_metrics (
                    timestamp, model, provider, input_tokens, output_tokens,
                    cache_creation_input_tokens, cache_read_input_tokens,
                    cache_hit, cost_without_cache, cost_with_cache,
                    cost_savings, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.timestamp,
                    metrics.model,
                    metrics.provider,
                    metrics.input_tokens,
                    metrics.output_tokens,
                    metrics.cache_creation_input_tokens,
                    metrics.cache_read_input_tokens,
                    1 if metrics.cache_hit else 0,
                    metrics.cost_without_cache,
                    metrics.cost_with_cache,
                    metrics.cost_savings,
                    metrics.latency_ms,
                ),
            )
            conn.commit()

        return metrics

    def get_cache_stats(
        self,
        model: Optional[str] = None,
        hours: int = 24,
    ) -> dict:
        """
        Get aggregated cache statistics.

        Args:
            model: Optional model filter
            hours: Look back this many hours (default 24)

        Returns:
            Dictionary with cache hit rate, cost savings, etc.
        """
        cutoff = isoformat_z(utc_now() - timedelta(hours=hours))

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT
                    COUNT(*) as total_calls,
                    SUM(cache_hit) as cache_hits,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(cache_creation_input_tokens) as total_cache_writes,
                    SUM(cache_read_input_tokens) as total_cache_reads,
                    SUM(cost_without_cache) as total_cost_without_cache,
                    SUM(cost_with_cache) as total_cost_with_cache,
                    SUM(cost_savings) as total_savings,
                    AVG(CASE WHEN cache_hit = 1 THEN latency_ms ELSE NULL END) as avg_latency_cached,
                    AVG(CASE WHEN cache_hit = 0 THEN latency_ms ELSE NULL END) as avg_latency_uncached
                FROM cache_metrics
                WHERE timestamp >= ?
            """
            params = [cutoff]

            if model:
                query += " AND model = ?"
                params.append(model)

            row = conn.execute(query, params).fetchone()

            if not row or row["total_calls"] == 0:
                return {
                    "total_calls": 0,
                    "cache_hits": 0,
                    "cache_hit_rate": 0.0,
                    "total_cost_without_cache": 0.0,
                    "total_cost_with_cache": 0.0,
                    "total_savings": 0.0,
                    "savings_percentage": 0.0,
                    "avg_latency_improvement_ms": 0,
                }

            cache_hit_rate = (row["cache_hits"] / row["total_calls"]) * 100 if row["total_calls"] > 0 else 0.0
            savings_pct = (
                (row["total_savings"] / row["total_cost_without_cache"]) * 100
                if row["total_cost_without_cache"] > 0
                else 0.0
            )

            avg_latency_improvement = 0
            if row["avg_latency_cached"] and row["avg_latency_uncached"]:
                avg_latency_improvement = int(row["avg_latency_uncached"] - row["avg_latency_cached"])

            return {
                "total_calls": row["total_calls"],
                "cache_hits": row["cache_hits"],
                "cache_hit_rate": round(cache_hit_rate, 2),
                "total_input_tokens": row["total_input_tokens"],
                "total_output_tokens": row["total_output_tokens"],
                "total_cache_writes": row["total_cache_writes"],
                "total_cache_reads": row["total_cache_reads"],
                "total_cost_without_cache": round(row["total_cost_without_cache"], 4),
                "total_cost_with_cache": round(row["total_cost_with_cache"], 4),
                "total_savings": round(row["total_savings"], 4),
                "savings_percentage": round(savings_pct, 2),
                "avg_latency_cached_ms": int(row["avg_latency_cached"] or 0),
                "avg_latency_uncached_ms": int(row["avg_latency_uncached"] or 0),
                "avg_latency_improvement_ms": avg_latency_improvement,
            }

    def print_cache_report(self, hours: int = 24):
        """Print a formatted cache performance report"""
        stats = self.get_cache_stats(hours=hours)

        print("\n" + "=" * 60)
        print(f"ANTHROPIC PROMPT CACHE REPORT (Last {hours} hours)")
        print("=" * 60)
        print(f"Total API Calls:        {stats['total_calls']}")
        print(f"Cache Hits:             {stats['cache_hits']} ({stats['cache_hit_rate']}%)")
        print("\nToken Usage:")
        print(f"  Input Tokens:         {stats['total_input_tokens']:,}")
        print(f"  Output Tokens:        {stats['total_output_tokens']:,}")
        print(f"  Cache Writes:         {stats['total_cache_writes']:,}")
        print(f"  Cache Reads:          {stats['total_cache_reads']:,}")
        print("\nCost Analysis:")
        print(f"  Without Caching:      ${stats['total_cost_without_cache']:.4f}")
        print(f"  With Caching:         ${stats['total_cost_with_cache']:.4f}")
        print(f"  Total Savings:        ${stats['total_savings']:.4f} ({stats['savings_percentage']}%)")
        print("\nLatency:")
        print(f"  Cached (avg):         {stats['avg_latency_cached_ms']}ms")
        print(f"  Uncached (avg):       {stats['avg_latency_uncached_ms']}ms")
        print(f"  Improvement:          {stats['avg_latency_improvement_ms']}ms")
        print("=" * 60 + "\n")


# Global instance
_cache_tracker: Optional[CacheMetricsTracker] = None


def get_cache_tracker() -> CacheMetricsTracker:
    """Get or create the global cache metrics tracker"""
    global _cache_tracker
    if _cache_tracker is None:
        _cache_tracker = CacheMetricsTracker()
    return _cache_tracker
