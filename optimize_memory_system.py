import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from python.helpers.qdrant_client import QdrantStore
from python.helpers.memory_config import get_memory_config
import models

async def optimize_qdrant_collection():
    """Pre-optimize Qdrant collection for Unity/MLcreator data."""
    
    print("=== Memory System Optimizer ===")
    print("Optimizing Qdrant collection for Unity/MLcreator...")
    
    try:
        # Get memory configuration
        config = get_memory_config()
        
        # Initialize embeddings model
        embeddings_model = models.get_embedding_model()
        
        # Create optimized Qdrant store with enhanced payload keys
        store = QdrantStore(
            embedder=embeddings_model,
            collection="agent-zero",
            url=config.get("qdrant", {}).get("url", "http://localhost:6333"),
            api_key=config.get("qdrant", {}).get("api_key", ""),
            prefer_hybrid=True,
            score_threshold=0.55,  # Optimized threshold
            limit=30,  # Increased limit
            timeout=15,  # Increased timeout
            searchable_payload_keys=[
                "area", 
                "entity_type", 
                "scene_name", 
                "project_id", 
                "tags", 
                "consolidation_action",
                "source",
                "entity_name",
                "file_path"
            ]
        )
        
        # Ensure collection has proper configuration
        await store._ensure_collection()
        
        print("✓ Qdrant collection optimized")
        print(f"  - Collection: agent-zero")
        print(f"  - URL: {config.get('qdrant', {}).get('url')}")
        print(f"  - Score threshold: 0.55 (optimized)")
        print(f"  - Result limit: 30 (increased)")
        print(f"  - Timeout: 15s (increased)")
        print(f"  - Indexed fields: 9 payload keys")
        
        return True
        
    except Exception as e:
        print(f"✗ Optimization failed: {str(e)}")
        return False

async def verify_qdrant_connection():
    """Verify Qdrant is running and accessible."""
    print("\nVerifying Qdrant connection...")
    
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url="http://localhost:6333", timeout=5)
        
        # Try to list collections
        collections = await client.get_collections()
        print(f"✓ Connected to Qdrant (found {len(collections.collections)} collections)")
        
        # Check if agent-zero collection exists
        collection_names = [c.name for c in collections.collections]
        if "agent-zero" in collection_names:
            collection_info = await client.get_collection("agent-zero")
            print(f"  - Collection 'agent-zero' exists with {collection_info.points_count} points")
        else:
            print("  - Collection 'agent-zero' will be created")
        
        return True
        
    except Exception as e:
        print(f"✗ Cannot connect to Qdrant: {str(e)}")
        print("  Please ensure Qdrant is running on http://localhost:6333")
        print("  Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant")
        return False

async def main():
    """Main optimization routine."""
    print("\n" + "="*50)
    print("Agent Zero Memory System Optimizer")
    print("="*50 + "\n")
    
    # Verify Qdrant connection first
    if not await verify_qdrant_connection():
        print("\n✗ Optimization aborted - Qdrant not available")
        return False
    
    # Run optimization
    success = await optimize_qdrant_collection()
    
    if success:
        print("\n✓ Memory system optimization complete!")
        print("\nNext steps:")
        print("  1. Restart agent-zero to apply changes")
        print("  2. Monitor memory performance in logs")
        print("  3. Adjust thresholds if needed")
    else:
        print("\n✗ Optimization failed - check errors above")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)