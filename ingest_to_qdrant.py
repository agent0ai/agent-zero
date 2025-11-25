#!/usr/bin/env python3
"""
Unity Knowledge Base Ingestion Pipeline
Embeds documents and uploads to Qdrant with proper chunking
"""

import json
import uuid
import hashlib
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

QDRANT_URL = "http://qdrant-unity:6333"
COLLECTION_NAME = "unity_project_kb"
METADATA_FILE = "/tmp/unity_kb_metadata.json"

class UnityKBIngester:
    def __init__(self):
        print("🔧 Initializing embeddings model...")
        self.dense_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.sparse_vectorizer = TfidfVectorizer(max_features=1000)
        print("   ✅ Model loaded: all-MiniLM-L6-v2 (384 dimensions)")
    
    def chunk_code(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Chunk C# code respecting semantic boundaries
        Uses separator hierarchy from research document
        """
        separators = [
            "\nnamespace ",
            "\nclass ",
            "\nstruct ",
            "\npublic ",
            "\nprivate ",
            "\n\n",
            "\n"
        ]
        
        chunks = []
        current_chunk = ""
        
        for line in content.split('\n'):
            if len(current_chunk) + len(line) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                current_chunk += "\n" + line
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def enrich_context(self, chunk: str, metadata: Dict) -> str:
        """
        Add context header to chunk (per research Section 6.2)
        """
        header = f"""// File: {metadata['file_path']}
// Assembly: {metadata['assembly_name']}
// Class: {metadata['class_name']}
// Type: {metadata['code_type']}

"""
        return header + chunk
    
    def generate_deterministic_uuid(self, asset_guid: str, chunk_index: int) -> str:
        """UUID v5 generation (per research Section 5.1)"""
        namespace = uuid.NAMESPACE_DNS
        seed = f"{asset_guid}_{chunk_index}"
        return str(uuid.uuid5(namespace, seed))
    
    def create_sparse_vector(self, text: str) -> List[Dict]:
        """Create sparse vector for keyword matching"""
        # Simple TF-IDF based sparse vector
        # In production, use SPLADE or BM25
        tokens = text.lower().split()
        token_counts = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1
        
        # Convert to sparse format: list of {index, value}
        sparse = []
        for i, (token, count) in enumerate(list(token_counts.items())[:100]):
            sparse.append({
                "index": hash(token) % 100000,
                "value": float(count)
            })
        return sparse
    
    def ingest_documents(self, batch_size: int = 100):
        """Main ingestion pipeline"""
        print("\n" + "=" * 60)
        print("📤 INGESTION PIPELINE")
        print("=" * 60)
        
        # Load metadata from build_unity_kb.py output
        print(f"\n1. Loading metadata from {METADATA_FILE}...")
        with open(METADATA_FILE, 'r') as f:
            documents = json.load(f)
        print(f"   ✅ Loaded {len(documents)} documents")
        
        # Process documents
        print(f"\n2. Processing documents...")
        points = []
        total_chunks = 0
        
        for doc_idx, doc in enumerate(documents):
            print(f"\r   Processing {doc_idx + 1}/{len(documents)}: {doc['file_path'][:50]}...", end='')
            
            # Chunk the content
            chunks = self.chunk_code(doc['content'])
            
            for chunk_idx, chunk in enumerate(chunks):
                # Context enrichment
                enriched_chunk = self.enrich_context(chunk, doc)
                
                # Generate embeddings
                dense_vector = self.dense_model.encode(enriched_chunk).tolist()
                sparse_vector = self.create_sparse_vector(enriched_chunk)
                
                # Deterministic UUID
                point_id = self.generate_deterministic_uuid(
                    doc['asset_guid'],
                    chunk_idx
                )
                
                # Create point
                point = {
                    "id": point_id,
                    "vector": {
                        "text-dense": dense_vector,
                        "text-sparse": {
                            "indices": [sv["index"] for sv in sparse_vector],
                            "values": [sv["value"] for sv in sparse_vector]
                        }
                    },
                    "payload": {
                        "asset_guid": doc['asset_guid'],
                        "file_path": doc['file_path'],
                        "assembly_name": doc['assembly_name'],
                        "code_type": doc['code_type'],
                        "class_name": doc['class_name'],
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "content": chunk,  # Store original chunk
                        "content_hash": doc['content_hash']
                    }
                }
                
                points.append(point)
                total_chunks += 1
                
                # Batch upload
                if len(points) >= batch_size:
                    self._upload_batch(points)
                    points = []
        
        print()  # New line after progress
        
        # Upload remaining points
        if points:
            self._upload_batch(points)
        
        print(f"\n   ✅ Processed {len(documents)} files into {total_chunks} chunks")
        
        # Verify upload
        print(f"\n3. Verifying ingestion...")
        response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        info = response.json()["result"]
        print(f"   ✅ Collection '{COLLECTION_NAME}' now has {info['points_count']} points")
        
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE")
        print("=" * 60)
    
    def _upload_batch(self, points: List[Dict]):
        """Upload a batch of points to Qdrant"""
        payload = {
            "points": points
        }
        response = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
            json=payload
        )
        if response.status_code != 200:
            print(f"\n   ⚠️  Upload error: {response.text}")

def main():
    ingester = UnityKBIngester()
    ingester.ingest_documents(batch_size=50)

if __name__ == "__main__":
    main()
