import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent))

from python.helpers.memory import Memory
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import matplotlib.pyplot as plt
import numpy as np

class AgentZeroTestSuite:
    """Comprehensive test suite for Agent Zero with Qdrant visualization"""
    
    def __init__(self):
        self.results = []
        self.test_start_time = datetime.now()
        self.qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
        self.test_collection = "agent-zero-test-results"
        
    async def setup_test_collection(self):
        """Create a dedicated collection for test results visualization"""
        try:
            await self.qdrant_client.delete_collection(self.test_collection)
        except:
            pass
            
        await self.qdrant_client.create_collection(
            collection_name=self.test_collection,
            vectors_config=VectorParams(size=3, distance=Distance.COSINE)
        )
        
    async def test_memory_recall(self) -> Dict[str, Any]:
        """Test 1: Memory Recall Accuracy"""
        print("\n🧪 Test 1: Memory Recall Accuracy")
        print("=" * 60)
        
        test_queries = [
            {
                "query": "Unity error handling",
                "expected_tags": ["unity", "error"],
                "expected_area": "main"
            },
            {
                "query": "Game Creator action pattern",
                "expected_tags": ["gamecreator", "action"],
                "expected_area": "solutions"
            },
            {
                "query": "ML-Agents integration",
                "expected_tags": ["ml-agents", "unity"],
                "expected_area": "main"
            },
            {
                "query": "Unity build configuration",
                "expected_tags": ["unity", "build"],
                "expected_area": "main"
            },
            {
                "query": "Project optimization strategies",
                "expected_tags": ["optimization", "performance"],
                "expected_area": "main"
            }
        ]
        
        results = []
        memory = await Memory.get_by_subdir("mlcreator")
        
        for i, test in enumerate(test_queries, 1):
            start_time = time.time()
            
            try:
                docs = await memory.search_similarity_threshold(
                    query=test["query"],
                    limit=5,
                    threshold=0.6
                )
                
                recall_time = time.time() - start_time
                
                # Check if expected tags are present
                found_tags = []
                found_areas = []
                for doc in docs:
                    if 'tags' in doc.metadata:
                        found_tags.extend(doc.metadata['tags'])
                    if 'area' in doc.metadata:
                        found_areas.append(doc.metadata['area'])
                
                tag_match = any(tag in found_tags for tag in test["expected_tags"])
                area_match = test["expected_area"] in found_areas
                
                result = {
                    "test_id": f"recall_{i}",
                    "query": test["query"],
                    "success": tag_match and len(docs) > 0,
                    "recall_time_ms": round(recall_time * 1000, 2),
                    "num_results": len(docs),
                    "tag_match": tag_match,
                    "area_match": area_match,
                    "found_tags": list(set(found_tags)),
                    "score": (1.0 if tag_match else 0.5) * (1.0 if area_match else 0.8)
                }
                
                results.append(result)
                
                status = "✅" if result["success"] else "⚠️"
                print(f"{status} Query {i}: '{test['query']}'")
                print(f"   Results: {result['num_results']} | Time: {result['recall_time_ms']}ms | Score: {result['score']:.2f}")
                
            except Exception as e:
                results.append({
                    "test_id": f"recall_{i}",
                    "query": test["query"],
                    "success": False,
                    "error": str(e),
                    "score": 0.0
                })
                print(f"❌ Query {i}: Failed - {e}")
        
        avg_score = sum(r["score"] for r in results) / len(results)
        avg_time = sum(r.get("recall_time_ms", 0) for r in results) / len(results)
        
        return {
            "test_name": "Memory Recall",
            "results": results,
            "avg_score": avg_score,
            "avg_time_ms": avg_time,
            "pass_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_server_side_filtering(self) -> Dict[str, Any]:
        """Test 2: Server-Side Filtering Performance"""
        print("\n🧪 Test 2: Server-Side Filtering Performance")
        print("=" * 60)
        
        memory = await Memory.get_by_subdir("mlcreator")
        
        filter_tests = [
            {"filter": "area == 'main'", "expected_min": 1},
            {"filter": "area == 'solutions'", "expected_min": 1},
            {"filter": "area == 'main' or area == 'solutions'", "expected_min": 2},
        ]
        
        results = []
        
        for i, test in enumerate(filter_tests, 1):
            start_time = time.time()
            
            try:
                docs = await memory.search_similarity_threshold(
                    query="project",
                    limit=10,
                    threshold=0.5,
                    filter=test["filter"]
                )
                
                filter_time = time.time() - start_time
                success = len(docs) >= test["expected_min"]
                
                result = {
                    "test_id": f"filter_{i}",
                    "filter": test["filter"],
                    "success": success,
                    "filter_time_ms": round(filter_time * 1000, 2),
                    "num_results": len(docs),
                    "score": 1.0 if success else 0.0
                }
                
                results.append(result)
                
                status = "✅" if success else "❌"
                print(f"{status} Filter {i}: {test['filter']}")
                print(f"   Results: {result['num_results']} | Time: {result['filter_time_ms']}ms")
                
            except Exception as e:
                results.append({
                    "test_id": f"filter_{i}",
                    "filter": test["filter"],
                    "success": False,
                    "error": str(e),
                    "score": 0.0
                })
                print(f"❌ Filter {i}: Failed - {e}")
        
        avg_score = sum(r["score"] for r in results) / len(results)
        avg_time = sum(r.get("filter_time_ms", 0) for r in results) / len(results)
        
        return {
            "test_name": "Server-Side Filtering",
            "results": results,
            "avg_score": avg_score,
            "avg_time_ms": avg_time,
            "pass_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_vector_quality(self) -> Dict[str, Any]:
        """Test 3: Vector Embedding Quality"""
        print("\n🧪 Test 3: Vector Embedding Quality")
        print("=" * 60)
        
        # Test semantic similarity
        similarity_pairs = [
            ("Unity game development", "Game Creator Unity integration", 0.7),
            ("Error handling", "Exception management", 0.6),
            ("Build configuration", "Compilation settings", 0.6),
            ("Random text", "Unity development", 0.3),  # Should be low
        ]
        
        memory = await Memory.get_by_subdir("mlcreator")
        results = []
        
        for i, (query1, query2, expected_min_sim) in enumerate(similarity_pairs, 1):
            try:
                # Search for both queries
                docs1 = await memory.search_similarity_threshold(query1, limit=3, threshold=0.5)
                docs2 = await memory.search_similarity_threshold(query2, limit=3, threshold=0.5)
                
                # Check if they return similar results
                overlap = len(set(d.metadata.get('id') for d in docs1) & 
                             set(d.metadata.get('id') for d in docs2))
                
                similarity_score = overlap / max(len(docs1), len(docs2), 1)
                success = similarity_score >= expected_min_sim if expected_min_sim > 0.5 else similarity_score < expected_min_sim
                
                result = {
                    "test_id": f"vector_{i}",
                    "query_pair": f"{query1} <-> {query2}",
                    "similarity_score": round(similarity_score, 2),
                    "expected_min": expected_min_sim,
                    "success": success,
                    "score": 1.0 if success else 0.5
                }
                
                results.append(result)
                
                status = "✅" if success else "⚠️"
                print(f"{status} Pair {i}: Similarity = {similarity_score:.2f} (expected >= {expected_min_sim})")
                
            except Exception as e:
                results.append({
                    "test_id": f"vector_{i}",
                    "success": False,
                    "error": str(e),
                    "score": 0.0
                })
                print(f"❌ Pair {i}: Failed - {e}")
        
        avg_score = sum(r["score"] for r in results) / len(results)
        
        return {
            "test_name": "Vector Quality",
            "results": results,
            "avg_score": avg_score,
            "pass_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_payload_indexing(self) -> Dict[str, Any]:
        """Test 4: Payload Index Performance"""
        print("\n🧪 Test 4: Payload Index Performance")
        print("=" * 60)
        
        # Get collection info
        try:
            collection_info = await self.qdrant_client.get_collection("agent-zero-mlcreator")
            
            # Check if indexes exist
            indexed_fields = []
            if hasattr(collection_info, 'payload_schema'):
                indexed_fields = list(collection_info.payload_schema.keys())
            
            expected_indexes = ["area", "tags", "project"]
            found_indexes = [field for field in expected_indexes if field in indexed_fields]
            
            result = {
                "test_name": "Payload Indexing",
                "indexed_fields": indexed_fields,
                "expected_indexes": expected_indexes,
                "found_indexes": found_indexes,
                "success": len(found_indexes) >= 1,  # At least one index
                "score": len(found_indexes) / len(expected_indexes)
            }
            
            status = "✅" if result["success"] else "⚠️"
            print(f"{status} Indexed fields: {indexed_fields}")
            print(f"   Expected: {expected_indexes}")
            print(f"   Score: {result['score']:.2f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to check indexes: {e}")
            return {
                "test_name": "Payload Indexing",
                "success": False,
                "error": str(e),
                "score": 0.0
            }
    
    async def visualize_results_in_qdrant(self, all_results: List[Dict]):
        """Store test results as vectors in Qdrant for visualization"""
        print("\n📊 Storing results in Qdrant for visualization...")
        
        points = []
        
        for i, test_result in enumerate(all_results):
            # Create a 3D vector: [avg_score, pass_rate, avg_time_normalized]
            avg_time = test_result.get("avg_time_ms", 0)
            vector = [
                test_result.get("avg_score", 0),
                test_result.get("pass_rate", 0),
                min(avg_time / 1000, 1.0)  # Normalize time to 0-1
            ]
            
            point = PointStruct(
                id=i,
                vector=vector,
                payload={
                    "test_name": test_result["test_name"],
                    "avg_score": test_result.get("avg_score", 0),
                    "pass_rate": test_result.get("pass_rate", 0),
                    "avg_time_ms": test_result.get("avg_time_ms", 0),
                    "timestamp": datetime.now().isoformat(),
                    "status": "✅ PASS" if test_result.get("avg_score", 0) >= 0.7 else "⚠️ WARNING",
                    "details": json.dumps(test_result.get("results", [])[:3])  # Store first 3 results
                }
            )
            points.append(point)
        
        await self.qdrant_client.upsert(
            collection_name=self.test_collection,
            points=points
        )
        
        print(f"✅ Stored {len(points)} test results in Qdrant")
        print(f"   View at: http://localhost:6333/dashboard#/collections/{self.test_collection}")
    
    def generate_report(self, all_results: List[Dict]):
        """Generate a comprehensive test report"""
        report_path = Path("test_results") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        overall_score = sum(r.get("avg_score", 0) for r in all_results) / len(all_results)
        overall_pass_rate = sum(r.get("pass_rate", 0) for r in all_results) / len(all_results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 2),
            "overall_pass_rate": round(overall_pass_rate, 2),
            "test_results": all_results,
            "summary": {
                "total_tests": len(all_results),
                "passed": sum(1 for r in all_results if r.get("avg_score", 0) >= 0.7),
                "warnings": sum(1 for r in all_results if 0.5 <= r.get("avg_score", 0) < 0.7),
                "failed": sum(1 for r in all_results if r.get("avg_score", 0) < 0.5)
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        return report
    
    async def run_all_tests(self):
        """Run all tests and generate visualizations"""
        print("🚀 Starting Agent Zero Test Suite")
        print("=" * 60)
        
        await self.setup_test_collection()
        
        # Run all tests
        test_results = []
        
        test_results.append(await self.test_memory_recall())
        test_results.append(await self.test_server_side_filtering())
        test_results.append(await self.test_vector_quality())
        test_results.append(await self.test_payload_indexing())
        
        # Visualize in Qdrant
        await self.visualize_results_in_qdrant(test_results)
        
        # Generate report
        report = self.generate_report(test_results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Score: {report['overall_score']:.2f}/1.00")
        print(f"Overall Pass Rate: {report['overall_pass_rate']:.1%}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Warnings: {report['summary']['warnings']}")
        print(f"Failed: {report['summary']['failed']}")
        print("\n🎯 View detailed visualizations at:")
        print(f"   http://localhost:6333/dashboard#/collections/{self.test_collection}")
        print("=" * 60)
        
        return report

if __name__ == "__main__":
    suite = AgentZeroTestSuite()
    asyncio.run(suite.run_all_tests())
