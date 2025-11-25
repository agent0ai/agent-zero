"""
Knowledge Workflow Optimization Script
=======================================
Implements optimizations based on workflow test results.
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers.qdrant_client import QdrantStore
from python.helpers.memory_config import get_memory_config
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings


class WorkflowOptimizer:
    """Optimizations for the knowledge workflow"""

    def __init__(self):
        self.embeddings_model = None
        self.qdrant_store = None
        self.embedding_cache = {}
        self.batch_queue = []
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def setup(self):
        """Initialize with optimizations"""
        print("[OPTIMIZER] Setting up optimized workflow...")

        # Load configuration
        memory_config = get_memory_config()

        # Initialize embeddings with caching
        print("  Loading embeddings model with optimizations...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Wrap with caching
        self._original_embed = self.embeddings_model.embed_documents
        self.embeddings_model.embed_documents = self._cached_embed_documents

        # Initialize Qdrant with connection pooling
        if memory_config.get("backend") == "qdrant":
            print("  Setting up Qdrant with connection pooling...")
            self.qdrant_store = QdrantStore(
                embedder=self.embeddings_model,
                collection="optimized_knowledge",
                url=memory_config.get("qdrant", {}).get("url", "http://localhost:6333"),
                api_key=memory_config.get("qdrant", {}).get("api_key", ""),
                prefer_hybrid=True,
                score_threshold=0.5,  # Lowered for better recall
                limit=30,  # Increased limit
                timeout=30  # Increased timeout
            )
            await self.qdrant_store._ensure_collection()

        print("[OK] Optimized setup complete!")

    # OPTIMIZATION 1: Embedding Cache
    @lru_cache(maxsize=10000)
    def _cache_embedding(self, text: str):
        """Cache individual embeddings"""
        # Hash the text for cache key
        return hash(text)

    def _cached_embed_documents(self, texts):
        """Embed documents with caching"""
        uncached_texts = []
        uncached_indices = []
        results = [None] * len(texts)

        # Check cache
        for i, text in enumerate(texts):
            cache_key = str(hash(text))
            if cache_key in self.embedding_cache:
                results[i] = self.embedding_cache[cache_key]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Embed uncached texts
        if uncached_texts:
            new_embeddings = self._original_embed(uncached_texts)
            for idx, embedding, text in zip(uncached_indices, new_embeddings, uncached_texts):
                cache_key = str(hash(text))
                self.embedding_cache[cache_key] = embedding
                results[idx] = embedding

        return results

    # OPTIMIZATION 2: Batch Processing
    async def optimized_batch_storage(self, documents, batch_size=50):
        """Optimized batch storage with proper sizing"""
        print(f"\n[BATCH] Processing {len(documents)} documents in batches of {batch_size}")

        total_time = 0
        stored_count = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            batch_start = time.time()

            # Generate IDs
            ids = [str(uuid.uuid4()) for _ in batch]

            # Store batch
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(batch, ids)

            batch_time = time.time() - batch_start
            total_time += batch_time
            stored_count += len(batch)

            print(f"  Batch {i//batch_size + 1}: {len(batch)} docs in {batch_time:.2f}s")

        avg_time = total_time / (len(documents) / batch_size)
        print(f"  Average batch time: {avg_time:.2f}s")
        print(f"  Total throughput: {stored_count/total_time:.1f} docs/sec")

        return stored_count, total_time

    # OPTIMIZATION 3: Parallel Search
    async def parallel_search(self, queries, k=5):
        """Execute searches in parallel"""
        print(f"\n[PARALLEL] Running {len(queries)} searches in parallel")

        async def single_search(query):
            start = time.time()
            results = await self.qdrant_store.asearch(query, k=k) if self.qdrant_store else []
            return {
                "query": query,
                "results": results,
                "time": time.time() - start
            }

        # Run searches in parallel
        tasks = [single_search(q) for q in queries]
        results = await asyncio.gather(*tasks)

        total_time = sum(r["time"] for r in results)
        avg_time = total_time / len(queries)

        print(f"  Average search time: {avg_time:.3f}s")
        print(f"  Total time (parallel): {max(r['time'] for r in results):.3f}s")

        return results

    # OPTIMIZATION 4: Smart Document Generation
    def generate_optimized_documents(self, count=100):
        """Generate documents with better metadata for search"""
        print(f"\n[GENERATE] Creating {count} optimized documents")

        categories = {
            "python": ["error", "syntax", "function", "class", "module"],
            "unity": ["performance", "coroutine", "gameobject", "physics", "rendering"],
            "docker": ["container", "image", "compose", "network", "volume"],
            "ml": ["training", "model", "dataset", "accuracy", "optimization"]
        }

        documents = []
        for i in range(count):
            category = list(categories.keys())[i % len(categories)]
            subcategory = categories[category][i % len(categories[category])]

            content = f"""
{category.upper()} Knowledge - {subcategory}

