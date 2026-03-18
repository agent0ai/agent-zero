---
    title: "⚡ Performance: Optimize FAISS vector search for large memory"
    labels: "performance, enhancement, database"
    ---

    ## Problem

    FAISS vector database performance degrades significantly with >100k memory entries:

    - Search latency increases from ~10ms to >500ms
    - Memory usage grows linearly (and sometimes quadratically)
    - Index building/saving becomes slow
    - Concurrent searches block each other

    ## Current Bottlenecks

    1. **Flat Index** (`IndexFlatIP`)
       ```python
       index = faiss.IndexFlatIP(dimension)
       ```
       - Brute-force search: O(N) per query
       - No approximation, searches all vectors
       - Fine for <10k vectors, poor for >100k

    2. **Single Shared Index**
       - All agents share same FAISS index per memory_subdir
       - No sharding by agent/project
       - Potential lock contention (investigate if FAISS is thread-safe)

    3. **No Caching**
       - Every semantic search hits FAISS
       - Hot queries (common searches) recomputed
       - No query result caching layer

    4. **Embedding Model Loading**
       - Each memory subdir loads embedding model separately
       - If `default` and `projects/x` both use same model, loaded twice
       - Wastes GPU/CPU memory

    5. **Synchronous Operations**
       - `Memory.search_similarity_threshold()` is async but blocks on FAISS
       - Should use `await` for async FAISS if available, or run in thread pool

    ## Proposed Optimizations

    ### 1. Switch to HNSW Index (High Priority)

    HNSW (Hierarchical Navigable Small World) provides:
    - O(log N) search complexity
    - 95%+ recall with proper parameters
    - Fast incremental addition

    ```python
    # Current (Flat)
    index = faiss.IndexFlatIP(dimension)

    # HNSW replacement
    M = 32  # Number of connections per layer (16-64 typical)
    ef_construction = 200  # Depth of search during construction
    index = faiss.IndexHNSWFlat(dimension, M)
    index.hnsw.efConstruction = ef_construction
    index.hnsw.efSearch = 64  # Depth during search (trade speed vs recall)

    # Save index
    faiss.write_index(index, "index.faiss")
    ```

    **Estimated improvement:**
    - 100k vectors: 500ms → 20ms (25x faster)
    - 1M vectors: 5s → 50ms (100x faster)

    ### 2. Per-Project/Agent Sharding (Medium Priority)

    Split memory into separate indexes:

    ```python
    # Instead of:
    memory_subdir = "default"  # All agents share this

    # Use:
    memory_subdir = f"projects/{project_id}"  # Isolated per project
    # Or even:
    memory_subdir = f"agents/{agent_context_id}"  # Per agent
    ```

    **Benefits:**
    - Smaller indexes per shard
    - Reduced lock contention
    - Can defragment/compact per project

    **Tradeoffs:**
    - Cross-project search requires multiple indexes
    - Increases memory footprint if many small agents

    ### 3. Add Query Result Caching (Medium Priority)

    ```python
    from functools import lru_cache
    import hashlib

    @lru_cache(maxsize=1000)
    def cached_similarity_search(query_hash: str, k: int):
        # Embedding lookup is deterministic, can cache
        return perform_faiss_search(query_embedding, k)

    def get_query_hash(query: str, filters: dict) -> str:
        return hashlib.sha256(f"{query}:{json.dumps(filters, sort_keys=True)}".encode()).hexdigest()
    ```

    **Cache invalidation:**
    - When memory entries added/deleted → clear relevant cache
    - Use TTL (e.g., 5 minutes) for memory updates
    - Separate cache per memory_subdir

    ### 4. Async FAISS Operations (Low Priority)

    FAISS is synchronous. Offload to thread pool:

    ```python
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=4)

    async def search_async(query, k):
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(executor, index.search, query, k)
        return await future
    ```

    **Benefit:** Agent event loop not blocked during search

    ### 5. Embedding Model Caching (Low Priority)

    Singleton pattern for embedding models:

    ```python
    # Current: Each Memory.initialize() creates new model
    model = models.get_embedding_model(...)  # New instance each time

    # Proposed: Cache by model config
    _embedding_cache = {}

    def get_cached_embedding_model(provider, name, **kwargs):
        key = f"{provider}/{name}:{hash(str(kwargs))}"
        if key not in _embedding_cache:
            _embedding_cache[key] = models.get_embedding_model(provider, name, **kwargs)
        return _embedding_cache[key]
    ```

    **Impact:** Memory savings when multiple memory subdirs use same model

    ## Migration Plan

    ### Phase 1: HNSW Index (Quick Win)
    1. Add `index_type` setting to `settings.json`: `"vector_index": "flat" | "hnsw"`
    2. If setting is `hnsw`, create HNSW index on first load
    3. **Migration:** If existing Flat index exists:
       - Load Flat index
       - Create HNSW index with same vectors
       - Save HNSW, delete Flat
       - One-time operation

    ### Phase 2: Caching
    1. Add `redis` optional dependency for distributed cache
    2. Implement `MemoryCache` class with `get/set/invalidate`
    3. Wrap `Memory.search_similarity_threshold()` with cache
    4. Cache key includes: query, filters, k, threshold
    5. TTL: 300 seconds (5 minutes)

    ### Phase 3: Sharding
    1. Modify `get_context_memory_subdir()` to include project/agent ID
    2. Ensure project isolation already works (check `projects.py`)
    3. Add cross-shard search when needed (query all shards, merge results)
    4. Document sharding strategy

    ## Benchmarking

    Before/after metrics:

    ```python
    # benchmark.py
    import time

    # 100k vectors, dimension=384
    queries = ["test query 1", "test query 2", ...]

    for query in queries:
        start = time.time()
        results = memory.search(query, k=10)
        elapsed = time.time() - start
        print(f"Search took {elapsed*1000:.1f}ms")
    ```

    Target:
    - Current (Flat): 500-1000ms
    - HNSW: <50ms
    - With caching: <5ms for hot queries

    ## Dependencies

    - `faiss` already installed (includes HNSW)
    - Optional: `redis` for distributed cache
    - `pytest-benchmark` for performance regression tests

    ## Testing

    - [ ] HNSW index produces same top-10 results as Flat (within 5% variance)
    - [ ] Search latency reduced by >80% for large indexes (>100k vectors)
    - [ ] Cache hit rate >70% for repeated queries
    - [ ] No memory leaks from embedding model duplication
    - [ ] Concurrent searches don't degrade performance

    ## Monitoring

    Add metrics:
    - `vector_search_duration_seconds` (histogram)
    - `vector_index_type` (gauge: 0=flat, 1=hnsw)
    - `vector_cache_hits_total`, `vector_cache_misses_total`
    - `embedding_model_loads_total`

    ## Risks

    - **HNSW recall:** May miss some vectors vs brute-force
      - Mitigation: Set `efSearch` high enough for 95%+ recall
      - Test with production-like queries

    - **Migration downtime:** Large index conversion takes minutes
      - Mitigation: Do on first startup, show progress bar

    - **Cache invalidation complexity:**
      - Start with simple TTL-based, move to event-driven later

    ## Acceptance Criteria

    1. Search latency <50ms for 100k+ vectors (measured p95)
    2. Memory usage reduced by 20% (index + embeddings)
    3. No regression in search quality (recall >95%)
    4. Hot queries (repeated within TTL) return in <5ms
    5. All existing functionality preserved

    ---
    *Performance optimization critical for scaling to production workloads.*
    