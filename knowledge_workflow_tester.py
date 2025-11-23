"""
Knowledge System Workflow & Dataflow Tester
============================================
Comprehensive testing framework to validate and optimize the knowledge generation pipeline.
"""

import asyncio
import time
import json
import uuid
import hashlib
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path
import os
import sys
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers.qdrant_client import QdrantStore
from python.helpers.memory_config import get_memory_config
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings


class WorkflowTester:
    """Test and optimize the knowledge system workflow"""

    def __init__(self):
        self.embeddings_model = None
        self.qdrant_store = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "metrics": {},
            "optimizations": []
        }
        self.test_collection = "workflow_test"

    async def setup(self):
        """Initialize test environment"""
        print("[SETUP] Initializing Workflow Tester...")

        # Load configuration
        memory_config = get_memory_config()

        # Initialize embeddings
        print("  Loading embeddings model...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize Qdrant
        if memory_config.get("backend") == "qdrant":
            print("  Connecting to Qdrant test collection...")
            self.qdrant_store = QdrantStore(
                embedder=self.embeddings_model,
                collection=self.test_collection,
                url=memory_config.get("qdrant", {}).get("url", "http://localhost:6333"),
                api_key=memory_config.get("qdrant", {}).get("api_key", ""),
                prefer_hybrid=True,
                score_threshold=0.6
            )
            await self.qdrant_store._ensure_collection()

        print("[OK] Setup complete!\n")

    # TEST 1: Document Generation Efficiency
    async def test_document_generation_efficiency(self) -> Dict:
        """Test how efficiently documents are generated"""
        print("="*60)
        print("TEST 1: DOCUMENT GENERATION EFFICIENCY")
        print("="*60)

        test_result = {
            "test_name": "document_generation_efficiency",
            "status": "running",
            "metrics": {}
        }

        batch_sizes = [10, 50, 100, 500]
        generation_times = {}

        for size in batch_sizes:
            print(f"\nGenerating {size} documents...")
            start_time = time.time()

            documents = []
            for i in range(size):
                # Simulate realistic document generation
                content = self._generate_realistic_content(i)
                doc = Document(
                    page_content=content,
                    metadata={
                        "id": f"gen_test_{i}",
                        "batch_size": size,
                        "timestamp": datetime.now().isoformat(),
                        "content_hash": hashlib.md5(content.encode()).hexdigest()[:8]
                    }
                )
                documents.append(doc)

            generation_time = time.time() - start_time
            generation_times[size] = {
                "total_time": generation_time,
                "per_document": generation_time / size,
                "docs_per_second": size / generation_time
            }

            print(f"  Generated {size} docs in {generation_time:.3f}s ({size/generation_time:.1f} docs/sec)")

        # Calculate efficiency score
        efficiency_scores = []
        for size, metrics in generation_times.items():
            # Ideal is 1000+ docs/sec for generation
            score = min(100, (metrics["docs_per_second"] / 1000) * 100)
            efficiency_scores.append(score)

        test_result["metrics"] = generation_times
        test_result["efficiency_score"] = statistics.mean(efficiency_scores)
        test_result["status"] = "passed" if test_result["efficiency_score"] > 70 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    # TEST 2: Embedding Generation Speed
    async def test_embedding_generation_speed(self) -> Dict:
        """Test embedding generation performance"""
        print("\n" + "="*60)
        print("TEST 2: EMBEDDING GENERATION SPEED")
        print("="*60)

        test_result = {
            "test_name": "embedding_generation_speed",
            "status": "running",
            "metrics": {}
        }

        test_texts = [
            "Short text for embedding",
            "Medium length text that contains more information for the embedding model to process",
            "Long text " * 50  # Simulate long document
        ]

        for text_type, text in zip(["short", "medium", "long"], test_texts):
            print(f"\nTesting {text_type} text embedding...")

            # Test single embedding
            start_time = time.time()
            embedding = await asyncio.to_thread(
                self.embeddings_model.embed_query, text
            )
            single_time = time.time() - start_time

            # Test batch embedding
            batch_size = 100
            texts = [text] * batch_size
            start_time = time.time()
            embeddings = await asyncio.to_thread(
                self.embeddings_model.embed_documents, texts
            )
            batch_time = time.time() - start_time

            test_result["metrics"][text_type] = {
                "single_time": single_time,
                "batch_time": batch_time,
                "batch_size": batch_size,
                "per_document": batch_time / batch_size,
                "speedup": (single_time * batch_size) / batch_time
            }

            print(f"  Single: {single_time:.4f}s")
            print(f"  Batch ({batch_size}): {batch_time:.3f}s ({batch_time/batch_size:.4f}s per doc)")
            print(f"  Speedup: {test_result['metrics'][text_type]['speedup']:.2f}x")

        # Calculate efficiency
        avg_speedup = statistics.mean([m["speedup"] for m in test_result["metrics"].values()])
        test_result["efficiency_score"] = min(100, avg_speedup * 10)  # 10x speedup = 100%
        test_result["status"] = "passed" if avg_speedup > 5 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    # TEST 3: Storage Pipeline Throughput
    async def test_storage_pipeline_throughput(self) -> Dict:
        """Test the complete storage pipeline throughput"""
        print("\n" + "="*60)
        print("TEST 3: STORAGE PIPELINE THROUGHPUT")
        print("="*60)

        test_result = {
            "test_name": "storage_pipeline_throughput",
            "status": "running",
            "metrics": {}
        }

        test_batches = [10, 50, 100, 200]
        throughput_metrics = {}

        for batch_size in test_batches:
            print(f"\nTesting batch size: {batch_size}")

            # Generate documents
            documents = []
            for i in range(batch_size):
                content = f"Pipeline test document {i}: {self._generate_realistic_content(i)}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "test": "pipeline",
                        "batch": batch_size,
                        "index": i
                    }
                )
                documents.append(doc)

            # Measure complete pipeline time
            pipeline_start = time.time()

            # 1. Generate embeddings
            embed_start = time.time()
            texts = [d.page_content for d in documents]
            embeddings = await asyncio.to_thread(
                self.embeddings_model.embed_documents, texts
            )
            embed_time = time.time() - embed_start

            # 2. Store in Qdrant
            store_start = time.time()
            ids = [str(uuid.uuid4()) for _ in documents]
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(documents, ids)
            store_time = time.time() - store_start

            pipeline_time = time.time() - pipeline_start

            throughput_metrics[batch_size] = {
                "total_time": pipeline_time,
                "embedding_time": embed_time,
                "storage_time": store_time,
                "docs_per_second": batch_size / pipeline_time,
                "embedding_percentage": (embed_time / pipeline_time) * 100,
                "storage_percentage": (store_time / pipeline_time) * 100
            }

            print(f"  Total: {pipeline_time:.3f}s ({batch_size/pipeline_time:.1f} docs/sec)")
            print(f"  Embedding: {embed_time:.3f}s ({throughput_metrics[batch_size]['embedding_percentage']:.1f}%)")
            print(f"  Storage: {store_time:.3f}s ({throughput_metrics[batch_size]['storage_percentage']:.1f}%)")

        test_result["metrics"] = throughput_metrics

        # Calculate efficiency
        avg_throughput = statistics.mean([m["docs_per_second"] for m in throughput_metrics.values()])
        test_result["efficiency_score"] = min(100, (avg_throughput / 100) * 100)  # 100 docs/sec = 100%
        test_result["status"] = "passed" if avg_throughput > 50 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    # TEST 4: Search Accuracy and Relevance
    async def test_search_accuracy(self) -> Dict:
        """Test search accuracy and relevance scoring"""
        print("\n" + "="*60)
        print("TEST 4: SEARCH ACCURACY AND RELEVANCE")
        print("="*60)

        test_result = {
            "test_name": "search_accuracy",
            "status": "running",
            "metrics": {}
        }

        # Create known test documents with specific content
        test_cases = [
            {
                "topic": "Python error handling",
                "documents": [
                    "Python try-except blocks are essential for error handling",
                    "TypeError in Python occurs when wrong type is used",
                    "Best practices for Python exception handling include specific catches"
                ],
                "queries": [
                    "Python exception handling",
                    "TypeError fix",
                    "try except best practices"
                ]
            },
            {
                "topic": "Unity performance",
                "documents": [
                    "Unity performance optimization requires profiler analysis",
                    "Object pooling in Unity reduces instantiation overhead",
                    "LOD system in Unity improves rendering performance"
                ],
                "queries": [
                    "Unity optimization",
                    "object pooling Unity",
                    "Unity profiler usage"
                ]
            }
        ]

        accuracy_metrics = []

        for test_case in test_cases:
            print(f"\nTesting topic: {test_case['topic']}")

            # Store test documents
            docs = []
            for i, content in enumerate(test_case["documents"]):
                doc = Document(
                    page_content=content,
                    metadata={
                        "topic": test_case["topic"],
                        "test_id": f"accuracy_{i}"
                    }
                )
                docs.append(doc)

            ids = [str(uuid.uuid4()) for _ in docs]
            if self.qdrant_store:
                await self.qdrant_store.aadd_documents(docs, ids)

            # Test queries
            query_results = []
            for query in test_case["queries"]:
                start_time = time.time()
                if self.qdrant_store:
                    results = await self.qdrant_store.asearch(query, k=3)
                else:
                    results = []
                search_time = time.time() - start_time

                # Check if relevant documents were found
                relevant_found = sum(1 for r in results if test_case["topic"].lower() in r.page_content.lower())
                relevance_score = (relevant_found / min(3, len(test_case["documents"]))) * 100

                query_results.append({
                    "query": query,
                    "time": search_time,
                    "results_count": len(results),
                    "relevance_score": relevance_score
                })

                print(f"  Query: '{query}'")
                print(f"    Time: {search_time:.3f}s, Results: {len(results)}, Relevance: {relevance_score:.0f}%")

            accuracy_metrics.append({
                "topic": test_case["topic"],
                "queries": query_results,
                "avg_relevance": statistics.mean([q["relevance_score"] for q in query_results]),
                "avg_time": statistics.mean([q["time"] for q in query_results])
            })

        test_result["metrics"] = accuracy_metrics

        # Calculate overall accuracy
        overall_relevance = statistics.mean([m["avg_relevance"] for m in accuracy_metrics])
        test_result["efficiency_score"] = overall_relevance
        test_result["status"] = "passed" if overall_relevance > 70 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    # TEST 5: Concurrent Operations Stress Test
    async def test_concurrent_operations(self) -> Dict:
        """Test system performance under concurrent load"""
        print("\n" + "="*60)
        print("TEST 5: CONCURRENT OPERATIONS STRESS TEST")
        print("="*60)

        test_result = {
            "test_name": "concurrent_operations",
            "status": "running",
            "metrics": {}
        }

        concurrent_levels = [1, 5, 10, 20]
        stress_metrics = {}

        for concurrency in concurrent_levels:
            print(f"\nTesting with {concurrency} concurrent operations...")

            async def single_operation(op_id: int):
                """Single operation combining write and read"""
                # Generate and store document
                content = f"Concurrent test {op_id}: {self._generate_realistic_content(op_id)}"
                doc = Document(
                    page_content=content,
                    metadata={"op_id": op_id, "concurrency": concurrency}
                )

                start_time = time.time()

                # Store
                if self.qdrant_store:
                    await self.qdrant_store.aadd_documents([doc], [str(uuid.uuid4())])

                    # Search
                    await self.qdrant_store.asearch(f"test {op_id}", k=1)

                return time.time() - start_time

            # Run concurrent operations
            start_time = time.time()
            tasks = [single_operation(i) for i in range(concurrency)]
            operation_times = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            stress_metrics[concurrency] = {
                "total_time": total_time,
                "avg_operation_time": statistics.mean(operation_times),
                "max_operation_time": max(operation_times),
                "min_operation_time": min(operation_times),
                "operations_per_second": concurrency / total_time,
                "efficiency": (concurrency / total_time) / concurrency  # Should be close to 1 for perfect scaling
            }

            print(f"  Total: {total_time:.3f}s")
            print(f"  Avg per operation: {stress_metrics[concurrency]['avg_operation_time']:.3f}s")
            print(f"  Throughput: {stress_metrics[concurrency]['operations_per_second']:.1f} ops/sec")
            print(f"  Scaling efficiency: {stress_metrics[concurrency]['efficiency']:.2%}")

        test_result["metrics"] = stress_metrics

        # Calculate efficiency based on scaling
        scaling_scores = [m["efficiency"] * 100 for m in stress_metrics.values()]
        test_result["efficiency_score"] = statistics.mean(scaling_scores)
        test_result["status"] = "passed" if test_result["efficiency_score"] > 60 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    # TEST 6: Memory and Deduplication
    async def test_memory_deduplication(self) -> Dict:
        """Test memory efficiency and deduplication"""
        print("\n" + "="*60)
        print("TEST 6: MEMORY EFFICIENCY AND DEDUPLICATION")
        print("="*60)

        test_result = {
            "test_name": "memory_deduplication",
            "status": "running",
            "metrics": {}
        }

        # Create documents with duplicates
        unique_contents = [
            "Unique document about Python programming",
            "Unique document about Unity development",
            "Unique document about machine learning"
        ]

        documents = []
        # Add each unique document multiple times
        for content in unique_contents:
            for i in range(10):  # 10 copies of each
                doc = Document(
                    page_content=content,
                    metadata={
                        "copy_number": i,
                        "content_hash": hashlib.md5(content.encode()).hexdigest()[:8]
                    }
                )
                documents.append(doc)

        print(f"Testing with {len(documents)} documents ({len(unique_contents)} unique)")

        # Store documents
        start_time = time.time()
        ids = [str(uuid.uuid4()) for _ in documents]
        if self.qdrant_store:
            await self.qdrant_store.aadd_documents(documents, ids)
        storage_time = time.time() - start_time

        # Search for each unique content
        search_results = {}
        for content in unique_contents:
            query = content.split()[-2]  # Use a key word from each
            if self.qdrant_store:
                results = await self.qdrant_store.asearch(query, k=10)
                # Count how many duplicates were found
                unique_results = len(set([r.page_content for r in results]))
                search_results[query] = {
                    "total_found": len(results),
                    "unique_found": unique_results,
                    "duplicate_ratio": (len(results) - unique_results) / len(results) if results else 0
                }

        test_result["metrics"] = {
            "total_documents": len(documents),
            "unique_documents": len(unique_contents),
            "storage_time": storage_time,
            "search_results": search_results,
            "duplication_factor": len(documents) / len(unique_contents)
        }

        # Efficiency is based on how well the system handles duplicates
        # Good system should store efficiently but still find all copies
        avg_found = statistics.mean([r["total_found"] for r in search_results.values()]) if search_results else 0
        test_result["efficiency_score"] = min(100, (avg_found / 10) * 100)  # Should find all 10 copies
        test_result["status"] = "passed" if test_result["efficiency_score"] > 70 else "needs_optimization"

        self.test_results["tests"].append(test_result)
        return test_result

    def _generate_realistic_content(self, index: int) -> str:
        """Generate realistic document content for testing"""
        topics = [
            "Python programming best practices for error handling",
            "Unity game development performance optimization",
            "Machine learning model training techniques",
            "Docker containerization and deployment strategies",
            "JavaScript async/await patterns and promises",
            "Database query optimization and indexing",
            "Security best practices for API development",
            "React component lifecycle and state management"
        ]

        base_content = random.choice(topics)
        return f"{base_content}. Document index: {index}. Additional context for testing purposes."

    async def analyze_and_optimize(self):
        """Analyze test results and suggest optimizations"""
        print("\n" + "="*60)
        print("ANALYSIS AND OPTIMIZATION RECOMMENDATIONS")
        print("="*60)

        optimizations = []

        for test in self.test_results["tests"]:
            if test["status"] == "needs_optimization":
                optimization = {
                    "test": test["test_name"],
                    "current_score": test["efficiency_score"],
                    "recommendations": []
                }

                if test["test_name"] == "document_generation_efficiency":
                    if test["efficiency_score"] < 70:
                        optimization["recommendations"].extend([
                            "Use batch document generation instead of individual",
                            "Pre-compile templates for common document types",
                            "Implement document caching for frequently used patterns"
                        ])

                elif test["test_name"] == "embedding_generation_speed":
                    if test["efficiency_score"] < 70:
                        optimization["recommendations"].extend([
                            "Always use batch embedding instead of single",
                            "Consider using a smaller embedding model for non-critical uses",
                            "Implement embedding cache for duplicate content"
                        ])

                elif test["test_name"] == "storage_pipeline_throughput":
                    metrics = test["metrics"]
                    for batch_metrics in metrics.values():
                        if batch_metrics["embedding_percentage"] > 60:
                            optimization["recommendations"].append("Embedding is bottleneck - optimize model or use GPU")
                        if batch_metrics["storage_percentage"] > 60:
                            optimization["recommendations"].append("Storage is bottleneck - consider batch size optimization")

                elif test["test_name"] == "search_accuracy":
                    if test["efficiency_score"] < 70:
                        optimization["recommendations"].extend([
                            "Improve document metadata for better filtering",
                            "Adjust similarity threshold for better relevance",
                            "Consider hybrid search with keyword filters"
                        ])

                elif test["test_name"] == "concurrent_operations":
                    if test["efficiency_score"] < 60:
                        optimization["recommendations"].extend([
                            "Implement connection pooling for Qdrant",
                            "Use async batch operations where possible",
                            "Consider rate limiting to prevent overload"
                        ])

                optimizations.append(optimization)

        self.test_results["optimizations"] = optimizations

        # Print recommendations
        if optimizations:
            print("\nOptimization Recommendations:")
            for opt in optimizations:
                print(f"\n{opt['test']} (Score: {opt['current_score']:.1f}%):")
                for rec in opt["recommendations"]:
                    print(f"  - {rec}")
        else:
            print("\nAll tests passed! System is performing efficiently.")

        return optimizations

    async def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("WORKFLOW TEST REPORT")
        print("="*60)

        # Calculate overall system score
        all_scores = [test["efficiency_score"] for test in self.test_results["tests"]]
        overall_score = statistics.mean(all_scores) if all_scores else 0

        report = {
            "timestamp": self.test_results["timestamp"],
            "overall_efficiency": overall_score,
            "test_summary": {},
            "bottlenecks": [],
            "recommendations": self.test_results.get("optimizations", [])
        }

        print(f"\nOVERALL SYSTEM EFFICIENCY: {overall_score:.1f}%")
        print("\nTest Results Summary:")
        print("-" * 40)

        for test in self.test_results["tests"]:
            status_symbol = "✓" if test["status"] == "passed" else "✗"
            print(f"{status_symbol} {test['test_name']}: {test['efficiency_score']:.1f}%")

            report["test_summary"][test["test_name"]] = {
                "score": test["efficiency_score"],
                "status": test["status"]
            }

            # Identify bottlenecks
            if test["efficiency_score"] < 70:
                report["bottlenecks"].append({
                    "area": test["test_name"],
                    "score": test["efficiency_score"],
                    "impact": "high" if test["efficiency_score"] < 50 else "medium"
                })

        # Save detailed report
        report_file = f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {report_file}")

        # Performance grade
        if overall_score >= 90:
            grade = "A - Excellent"
        elif overall_score >= 80:
            grade = "B - Good"
        elif overall_score >= 70:
            grade = "C - Acceptable"
        elif overall_score >= 60:
            grade = "D - Needs Improvement"
        else:
            grade = "F - Critical Issues"

        print(f"\nPERFORMANCE GRADE: {grade}")

        return report


async def main():
    """Run complete workflow test sequence"""
    tester = WorkflowTester()

    print("="*60)
    print("KNOWLEDGE SYSTEM WORKFLOW & DATAFLOW TESTER")
    print("="*60)

    # Initialize
    await tester.setup()

    # Run all tests in sequence
    print("\nRunning test sequence...")
    print("-" * 60)

    # Test 1: Document Generation
    await tester.test_document_generation_efficiency()

    # Test 2: Embedding Speed
    await tester.test_embedding_generation_speed()

    # Test 3: Storage Pipeline
    await tester.test_storage_pipeline_throughput()

    # Test 4: Search Accuracy
    await tester.test_search_accuracy()

    # Test 5: Concurrent Operations
    await tester.test_concurrent_operations()

    # Test 6: Memory Deduplication
    await tester.test_memory_deduplication()

    # Analyze and optimize
    await tester.analyze_and_optimize()

    # Generate final report
    report = await tester.generate_report()

    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

    return report


if __name__ == "__main__":
    asyncio.run(main())