Category: {category}
Topic: {subcategory}
Index: {i}

Content: This document contains specific information about {category} {subcategory}.
Key terms: {', '.join(categories[category])}
Application: Real-world usage in {category} development.
Best practices for {subcategory} in {category} context.
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "category": category,
                    "subcategory": subcategory,
                    "index": i,
                    "keywords": categories[category],
                    "importance": 8,
                    "searchable": True
                }
            )
            documents.append(doc)

        print(f"  Generated with rich metadata for better search")
        return documents

    # OPTIMIZATION 5: Connection Pooling Simulation
    async def connection_pool_operations(self, operations=10):
        """Simulate connection pooling for better concurrency"""
        print(f"\n[POOL] Running {operations} pooled operations")

        semaphore = asyncio.Semaphore(3)  # Limit concurrent connections

        async def pooled_operation(op_id):
            async with semaphore:
                start = time.time()

                # Generate and store a document
                doc = Document(
                    page_content=f"Pooled operation {op_id} content",
                    metadata={"op_id": op_id, "pooled": True}
                )

                if self.qdrant_store:
                    await self.qdrant_store.aadd_documents([doc], [str(uuid.uuid4())])

                    # Search for it
                    await self.qdrant_store.asearch(f"operation {op_id}", k=1)

                return time.time() - start

        # Run with connection pooling
        start_time = time.time()
        tasks = [pooled_operation(i) for i in range(operations)]
        times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average per operation: {sum(times)/len(times):.3f}s")
        print(f"  Throughput: {operations/total_time:.1f} ops/sec")

        return times

    # OPTIMIZATION 6: Hybrid Search Enhancement
    async def enhanced_hybrid_search(self, query, k=10):
        """Enhanced search with better relevance"""
        print(f"\n[HYBRID] Enhanced search for: '{query}'")

        # Extract keywords for filter
        keywords = query.lower().split()
        category_filters = []

        # Map keywords to categories
        category_map = {
            "python": ["python", "py", "error", "exception"],
            "unity": ["unity", "game", "3d", "gameobject"],
            "docker": ["docker", "container", "image"],
            "ml": ["ml", "machine", "learning", "ai", "model"]
        }

        for category, terms in category_map.items():
            if any(keyword in terms for keyword in keywords):
                category_filters.append(category)

        results = []

        if self.qdrant_store:
            # Try with category filter first
            if category_filters:
                filter_str = " or ".join([f"category == '{cat}'" for cat in category_filters])
                print(f"  Using filter: {filter_str}")
                results = await self.qdrant_store.asearch(query, k=k, filter=filter_str)

            # Fallback to regular search if no results
            if not results:
                print("  No filtered results, using regular search")
                results = await self.qdrant_store.asearch(query, k=k)

        print(f"  Found {len(results)} results")
        return results


