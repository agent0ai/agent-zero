import asyncio
from qdrant_client import AsyncQdrantClient

async def reset_qdrant():
    print("🗑️ Clearing Qdrant collections...")
    client = AsyncQdrantClient(url="http://localhost:6333")
    
    collections = ["agent-zero-mlcreator", "agent-zero-default"]
    
    for name in collections:
        try:
            await client.delete_collection(name)
            print(f"✅ Deleted collection: {name}")
        except Exception as e:
            print(f"⚠️ Could not delete {name}: {e}")

if __name__ == "__main__":
    asyncio.run(reset_qdrant())
