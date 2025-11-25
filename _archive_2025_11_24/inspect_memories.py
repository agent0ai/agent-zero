import asyncio
from qdrant_client import AsyncQdrantClient
from datetime import datetime
import json

async def inspect_memories():
    print("🔍 Inspecting Qdrant Memories...")
    client = AsyncQdrantClient(url="http://localhost:6333")
    
    # 1. List Collections
    try:
        collections = await client.get_collections()
        print(f"\n📚 Collections found: {[c.name for c in collections.collections]}")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return

    target_collection = "agent-zero-mlcreator"
    
    # 2. Get Collection Info
    try:
        info = await client.get_collection(target_collection)
        print(f"\n📊 Collection: {target_collection}")
        print(f"   • Points count: {info.points_count}")
        print(f"   • Vector size: {info.config.params.vectors.size}")
        print(f"   • Status: {info.status}")
    except Exception as e:
        print(f"⚠️ Collection '{target_collection}' not found or error: {e}")
        return

    # 3. Fetch Recent Memories (Scroll)
    print(f"\n📝 Latest 5 Memories in '{target_collection}':")
    print("=" * 60)
    
    try:
        # Scroll to get points
        points, _ = await client.scroll(
            collection_name=target_collection,
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        if not points:
            print("   (No memories found)")
        
        for i, point in enumerate(points, 1):
            payload = point.payload
            text = payload.get("text", "N/A")
            meta = {k:v for k,v in payload.items() if k != "text" and k != "id"}
            
            print(f"\n🔹 Memory #{i} (ID: {point.id})")
            print(f"   📂 Metadata: {json.dumps(meta, indent=2)}")
            print(f"   📄 Content: {text[:200]}..." if len(text) > 200 else f"   📄 Content: {text}")
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Failed to fetch points: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_memories())