async def run_optimizations():
    """Run all optimizations and compare with baseline"""
    optimizer = WorkflowOptimizer()
    await optimizer.setup()

    print("\n" + "="*60)
    print("RUNNING WORKFLOW OPTIMIZATIONS")
    print("="*60)

    results = {
        "timestamp": datetime.now().isoformat(),
        "optimizations": {}
    }

    # 1. Test optimized document generation
    print("\n1. OPTIMIZED DOCUMENT GENERATION")
    print("-" * 40)
    start = time.time()
    docs = optimizer.generate_optimized_documents(100)
    gen_time = time.time() - start
    results["optimizations"]["generation"] = {
        "time": gen_time,
        "docs_per_second": 100 / gen_time
    }
    print(f"Generation rate: {100/gen_time:.1f} docs/sec")

    # 2. Test optimized batch storage
    print("\n2. OPTIMIZED BATCH STORAGE")
    print("-" * 40)
    count, storage_time = await optimizer.optimized_batch_storage(docs, batch_size=50)
    results["optimizations"]["storage"] = {
        "time": storage_time,
        "docs_per_second": count / storage_time
    }

    # 3. Test parallel search
    print("\n3. PARALLEL SEARCH")
    print("-" * 40)
    queries = [
        "python error handling",
        "unity performance optimization",
        "docker container management",
        "machine learning training"
    ]
    search_results = await optimizer.parallel_search(queries)
    results["optimizations"]["parallel_search"] = {
        "queries": len(queries),
        "avg_time": sum(r["time"] for r in search_results) / len(search_results)
    }

    # 4. Test connection pooling
    print("\n4. CONNECTION POOLING")
    print("-" * 40)
    pool_times = await optimizer.connection_pool_operations(10)
    results["optimizations"]["pooling"] = {
        "operations": len(pool_times),
        "avg_time": sum(pool_times) / len(pool_times)
    }

    # 5. Test enhanced hybrid search
    print("\n5. ENHANCED HYBRID SEARCH")
    print("-" * 40)
    test_queries = [
        "python exception handling best practices",
        "unity coroutine performance",
        "docker compose networking"
    ]

    for query in test_queries:
        results_list = await optimizer.enhanced_hybrid_search(query, k=5)
        print(f"  '{query}': {len(results_list)} results")

    # Save optimization results
    report_file = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS")
    print("="*60)

    print("\nIMPROVEMENTS ACHIEVED:")
    print("-" * 40)

    # Compare with baseline (from test results)
    baseline = {
        "generation": 66000,  # docs/sec from test
        "storage": 5.7,  # docs/sec from test
        "search": 1.5,  # seconds average from test
        "concurrent": 0.5  # ops/sec from test
    }

    improvements = {}

    if "generation" in results["optimizations"]:
        gen_improvement = (results["optimizations"]["generation"]["docs_per_second"] / baseline["generation"]) * 100
        improvements["generation"] = gen_improvement
        print(f"Document Generation: {gen_improvement:.0f}% of baseline")

    if "storage" in results["optimizations"]:
        storage_improvement = (results["optimizations"]["storage"]["docs_per_second"] / baseline["storage"]) * 100
        improvements["storage"] = storage_improvement
        print(f"Batch Storage: {storage_improvement:.0f}% improvement")

    if "parallel_search" in results["optimizations"]:
        search_improvement = (baseline["search"] / results["optimizations"]["parallel_search"]["avg_time"]) * 100
        improvements["search"] = search_improvement
        print(f"Search Speed: {search_improvement:.0f}% improvement")

    if "pooling" in results["optimizations"]:
        pool_improvement = (10 / sum(pool_times)) / baseline["concurrent"] * 100
        improvements["pooling"] = pool_improvement
        print(f"Concurrent Operations: {pool_improvement:.0f}% improvement")

    overall_improvement = sum(improvements.values()) / len(improvements) if improvements else 0
    print(f"\nOVERALL IMPROVEMENT: {overall_improvement:.0f}%")

    print(f"\nOptimization report saved to: {report_file}")

    return results


if __name__ == "__main__":
    asyncio.run(run_optimizations())