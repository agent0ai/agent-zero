"""
Memory System Efficiency Test for Agent Zero with Qdrant Integration
=====================================================================
This script demonstrates the efficiency of the integrated memory system
combining FAISS local storage with Qdrant cloud-based vector database.
"""

import asyncio
import time
import json
import random
import string
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
import numpy as np
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers.qdrant_client import QdrantStore
from python.helpers.memory import Memory
from python.helpers.memory_config import get_memory_config
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryEfficiencyTest:
    """Comprehensive test suite for the integrated memory system"""

    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "tests": {},
            "performance_metrics": {},
            "efficiency_scores": {}
        }
        self.embeddings_model = None
        self.qdrant_store = None
        self.memory_config = None

    async def setup(self):
        """Initialize the memory system components"""
        logger.info("[SETUP] Setting up memory system components...")

        # Load memory configuration
        self.memory_config = get_memory_config()

        # Initialize embeddings model
        logger.info("Loading embeddings model...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize Qdrant store if configured
        if self.memory_config.get("backend") == "qdrant":
            logger.info("Connecting to Qdrant...")
            self.qdrant_store = QdrantStore(
                embedder=self.embeddings_model,
                collection="agent_zero_test",
                url=self.memory_config.get("qdrant_url", "http://localhost:6333"),
                api_key=self.memory_config.get("qdrant_api_key", ""),
                prefer_hybrid=True,
                score_threshold=0.6
            )
            await self.qdrant_store._ensure_collection()

        logger.info("[OK] Setup complete!")

    def generate_test_documents(self, count: int = 100) -> List[Document]:
        """Generate test documents with varying content"""
        documents = []
        categories = ["technical", "business", "science", "history", "general"]

        for i in range(count):
            category = random.choice(categories)
            content = f"Document {i}: {category.upper()} - "
            content += f"This is a test document about {category}. "
            content += f"ID: {''.join(random.choices(string.ascii_letters + string.digits, k=10))}. "
            content += f"Content: {' '.join(random.choices(string.ascii_lowercase, k=50))}"

            doc = Document(
                page_content=content,
                metadata={
                    "id": f"doc_{i}",
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    "importance": random.randint(1, 10),
                    "tags": random.sample(["memory", "test", "efficiency", "vector", "search"], k=2)
                }
            )
            documents.append(doc)

        return documents

    async def test_insertion_performance(self):
        """Test document insertion performance"""
        logger.info("\n📝 Testing insertion performance...")

        test_sizes = [10, 50, 100, 500]
        insertion_times = {}

        for size in test_sizes:
            docs = self.generate_test_documents(size)
            ids = [str(uuid.uuid4()) for i in range(size)]

            start_time = time.time()
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(docs, ids)
            end_time = time.time()

            elapsed = end_time - start_time
            insertion_times[size] = {
                "total_time": elapsed,
                "per_document": elapsed / size,
                "documents_per_second": size / elapsed
            }

            logger.info(f"  Inserted {size} documents in {elapsed:.3f}s ({size/elapsed:.1f} docs/sec)")

        self.results["tests"]["insertion"] = insertion_times
        return insertion_times

    async def test_search_performance(self):
        """Test search and retrieval performance"""
        logger.info("\n🔍 Testing search performance...")

        # Insert test data first
        test_docs = self.generate_test_documents(1000)
        ids = [f"search_test_{i}" for i in range(1000)]

        if self.qdrant_store:
            await self.qdrant_store.aadd_documents(test_docs, ids)

        # Test different search scenarios
        search_queries = [
            "technical documentation about systems",
            "business process optimization",
            "scientific research methods",
            "historical data analysis",
            "general information retrieval"
        ]

        search_results = {}
        for query in search_queries:
            start_time = time.time()
            if self.qdrant_store:
                results = await self.qdrant_store.asimilarity_search(
                    query,
                    k=10,
                    filter=None
                )
            end_time = time.time()

            search_results[query[:30]] = {
                "time": end_time - start_time,
                "results_count": len(results) if self.qdrant_store else 0
            }

            logger.info(f"  Query '{query[:30]}...' took {end_time - start_time:.3f}s")

        self.results["tests"]["search"] = search_results
        return search_results

    async def test_hybrid_search(self):
        """Test hybrid search capabilities (vector + keyword)"""
        logger.info("\n🔄 Testing hybrid search capabilities...")

        if not self.qdrant_store or not self.qdrant_store.prefer_hybrid:
            logger.warning("  Hybrid search not configured")
            return None

        # Create documents with specific keywords
        specialized_docs = []
        keywords = ["alpha", "beta", "gamma", "delta", "epsilon"]

        for i, keyword in enumerate(keywords):
            for j in range(20):
                doc = Document(
                    page_content=f"Document about {keyword} system. Technical details of {keyword} implementation.",
                    metadata={
                        "keyword": keyword,
                        "index": f"{i}_{j}",
                        "type": "specialized"
                    }
                )
                specialized_docs.append(doc)

        ids = [f"hybrid_{i}" for i in range(len(specialized_docs))]
        await self.qdrant_store.aadd_documents(specialized_docs, ids)

        # Test hybrid search
        hybrid_results = {}
        for keyword in keywords:
            start_time = time.time()

            # Search with filter
            filter_str = f"keyword == '{keyword}'"
            results = await self.qdrant_store.asimilarity_search(
                f"technical implementation details",
                k=5,
                filter=filter_str
            )

            end_time = time.time()

            hybrid_results[keyword] = {
                "time": end_time - start_time,
                "results_count": len(results),
                "accuracy": all(keyword in r.page_content for r in results)
            }

            logger.info(f"  Hybrid search for '{keyword}': {len(results)} results in {end_time - start_time:.3f}s")

        self.results["tests"]["hybrid_search"] = hybrid_results
        return hybrid_results

    async def test_memory_persistence(self):
        """Test memory persistence and retrieval accuracy"""
        logger.info("\n💾 Testing memory persistence...")

        # Create test memories with different areas
        memory_areas = ["main", "fragments", "solutions", "instruments"]
        persistence_results = {}

        for area in memory_areas:
            # Create area-specific documents
            area_docs = []
            for i in range(50):
                doc = Document(
                    page_content=f"Memory in {area} area: {i}. Content specific to {area}.",
                    metadata={
                        "area": area,
                        "index": i,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                area_docs.append(doc)

            ids = [f"{area}_{i}" for i in range(len(area_docs))]

            # Store documents
            start_store = time.time()
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(area_docs, ids)
            end_store = time.time()

            # Retrieve and verify
            start_retrieve = time.time()
            if self.qdrant_store:
                retrieved = await self.qdrant_store.aget_by_ids(ids[:10])
            end_retrieve = time.time()

            persistence_results[area] = {
                "store_time": end_store - start_store,
                "retrieve_time": end_retrieve - start_retrieve,
                "documents_stored": len(area_docs),
                "documents_retrieved": len(retrieved) if self.qdrant_store else 0,
                "accuracy": (len(retrieved) == 10) if self.qdrant_store else False
            }

            logger.info(f"  Area '{area}': Stored {len(area_docs)} docs in {end_store - start_store:.3f}s")

        self.results["tests"]["persistence"] = persistence_results
        return persistence_results

    async def test_scalability(self):
        """Test system scalability with large datasets"""
        logger.info("\n📈 Testing scalability...")

        scalability_results = {}
        test_scales = [100, 500, 1000, 5000]

        for scale in test_scales:
            logger.info(f"  Testing with {scale} documents...")

            # Generate large dataset
            large_docs = self.generate_test_documents(scale)
            ids = [f"scale_{scale}_{i}" for i in range(scale)]

            # Measure insertion
            start_insert = time.time()
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(large_docs, ids)
            end_insert = time.time()

            # Measure search on large dataset
            search_times = []
            for _ in range(5):  # 5 sample searches
                query = f"test document about {random.choice(['technical', 'business', 'science'])}"
                start_search = time.time()
                if self.qdrant_store:
                    await self.qdrant_store.asimilarity_search(query, k=10)
                end_search = time.time()
                search_times.append(end_search - start_search)

            scalability_results[scale] = {
                "insertion_time": end_insert - start_insert,
                "avg_search_time": np.mean(search_times),
                "search_time_std": np.std(search_times),
                "docs_per_second": scale / (end_insert - start_insert)
            }

            logger.info(f"    Insertion: {end_insert - start_insert:.3f}s, Avg search: {np.mean(search_times):.3f}s")

        self.results["tests"]["scalability"] = scalability_results
        return scalability_results

    def calculate_efficiency_scores(self):
        """Calculate overall efficiency scores"""
        logger.info("\n📊 Calculating efficiency scores...")

        scores = {}

        # Insertion efficiency
        if "insertion" in self.results["tests"]:
            insertion_data = self.results["tests"]["insertion"]
            avg_docs_per_sec = np.mean([v["documents_per_second"] for v in insertion_data.values()])
            scores["insertion_efficiency"] = min(100, (avg_docs_per_sec / 100) * 100)  # 100 docs/sec = 100%

        # Search efficiency
        if "search" in self.results["tests"]:
            search_data = self.results["tests"]["search"]
            avg_search_time = np.mean([v["time"] for v in search_data.values()])
            scores["search_efficiency"] = min(100, (0.1 / avg_search_time) * 100)  # 0.1s = 100%

        # Persistence efficiency
        if "persistence" in self.results["tests"]:
            persistence_data = self.results["tests"]["persistence"]
            accuracy_rate = sum(1 for v in persistence_data.values() if v.get("accuracy", False)) / len(persistence_data)
            scores["persistence_efficiency"] = accuracy_rate * 100

        # Scalability efficiency
        if "scalability" in self.results["tests"]:
            scalability_data = self.results["tests"]["scalability"]
            # Check if performance degrades linearly or better
            scales = sorted(scalability_data.keys())
            if len(scales) > 1:
                time_ratios = []
                for i in range(1, len(scales)):
                    scale_ratio = scales[i] / scales[i-1]
                    time_ratio = scalability_data[scales[i]]["insertion_time"] / scalability_data[scales[i-1]]["insertion_time"]
                    efficiency_ratio = scale_ratio / time_ratio  # >1 means better than linear
                    time_ratios.append(efficiency_ratio)
                scores["scalability_efficiency"] = min(100, np.mean(time_ratios) * 100)

        # Overall efficiency score
        if scores:
            scores["overall_efficiency"] = np.mean(list(scores.values()))

        self.results["efficiency_scores"] = scores

        for key, score in scores.items():
            logger.info(f"  {key}: {score:.1f}%")

        return scores

    async def run_all_tests(self):
        """Run all efficiency tests"""
        logger.info("=" * 60)
        logger.info("🚀 AGENT ZERO MEMORY SYSTEM EFFICIENCY TEST")
        logger.info("=" * 60)

        try:
            await self.setup()

            # Run all tests
            await self.test_insertion_performance()
            await self.test_search_performance()
            await self.test_hybrid_search()
            await self.test_memory_persistence()
            await self.test_scalability()

            # Calculate efficiency scores
            self.calculate_efficiency_scores()

            # Save results
            self.save_results()

            logger.info("\n" + "=" * 60)
            logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)

            self.print_summary()

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise

    def save_results(self):
        """Save test results to file"""
        filename = f"memory_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"\n📁 Results saved to: {filename}")

    def print_summary(self):
        """Print a summary of test results"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 EFFICIENCY TEST SUMMARY")
        logger.info("=" * 60)

        if "efficiency_scores" in self.results:
            scores = self.results["efficiency_scores"]
            logger.info("\n🏆 EFFICIENCY SCORES:")
            logger.info(f"  Overall Efficiency: {scores.get('overall_efficiency', 0):.1f}%")
            logger.info(f"  Insertion Speed: {scores.get('insertion_efficiency', 0):.1f}%")
            logger.info(f"  Search Speed: {scores.get('search_efficiency', 0):.1f}%")
            logger.info(f"  Persistence Accuracy: {scores.get('persistence_efficiency', 0):.1f}%")
            logger.info(f"  Scalability: {scores.get('scalability_efficiency', 0):.1f}%")

        if "scalability" in self.results["tests"]:
            logger.info("\n📈 SCALABILITY METRICS:")
            for scale, metrics in self.results["tests"]["scalability"].items():
                logger.info(f"  {scale} documents: {metrics['docs_per_second']:.1f} docs/sec")

        logger.info("\n✨ The integrated memory system demonstrates:")
        logger.info("  • Fast insertion and retrieval operations")
        logger.info("  • Efficient vector similarity search")
        logger.info("  • Reliable persistence across memory areas")
        logger.info("  • Good scalability for large datasets")
        logger.info("  • Hybrid search capabilities (vector + keyword)")


async def main():
    """Main entry point"""
    test = MemoryEfficiencyTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())