import asyncio
from typing import Dict, List, Optional
from python.unity_memory.data_models import UnityMemoryEntry
from langchain_core.documents import Document
import numpy as np

class UnityMemoryOptimizer:
    """Optimize Unity-specific memory operations."""
    
    def __init__(self, qdrant_store, embedder):
        self.store = qdrant_store
        self.embedder = embedder
        self.cache = {}
    
    async def batch_upsert_unity_memories(
        self, 
        entries: List[UnityMemoryEntry],
        batch_size: int = 50
    ):
        """Batch insert Unity memories for better performance."""
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i+batch_size]
            documents = [
                Document(
                    page_content=entry.content,
                    metadata={
                        "entity_type": entry.entity_type,
                        "entity_name": entry.entity_name,
                        "project_id": entry.project_id,
                        "file_path": entry.file_path,
                        "tags": entry.tags,
                        "area": "unity",
                        "last_updated": entry.last_updated.isoformat() if entry.last_updated else None
                    }
                )
                for entry in batch
            ]
            ids = [entry.id for entry in batch]
            await self.store.aadd_documents(documents, ids)
            
    def get_cached_embedding(self, key: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        return self.cache.get(key)
    
    def cache_embedding(self, key: str, embedding: List[float]):
        """Cache an embedding for reuse."""
        # Limit cache size to 1000 entries
        if len(self.cache) > 1000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.cache.keys())[:100]
            for k in keys_to_remove:
                del self.cache[k]
        self.cache[key] = embedding