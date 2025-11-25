"""
High-Performance Memory Cache for Unity Knowledge Base.

This module provides:
- LRU cache for frequently accessed entities
- Batch operation buffering
- Embedding cache with persistence
- Query result caching with TTL
- Memory-efficient storage strategies
"""

import asyncio
import hashlib
import json
import os
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import logging
from functools import wraps

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entry in the cache with metadata."""
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl_seconds: Optional[float] = None

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds


@dataclass
class BatchOperation:
    """Represents a pending batch operation."""
    operation: str  # "insert", "update", "delete"
    collection: str
    documents: List[Document]
    ids: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = 3600,  # 1 hour
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            # Update access tracking
            entry.accessed_at = time.time()
            entry.access_count += 1

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self._hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ):
        """Set value in cache."""
        async with self._lock:
            # Remove if exists (to update position)
            if key in self._cache:
                del self._cache[key]

            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                ttl_seconds=ttl or self.default_ttl,
            )

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    async def cleanup_expired(self):
        """Remove all expired entries."""
        async with self._lock:
            expired = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired:
                del self._cache[key]
            return len(expired)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
        }


class EmbeddingCache:
    """
    Persistent embedding cache for reducing API calls.

    Features:
    - In-memory LRU cache
    - Disk persistence for warm starts
    - Batch embedding support
    - Automatic cleanup
    """

    def __init__(
        self,
        cache_dir: str = "memory/embedding_cache",
        max_memory_entries: int = 10000,
        max_disk_entries: int = 100000,
        persist_interval: int = 100,  # Persist every N new embeddings
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_memory = max_memory_entries
        self.max_disk = max_disk_entries
        self.persist_interval = persist_interval

        self._memory_cache: OrderedDict[str, List[float]] = OrderedDict()
        self._pending_persist: Dict[str, List[float]] = {}
        self._persist_count = 0
        self._lock = asyncio.Lock()

        # Load existing cache on init
        self._load_from_disk()

    def _hash_text(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _load_from_disk(self):
        """Load embeddings from disk cache."""
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    # Load most recent entries
                    for key, emb in list(data.items())[-self.max_memory:]:
                        self._memory_cache[key] = emb
                logger.info(f"Loaded {len(self._memory_cache)} embeddings from cache")
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")

    async def _persist_to_disk(self):
        """Persist pending embeddings to disk."""
        if not self._pending_persist:
            return

        cache_file = self.cache_dir / "embeddings.pkl"

        async with self._lock:
            try:
                # Load existing
                existing = {}
                if cache_file.exists():
                    with open(cache_file, "rb") as f:
                        existing = pickle.load(f)

                # Merge new
                existing.update(self._pending_persist)

                # Trim to max disk size
                if len(existing) > self.max_disk:
                    existing = dict(list(existing.items())[-self.max_disk:])

                # Save
                with open(cache_file, "wb") as f:
                    pickle.dump(existing, f)

                self._pending_persist.clear()
                logger.debug(f"Persisted embeddings to disk: {len(existing)} total")

            except Exception as e:
                logger.error(f"Failed to persist embeddings: {e}")

    async def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        key = self._hash_text(text)

        async with self._lock:
            if key in self._memory_cache:
                # Move to end (most recently used)
                self._memory_cache.move_to_end(key)
                return self._memory_cache[key]

        return None

    async def get_many(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """Get multiple embeddings from cache."""
        results = {}
        async with self._lock:
            for text in texts:
                key = self._hash_text(text)
                if key in self._memory_cache:
                    self._memory_cache.move_to_end(key)
                    results[text] = self._memory_cache[key]
                else:
                    results[text] = None
        return results

    async def set(self, text: str, embedding: List[float]):
        """Set embedding in cache."""
        key = self._hash_text(text)

        async with self._lock:
            # Evict oldest if at capacity
            while len(self._memory_cache) >= self.max_memory:
                self._memory_cache.popitem(last=False)

            self._memory_cache[key] = embedding
            self._pending_persist[key] = embedding
            self._persist_count += 1

        # Persist periodically
        if self._persist_count >= self.persist_interval:
            await self._persist_to_disk()
            self._persist_count = 0

    async def set_many(self, embeddings: Dict[str, List[float]]):
        """Set multiple embeddings in cache."""
        async with self._lock:
            for text, embedding in embeddings.items():
                key = self._hash_text(text)

                while len(self._memory_cache) >= self.max_memory:
                    self._memory_cache.popitem(last=False)

                self._memory_cache[key] = embedding
                self._pending_persist[key] = embedding

            self._persist_count += len(embeddings)

        if self._persist_count >= self.persist_interval:
            await self._persist_to_disk()
            self._persist_count = 0

    async def flush(self):
        """Force persistence to disk."""
        await self._persist_to_disk()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "memory_entries": len(self._memory_cache),
            "pending_persist": len(self._pending_persist),
            "max_memory": self.max_memory,
            "max_disk": self.max_disk,
        }


class QueryResultCache:
    """
    Cache for search query results with intelligent invalidation.

    Features:
    - Query normalization for better hit rates
    - TTL-based expiration
    - Pattern-based invalidation
    - Statistics tracking
    """

    def __init__(
        self,
        max_entries: int = 500,
        default_ttl: float = 300,  # 5 minutes
    ):
        self.cache = LRUCache(max_size=max_entries, default_ttl=default_ttl)
        self._invalidation_patterns: List[str] = []

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent cache keys."""
        # Lowercase, remove extra whitespace
        normalized = " ".join(query.lower().split())
        return normalized

    def _make_key(
        self,
        query: str,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate cache key from query parameters."""
        key_parts = [self._normalize_query(query)]

        if collection:
            key_parts.append(f"c:{collection}")

        if filters:
            # Sort filters for consistent keys
            filter_str = json.dumps(filters, sort_keys=True)
            key_parts.append(f"f:{filter_str}")

        return hashlib.md5(":".join(key_parts).encode()).hexdigest()

    async def get(
        self,
        query: str,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Any]]:
        """Get cached query results."""
        key = self._make_key(query, collection, filters)
        return await self.cache.get(key)

    async def set(
        self,
        query: str,
        results: List[Any],
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ):
        """Cache query results."""
        key = self._make_key(query, collection, filters)
        await self.cache.set(key, results, ttl)

    async def invalidate_collection(self, collection: str):
        """Invalidate all results for a collection."""
        # This is a simple approach - could be optimized with collection tracking
        await self.cache.clear()
        logger.debug(f"Invalidated cache for collection: {collection}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate results matching a pattern."""
        # Store pattern for future checks
        self._invalidation_patterns.append(pattern)
        # Clear cache (simple approach)
        await self.cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.stats()


class BatchOperationBuffer:
    """
    Buffer for batching database operations.

    Features:
    - Automatic batching of inserts/updates/deletes
    - Configurable batch size and flush interval
    - Async flush with retry
    - Operation coalescing
    """

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 5.0,  # seconds
        max_buffer_size: int = 1000,
        flush_callback: Optional[Callable] = None,
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_buffer_size = max_buffer_size
        self.flush_callback = flush_callback

        self._buffer: Dict[str, List[BatchOperation]] = {
            "insert": [],
            "update": [],
            "delete": [],
        }
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self._ops_buffered = 0
        self._ops_flushed = 0
        self._flushes = 0

    async def start(self):
        """Start the automatic flush task."""
        self._running = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())

    async def stop(self):
        """Stop and flush remaining operations."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
        await self.flush()

    async def add_insert(
        self,
        collection: str,
        documents: List[Document],
        ids: List[str],
        **metadata,
    ):
        """Add insert operation to buffer."""
        await self._add_operation(
            "insert", collection, documents, ids, metadata
        )

    async def add_update(
        self,
        collection: str,
        documents: List[Document],
        ids: List[str],
        **metadata,
    ):
        """Add update operation to buffer."""
        await self._add_operation(
            "update", collection, documents, ids, metadata
        )

    async def add_delete(
        self,
        collection: str,
        ids: List[str],
        **metadata,
    ):
        """Add delete operation to buffer."""
        await self._add_operation(
            "delete", collection, [], ids, metadata
        )

    async def _add_operation(
        self,
        operation: str,
        collection: str,
        documents: List[Document],
        ids: List[str],
        metadata: Dict[str, Any],
    ):
        """Add operation to buffer."""
        async with self._lock:
            self._buffer[operation].append(BatchOperation(
                operation=operation,
                collection=collection,
                documents=documents,
                ids=ids,
                metadata=metadata,
            ))
            self._ops_buffered += len(ids)

            # Check if we should flush
            total_buffered = sum(len(ops) for ops in self._buffer.values())
            if total_buffered >= self.max_buffer_size:
                await self._do_flush()

    async def flush(self):
        """Manually flush all buffered operations."""
        async with self._lock:
            await self._do_flush()

    async def _do_flush(self):
        """Execute all buffered operations."""
        if not self.flush_callback:
            logger.warning("No flush callback configured")
            return

        for operation, ops in self._buffer.items():
            if not ops:
                continue

            # Group by collection
            by_collection: Dict[str, List[BatchOperation]] = {}
            for op in ops:
                if op.collection not in by_collection:
                    by_collection[op.collection] = []
                by_collection[op.collection].append(op)

            # Execute per collection
            for collection, collection_ops in by_collection.items():
                try:
                    # Combine operations
                    all_docs = []
                    all_ids = []
                    for op in collection_ops:
                        all_docs.extend(op.documents)
                        all_ids.extend(op.ids)

                    if all_ids:
                        await self.flush_callback(
                            operation=operation,
                            collection=collection,
                            documents=all_docs,
                            ids=all_ids,
                        )
                        self._ops_flushed += len(all_ids)

                except Exception as e:
                    logger.error(f"Flush failed for {operation}/{collection}: {e}")

            ops.clear()

        self._flushes += 1

    async def _auto_flush_loop(self):
        """Background task for periodic flushing."""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            try:
                await self.flush()
            except Exception as e:
                logger.error(f"Auto-flush error: {e}")

    def stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "buffered": sum(len(ops) for ops in self._buffer.values()),
            "ops_buffered_total": self._ops_buffered,
            "ops_flushed_total": self._ops_flushed,
            "flushes": self._flushes,
            "by_operation": {
                op: len(ops) for op, ops in self._buffer.items()
            },
        }


class UnityMemoryCache:
    """
    Unified caching layer for Unity knowledge base.

    Combines:
    - Entity cache (LRU)
    - Embedding cache (persistent)
    - Query result cache (TTL)
    - Batch operation buffer
    """

    def __init__(
        self,
        cache_dir: str = "memory/unity_cache",
        entity_cache_size: int = 5000,
        embedding_cache_size: int = 10000,
        query_cache_size: int = 500,
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.entity_cache = LRUCache(
            max_size=entity_cache_size,
            default_ttl=3600,  # 1 hour
        )

        self.embedding_cache = EmbeddingCache(
            cache_dir=str(self.cache_dir / "embeddings"),
            max_memory_entries=embedding_cache_size,
        )

        self.query_cache = QueryResultCache(
            max_entries=query_cache_size,
            default_ttl=300,  # 5 minutes
        )

        self.batch_buffer = BatchOperationBuffer(
            batch_size=batch_size,
            flush_interval=flush_interval,
        )

    async def start(self, flush_callback: Optional[Callable] = None):
        """Start caching services."""
        self.batch_buffer.flush_callback = flush_callback
        await self.batch_buffer.start()

    async def stop(self):
        """Stop caching services."""
        await self.batch_buffer.stop()
        await self.embedding_cache.flush()

    async def get_entity(self, entity_id: str) -> Optional[Document]:
        """Get entity from cache."""
        return await self.entity_cache.get(entity_id)

    async def set_entity(self, entity_id: str, document: Document):
        """Cache entity."""
        await self.entity_cache.set(entity_id, document)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        return await self.embedding_cache.get(text)

    async def set_embedding(self, text: str, embedding: List[float]):
        """Cache embedding."""
        await self.embedding_cache.set(text, embedding)

    async def get_embeddings_batch(
        self,
        texts: List[str],
    ) -> Tuple[Dict[str, List[float]], List[str]]:
        """
        Get cached embeddings, return cached and uncached texts.

        Returns:
            Tuple of (cached embeddings dict, list of uncached texts)
        """
        results = await self.embedding_cache.get_many(texts)
        cached = {t: e for t, e in results.items() if e is not None}
        uncached = [t for t, e in results.items() if e is None]
        return cached, uncached

    async def set_embeddings_batch(self, embeddings: Dict[str, List[float]]):
        """Cache multiple embeddings."""
        await self.embedding_cache.set_many(embeddings)

    async def get_query_results(
        self,
        query: str,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Any]]:
        """Get cached query results."""
        return await self.query_cache.get(query, collection, filters)

    async def set_query_results(
        self,
        query: str,
        results: List[Any],
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """Cache query results."""
        await self.query_cache.set(query, results, collection, filters)

    async def buffer_insert(
        self,
        collection: str,
        documents: List[Document],
        ids: List[str],
    ):
        """Buffer insert operation."""
        await self.batch_buffer.add_insert(collection, documents, ids)

    async def buffer_delete(self, collection: str, ids: List[str]):
        """Buffer delete operation."""
        await self.batch_buffer.add_delete(collection, ids)

    async def flush_operations(self):
        """Flush all buffered operations."""
        await self.batch_buffer.flush()

    async def invalidate_collection(self, collection: str):
        """Invalidate all caches for a collection."""
        await self.query_cache.invalidate_collection(collection)

    async def cleanup(self):
        """Cleanup expired entries."""
        await self.entity_cache.cleanup_expired()

    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "entity_cache": self.entity_cache.stats(),
            "embedding_cache": self.embedding_cache.stats(),
            "query_cache": self.query_cache.stats(),
            "batch_buffer": self.batch_buffer.stats(),
        }


def cached_search(cache: UnityMemoryCache, ttl: float = 300):
    """Decorator for caching search results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(
            query: str,
            collection: Optional[str] = None,
            filters: Optional[Dict[str, Any]] = None,
            **kwargs
        ):
            # Check cache
            cached = await cache.get_query_results(query, collection, filters)
            if cached is not None:
                return cached

            # Execute search
            results = await func(query, collection=collection, filters=filters, **kwargs)

            # Cache results
            await cache.set_query_results(
                query, results, collection, filters
            )

            return results
        return wrapper
    return decorator
