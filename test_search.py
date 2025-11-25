#!/usr/bin/env python3
"""
Test semantic search on Unity Knowledge Base
"""

import requests
import json
from sentence_transformers import SentenceTransformer

QDRANT_URL = "http://qdrant-unity:6333"
COLLECTION_NAME = "unity_project_kb"

def test_search(query: str, filters: dict = None):
    """Test hybrid search with optional filters"""
    
    print(f"\n🔍 Query: \"{query}\"")
    if filters:
        print(f"   Filters: {filters}")
    
    # Load model for query embedding
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()
    
    # Build search payload
    search_payload = {
        "vector": {
            "name": "text-dense",
            "vector": query_vector
        },
        "limit": 5,
        "with_payload": True
    }
    
    if filters:
        search_payload["filter"] = filters
    
    # Execute search
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
        json=search_payload
    )
    
    results = response.json()["result"]
    
    print(f"\n   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        payload = result["payload"]
        score = result["score"]
        print(f"\n   [{i}] Score: {score:.4f}")
        print(f"       File: {payload['file_path']}")
        print(f"       Class: {payload['class_name']}")
        print(f"       Assembly: {payload['assembly_name']}")
        print(f"       Type: {payload['code_type']}")
        print(f"       Preview: {payload['content'][:150]}...")

def main():
    print("=" * 60)
    print("🧪 UNITY KNOWLEDGE BASE - SEARCH TESTS")
    print("=" * 60)
    
    # Test 1: Semantic search
    test_search("player movement and controls")
    
    # Test 2: Editor-specific search
    test_search(
        "custom editor tools",
        filters={"must": [{"key": "code_type", "match": {"value": "editor"}}]}
    )
    
    # Test 3: Assembly-scoped search
    test_search(
        "game state management",
        filters={"must": [{"key": "assembly_name", "match": {"value": "GameCreator.Runtime.Core"}}]}
    )
    
    print("\n" + "=" * 60)
    print("✅ SEARCH TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
