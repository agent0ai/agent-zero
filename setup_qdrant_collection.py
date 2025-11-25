#!/usr/bin/env python3
"""
Qdrant Collection Setup for Unity Knowledge Base
Creates collection with Hybrid Search configuration
"""

import requests
import json

QDRANT_URL = "http://qdrant-unity:6333"
COLLECTION_NAME = "unity_project_kb"

def create_collection():
    """Create Qdrant collection with hybrid search support"""
    
    print("=" * 60)
    print("🔧 QDRANT COLLECTION SETUP")
    print("=" * 60)
    
    # Check if collection exists
    print(f"\n1. Checking existing collections...")
    response = requests.get(f"{QDRANT_URL}/collections")
    collections = response.json()["result"]["collections"]
    
    existing = [c["name"] for c in collections]
    if COLLECTION_NAME in existing:
        print(f"   ⚠️  Collection '{COLLECTION_NAME}' already exists")
        choice = input("   Delete and recreate? (y/n): ")
        if choice.lower() == 'y':
            print(f"   🗑️  Deleting existing collection...")
            requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            print("   ✅ Deleted")
        else:
            print("   ℹ️  Using existing collection")
            return
    
    print(f"\n2. Creating collection '{COLLECTION_NAME}'...")
    
    # Collection configuration following research specs
    config = {
        "vectors": {
            "text-dense": {
                "size": 384,  # all-MiniLM-L6-v2 dimension
                "distance": "Cosine"
            }
        },
        "sparse_vectors": {
            "text-sparse": {
                "index": {
                    "on_disk": False  # RAM-based for speed
                }
            }
        },
        "optimizers_config": {
            "indexing_threshold": 20000
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        }
    }
    
    response = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
        json=config
    )
    
    if response.status_code == 200:
        print("   ✅ Collection created successfully")
    else:
        print(f"   ❌ Error: {response.text}")
        return
    
    print(f"\n3. Creating payload indexes...")
    
    # Create indexes for filtering (per research recommendations)
    indexes = [
        ("asset_guid", "keyword"),
        ("assembly_name", "keyword"),
        ("code_type", "keyword"),
        ("class_name", "keyword")
    ]
    
    for field_name, field_type in indexes:
        payload = {
            "field_name": field_name,
            "field_schema": field_type
        }
        response = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index",
            json=payload
        )
        if response.status_code == 200:
            print(f"   ✅ Index created: {field_name} ({field_type})")
        else:
            print(f"   ⚠️  Failed to create index for {field_name}")
    
    print("\n" + "=" * 60)
    print("✅ QDRANT COLLECTION READY")
    print("=" * 60)
    
    # Show collection info
    response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
    info = response.json()["result"]
    print(f"\nCollection: {COLLECTION_NAME}")
    print(f"Status: {info['status']}")
    print(f"Vectors: {info['config']['params']['vectors']}")
    print(f"Points: {info.get('points_count', 0)}")

if __name__ == "__main__":
    try:
        create_collection()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  - Qdrant is running at http://qdrant-unity:6333")
        print("  - You're running this inside the agent-zero-unity container")
