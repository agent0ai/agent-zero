"""
Enhanced Qdrant Client for Unity Project Management.

This module provides a powerful, Unity-optimized vector database layer with:
- Multi-collection management (scenes, scripts, assets, tasks, etc.)
- Hybrid search (dense + sparse vectors)
- Relationship/graph queries
- Batch operations with caching
- Real-time project state tracking
"""

import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import os
from functools import lru_cache

from langchain_core.documents import Document

try:
    from qdrant_client import AsyncQdrantClient, models as qmodels
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, Filter, FieldCondition,
        MatchValue, MatchAny, Range, PayloadSchemaType, SparseVector,
        NamedSparseVector, SparseIndexParams, SparseVectorParams,
        OptimizersConfigDiff, HnswConfigDiff
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    AsyncQdrantClient = None
    qmodels = None


class UnityCollectionType(Enum):
    """Unity-specific collection types for organized memory."""
    SCENES = "scenes"
    SCRIPTS = "scripts"
    ASSETS = "assets"
    PREFABS = "prefabs"
    GAMEOBJECTS = "gameobjects"
    COMPONENTS = "components"
    TASKS = "tasks"
    SOLUTIONS = "solutions"
    ERRORS = "errors"
    BUILD_LOGS = "build_logs"
    DOCUMENTATION = "documentation"
    CONVERSATIONS = "conversations"
    PROJECT_STATE = "project_state"
    DEPENDENCIES = "dependencies"
    RELATIONSHIPS = "relationships"


@dataclass
class UnitySearchResult:
    """Enhanced search result with context and relationships."""
    document: Document
    score: float
    collection: str
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    context_chain: List[Document] = field(default_factory=list)


@dataclass
class UnityQueryContext:
    """Context for intelligent Unity queries."""
    project_id: str
    active_scene: Optional[str] = None
    recent_scripts: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    error_context: Optional[str] = None
    build_target: Optional[str] = None
    unity_version: Optional[str] = None


@dataclass
class EmbeddingCache:
    """Cache for embeddings to reduce API calls."""
    max_size: int = 5000
    _cache: Dict[str, List[float]] = field(default_factory=dict)
    _access_order: List[str] = field(default_factory=list)

    def get(self, text: str) -> Optional[List[float]]:
        key = hashlib.md5(text.encode()).hexdigest()
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, text: str, embedding: List[float]):
        key = hashlib.md5(text.encode()).hexdigest()
        if len(self._cache) >= self.max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
        self._cache[key] = embedding
        self._access_order.append(key)


class UnityQdrantEnhanced:
    """
    Enhanced Qdrant client optimized for Unity project management.

    Features:
    - Multi-collection architecture for different entity types
    - Hybrid search with dense + sparse vectors
    - Relationship graph queries
    - Batch operations with intelligent caching
    - Real-time project state tracking
    - Context-aware retrieval with multi-hop reasoning
    """

    is_qdrant = True

    # Unity-specific payload indexes for fast filtering
    UNITY_PAYLOAD_INDEXES = [
        "entity_type", "entity_name", "scene_name", "script_name",
        "asset_type", "file_path", "project_id", "unity_version",
        "namespace", "class_name", "method_name", "component_type",
        "tag", "layer", "prefab_name", "material_name", "guid",
        "status", "priority", "error_type", "build_target",
        "source_entity", "target_entity", "relationship_type",
        "created_at", "updated_at", "area", "source", "tags"
    ]

    # Optimized HNSW config for different collection sizes
    HNSW_CONFIGS = {
        "small": HnswConfigDiff(m=16, ef_construct=100),      # < 10k docs
        "medium": HnswConfigDiff(m=32, ef_construct=200),     # 10k-100k docs
        "large": HnswConfigDiff(m=48, ef_construct=400),      # > 100k docs
    }

    def __init__(
        self,
        embedder,
        base_collection: str = "agent-zero-unity",
        url: str = "http://localhost:6333",
        api_key: str = "",
        prefer_hybrid: bool = True,
        score_threshold: float = 0.55,
        limit: int = 30,
        timeout: int = 15,
        enable_sparse: bool = True,
        cache_embeddings: bool = True,
        batch_size: int = 100,
    ):
        if not QDRANT_AVAILABLE:
            raise RuntimeError(
                "qdrant-client is not installed. Install with: pip install qdrant-client"
            )

        self.embedder = embedder
        self.client = AsyncQdrantClient(url=url, api_key=api_key or None, timeout=timeout)
        self.base_collection = base_collection
        self.prefer_hybrid = prefer_hybrid
        self.score_threshold = score_threshold
        self.limit = limit
        self.enable_sparse = enable_sparse
        self.batch_size = batch_size

        # Caching
        self.embedding_cache = EmbeddingCache() if cache_embeddings else None
        self._collection_cache: Dict[str, bool] = {}
        self._dimension: Optional[int] = None

        # Project state tracking
        self._project_states: Dict[str, Dict[str, Any]] = {}

    def _get_collection_name(self, collection_type: UnityCollectionType) -> str:
        """Generate collection name for a specific Unity entity type."""
        return f"{self.base_collection}-{collection_type.value}"

    def _to_uuid(self, id_str: str) -> str:
        """Convert any string ID to a deterministic UUID."""
        try:
            uuid.UUID(str(id_str))
            return str(id_str)
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_str)))

    async def _get_dimension(self) -> int:
        """Get embedding dimension, cached for performance."""
        if self._dimension is None:
            embedding = await self._embed_text("dimension check")
            self._dimension = len(embedding)
        return self._dimension

    async def _embed_text(self, text: str) -> List[float]:
        """Embed text with caching."""
        if self.embedding_cache:
            cached = self.embedding_cache.get(text)
            if cached:
                return cached

        embedding = await asyncio.to_thread(self.embedder.embed_query, text)

        if self.embedding_cache:
            self.embedding_cache.set(text, embedding)

        return embedding

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts with caching."""
        results = []
        uncached_indices = []
        uncached_texts = []

        # Check cache first
        for i, text in enumerate(texts):
            if self.embedding_cache:
                cached = self.embedding_cache.get(text)
                if cached:
                    results.append((i, cached))
                    continue
            uncached_indices.append(i)
            uncached_texts.append(text)

        # Embed uncached texts in batch
        if uncached_texts:
            embeddings = await asyncio.to_thread(
                self.embedder.embed_documents, uncached_texts
            )
            for idx, emb, text in zip(uncached_indices, embeddings, uncached_texts):
                results.append((idx, emb))
                if self.embedding_cache:
                    self.embedding_cache.set(text, emb)

        # Sort by original index and return
        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]

    def _generate_sparse_vector(self, text: str) -> Dict[int, float]:
        """Generate sparse vector from text using BM25-style tokenization."""
        # Simple BM25-style sparse vector generation
        tokens = text.lower().split()
        token_counts: Dict[str, int] = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        # Convert to sparse vector format
        sparse = {}
        for token, count in token_counts.items():
            # Use hash of token as index
            idx = hash(token) % 100000  # Limit to 100k dimensions
            sparse[idx] = float(count)

        return sparse

    async def _ensure_collection(
        self,
        collection_type: UnityCollectionType,
        size_hint: str = "medium"
    ) -> str:
        """Ensure collection exists with optimized configuration."""
        collection_name = self._get_collection_name(collection_type)

        if collection_name in self._collection_cache:
            return collection_name

        dim = await self._get_dimension()

        try:
            await self.client.get_collection(collection_name)
        except Exception:
            # Create collection with optimized settings
            vectors_config = {
                "dense": VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                    hnsw_config=self.HNSW_CONFIGS.get(size_hint, self.HNSW_CONFIGS["medium"])
                )
            }

            # Add sparse vectors for hybrid search
            sparse_vectors_config = None
            if self.enable_sparse:
                sparse_vectors_config = {
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=False)
                    )
                }

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                optimizers_config=OptimizersConfigDiff(
                    indexing_threshold=20000,
                    memmap_threshold=50000,
                )
            )

            # Create payload indexes
            for key in self.UNITY_PAYLOAD_INDEXES:
                try:
                    await self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=key,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass  # Index might already exist

        self._collection_cache[collection_name] = True
        return collection_name

    async def ensure_all_unity_collections(self):
        """Pre-create all Unity collections for optimal startup."""
        tasks = [
            self._ensure_collection(ct)
            for ct in UnityCollectionType
        ]
        await asyncio.gather(*tasks)

    # ==================== UNITY-SPECIFIC OPERATIONS ====================

    async def store_scene(
        self,
        scene_name: str,
        scene_path: str,
        content: str,
        game_objects: List[Dict[str, Any]],
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store Unity scene with full hierarchy."""
        collection = await self._ensure_collection(UnityCollectionType.SCENES)

        doc_id = self._to_uuid(f"scene:{project_id}:{scene_path}")
        embedding = await self._embed_text(content)

        payload = {
            "text": content,
            "entity_type": "scene",
            "entity_name": scene_name,
            "scene_name": scene_name,
            "file_path": scene_path,
            "project_id": project_id,
            "game_object_count": len(game_objects),
            "root_objects": [go["name"] for go in game_objects if not go.get("parent")],
            "area": "main",
            "timestamp": datetime.now().isoformat(),
            "original_id": doc_id,
            **(metadata or {})
        }

        vectors = {"dense": embedding}
        if self.enable_sparse:
            sparse = self._generate_sparse_vector(content)
            vectors["sparse"] = SparseVector(
                indices=list(sparse.keys()),
                values=list(sparse.values())
            )

        await self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload)]
        )

        # Store individual GameObjects
        await self._store_gameobjects_batch(game_objects, scene_name, project_id)

        return doc_id

    async def _store_gameobjects_batch(
        self,
        game_objects: List[Dict[str, Any]],
        scene_name: str,
        project_id: str
    ):
        """Batch store GameObjects from a scene."""
        collection = await self._ensure_collection(UnityCollectionType.GAMEOBJECTS)

        points = []
        texts = []

        for go in game_objects:
            content = self._gameobject_to_text(go)
            texts.append(content)

        embeddings = await self._embed_texts(texts)

        for go, content, embedding in zip(game_objects, texts, embeddings):
            doc_id = self._to_uuid(f"go:{project_id}:{scene_name}:{go['name']}")

            payload = {
                "text": content,
                "entity_type": "gameobject",
                "entity_name": go["name"],
                "scene_name": scene_name,
                "project_id": project_id,
                "tag": go.get("tag", "Untagged"),
                "layer": go.get("layer", 0),
                "components": [c.get("type", "") for c in go.get("components", [])],
                "parent": go.get("parent"),
                "children": go.get("children", []),
                "area": "main",
                "timestamp": datetime.now().isoformat(),
                "original_id": doc_id,
            }

            vectors = {"dense": embedding}
            if self.enable_sparse:
                sparse = self._generate_sparse_vector(content)
                vectors["sparse"] = SparseVector(
                    indices=list(sparse.keys()),
                    values=list(sparse.values())
                )

            points.append(PointStruct(id=doc_id, vector=vectors, payload=payload))

        # Batch upsert
        for i in range(0, len(points), self.batch_size):
            batch = points[i:i + self.batch_size]
            await self.client.upsert(collection_name=collection, points=batch)

    def _gameobject_to_text(self, go: Dict[str, Any]) -> str:
        """Convert GameObject to searchable text representation."""
        parts = [
            f"GameObject: {go['name']}",
            f"Tag: {go.get('tag', 'Untagged')}",
            f"Layer: {go.get('layer', 0)}",
        ]

        if go.get("components"):
            parts.append("Components: " + ", ".join(
                c.get("type", "Unknown") for c in go["components"]
            ))

        if go.get("children"):
            parts.append(f"Children: {', '.join(go['children'])}")

        return "\n".join(parts)

    async def store_script(
        self,
        file_path: str,
        content: str,
        classes: List[Dict[str, Any]],
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store C# script with class analysis."""
        collection = await self._ensure_collection(UnityCollectionType.SCRIPTS)

        doc_id = self._to_uuid(f"script:{project_id}:{file_path}")

        # Create rich text representation
        text = self._script_to_text(file_path, classes, content)
        embedding = await self._embed_text(text)

        # Extract class names and methods
        class_names = [c["name"] for c in classes]
        methods = []
        for c in classes:
            methods.extend([m["name"] for m in c.get("methods", [])])

        payload = {
            "text": text,
            "entity_type": "script",
            "entity_name": os.path.basename(file_path),
            "file_path": file_path,
            "project_id": project_id,
            "namespace": classes[0].get("namespace") if classes else None,
            "class_names": class_names,
            "methods": methods,
            "base_classes": [c.get("base_class") for c in classes if c.get("base_class")],
            "is_monobehaviour": any(
                "MonoBehaviour" in (c.get("base_classes") or []) for c in classes
            ),
            "unity_callbacks": self._extract_unity_callbacks(classes),
            "area": "main",
            "timestamp": datetime.now().isoformat(),
            "original_id": doc_id,
            **(metadata or {})
        }

        vectors = {"dense": embedding}
        if self.enable_sparse:
            sparse = self._generate_sparse_vector(text)
            vectors["sparse"] = SparseVector(
                indices=list(sparse.keys()),
                values=list(sparse.values())
            )

        await self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload)]
        )

        return doc_id

    def _script_to_text(
        self,
        file_path: str,
        classes: List[Dict[str, Any]],
        source_code: str
    ) -> str:
        """Convert script to searchable text representation."""
        parts = [f"C# Script: {os.path.basename(file_path)}"]

        for cls in classes:
            parts.append(f"\nClass: {cls['name']}")
            if cls.get("base_classes"):
                parts.append(f"  Inherits: {', '.join(cls['base_classes'])}")
            if cls.get("attributes"):
                parts.append(f"  Attributes: {', '.join(cls['attributes'])}")

            if cls.get("fields"):
                parts.append("  Fields:")
                for field in cls["fields"]:
                    parts.append(f"    - {field['name']}: {field['type']}")

            if cls.get("methods"):
                parts.append("  Methods:")
                for method in cls["methods"]:
                    params = ", ".join(
                        f"{p[1]} {p[0]}" for p in method.get("parameters", [])
                    )
                    parts.append(f"    - {method['name']}({params}): {method.get('return_type', 'void')}")

        # Add truncated source for context
        if len(source_code) > 2000:
            source_code = source_code[:2000] + "..."
        parts.append(f"\nSource Preview:\n{source_code}")

        return "\n".join(parts)

    def _extract_unity_callbacks(self, classes: List[Dict[str, Any]]) -> List[str]:
        """Extract Unity lifecycle callbacks from classes."""
        unity_callbacks = [
            "Awake", "Start", "Update", "FixedUpdate", "LateUpdate",
            "OnEnable", "OnDisable", "OnDestroy", "OnCollisionEnter",
            "OnCollisionExit", "OnTriggerEnter", "OnTriggerExit",
            "OnGUI", "OnDrawGizmos", "OnValidate"
        ]

        found = []
        for cls in classes:
            for method in cls.get("methods", []):
                if method["name"] in unity_callbacks:
                    found.append(method["name"])
        return list(set(found))

    async def store_asset(
        self,
        asset_path: str,
        asset_type: str,
        guid: str,
        project_id: str,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store Unity asset with dependencies."""
        collection = await self._ensure_collection(UnityCollectionType.ASSETS)

        doc_id = self._to_uuid(f"asset:{project_id}:{guid}")

        content = f"Unity Asset: {os.path.basename(asset_path)}\nType: {asset_type}\nPath: {asset_path}"
        if dependencies:
            content += f"\nDependencies: {', '.join(dependencies)}"

        embedding = await self._embed_text(content)

        payload = {
            "text": content,
            "entity_type": "asset",
            "entity_name": os.path.basename(asset_path),
            "file_path": asset_path,
            "asset_type": asset_type,
            "guid": guid,
            "project_id": project_id,
            "dependencies": dependencies or [],
            "area": "main",
            "timestamp": datetime.now().isoformat(),
            "original_id": doc_id,
            **(metadata or {})
        }

        vectors = {"dense": embedding}
        if self.enable_sparse:
            sparse = self._generate_sparse_vector(content)
            vectors["sparse"] = SparseVector(
                indices=list(sparse.keys()),
                values=list(sparse.values())
            )

        await self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload)]
        )

        # Store dependency relationships
        if dependencies:
            await self._store_relationships(
                doc_id, dependencies, "depends_on", project_id
            )

        return doc_id

    async def store_error(
        self,
        error_message: str,
        error_type: str,
        stack_trace: str,
        project_id: str,
        related_script: Optional[str] = None,
        solution: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store Unity error with context and potential solution."""
        collection = await self._ensure_collection(UnityCollectionType.ERRORS)

        doc_id = self._to_uuid(f"error:{project_id}:{hashlib.md5(error_message.encode()).hexdigest()[:8]}")

        content = f"Error: {error_message}\nType: {error_type}\nStack Trace:\n{stack_trace}"
        if solution:
            content += f"\n\nSolution:\n{solution}"

        embedding = await self._embed_text(content)

        payload = {
            "text": content,
            "entity_type": "error",
            "entity_name": error_type,
            "error_type": error_type,
            "error_message": error_message,
            "project_id": project_id,
            "related_script": related_script,
            "has_solution": solution is not None,
            "solution": solution,
            "area": "solutions" if solution else "errors",
            "timestamp": datetime.now().isoformat(),
            "original_id": doc_id,
            **(metadata or {})
        }

        vectors = {"dense": embedding}
        await self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload)]
        )

        return doc_id

    async def store_task(
        self,
        task_id: str,
        title: str,
        description: str,
        status: str,
        priority: int,
        project_id: str,
        related_entities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store development task."""
        collection = await self._ensure_collection(UnityCollectionType.TASKS)

        doc_id = self._to_uuid(f"task:{project_id}:{task_id}")

        content = f"Task: {title}\n\nDescription:\n{description}\n\nStatus: {status}\nPriority: {priority}"
        if tags:
            content += f"\nTags: {', '.join(tags)}"

        embedding = await self._embed_text(content)

        payload = {
            "text": content,
            "entity_type": "task",
            "entity_name": title,
            "task_id": task_id,
            "title": title,
            "status": status,
            "priority": priority,
            "project_id": project_id,
            "related_entities": related_entities or [],
            "tags": tags or [],
            "area": "tasks",
            "timestamp": datetime.now().isoformat(),
            "original_id": doc_id,
            **(metadata or {})
        }

        vectors = {"dense": embedding}
        await self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=doc_id, vector=vectors, payload=payload)]
        )

        return doc_id

    async def _store_relationships(
        self,
        source_id: str,
        target_ids: List[str],
        relationship_type: str,
        project_id: str
    ):
        """Store entity relationships for graph queries."""
        collection = await self._ensure_collection(UnityCollectionType.RELATIONSHIPS)

        points = []
        for target_id in target_ids:
            rel_id = self._to_uuid(f"rel:{source_id}:{target_id}:{relationship_type}")
            content = f"Relationship: {source_id} -> {relationship_type} -> {target_id}"

            embedding = await self._embed_text(content)

            payload = {
                "text": content,
                "entity_type": "relationship",
                "source_entity": source_id,
                "target_entity": target_id,
                "relationship_type": relationship_type,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "original_id": rel_id,
            }

            points.append(PointStruct(
                id=rel_id,
                vector={"dense": embedding},
                payload=payload
            ))

        if points:
            await self.client.upsert(collection_name=collection, points=points)

    # ==================== INTELLIGENT SEARCH ====================

    async def search_unity(
        self,
        query: str,
        collection_types: Optional[List[UnityCollectionType]] = None,
        project_id: Optional[str] = None,
        context: Optional[UnityQueryContext] = None,
        limit: int = 20,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_relationships: bool = False,
        multi_hop: bool = False
    ) -> List[UnitySearchResult]:
        """
        Intelligent Unity-aware search with context and relationships.

        Args:
            query: Search query
            collection_types: Specific collections to search (None = all)
            project_id: Filter by project
            context: Query context for enhanced relevance
            limit: Max results per collection
            score_threshold: Minimum similarity score
            filters: Additional payload filters
            include_relationships: Fetch related entities
            multi_hop: Enable multi-hop reasoning through relationships
        """
        threshold = score_threshold or self.score_threshold
        collections = collection_types or list(UnityCollectionType)

        # Enhance query with context
        enhanced_query = self._enhance_query_with_context(query, context)
        query_embedding = await self._embed_text(enhanced_query)

        # Build filter
        qdrant_filter = self._build_filter(project_id, filters)

        # Search all specified collections in parallel
        search_tasks = []
        for ct in collections:
            collection_name = self._get_collection_name(ct)
            if collection_name in self._collection_cache:
                search_tasks.append(
                    self._search_collection(
                        collection_name, query_embedding, query,
                        qdrant_filter, limit, threshold, ct.value
                    )
                )

        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Flatten and sort results
        all_results: List[UnitySearchResult] = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        all_results.sort(key=lambda x: x.score, reverse=True)

        # Fetch relationships if requested
        if include_relationships and all_results:
            await self._enrich_with_relationships(all_results[:limit])

        # Multi-hop reasoning
        if multi_hop and all_results:
            all_results = await self._multi_hop_expansion(
                all_results[:limit], query_embedding, project_id
            )

        return all_results[:limit]

    async def _search_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        query_text: str,
        qdrant_filter: Optional[Filter],
        limit: int,
        threshold: float,
        collection_type: str
    ) -> List[UnitySearchResult]:
        """Search a single collection."""
        try:
            # Prepare search request
            search_params = {
                "collection_name": collection_name,
                "query_vector": ("dense", query_embedding),
                "limit": limit,
                "score_threshold": threshold,
                "with_vectors": False,
            }

            if qdrant_filter:
                search_params["query_filter"] = qdrant_filter

            results = await self.client.search(**search_params)

            search_results = []
            for point in results:
                payload = dict(point.payload or {})
                text = payload.pop("text", "")
                payload["id"] = payload.get("original_id", str(point.id))

                search_results.append(UnitySearchResult(
                    document=Document(page_content=text, metadata=payload),
                    score=point.score,
                    collection=collection_type
                ))

            return search_results

        except Exception as e:
            # Collection might not exist yet
            return []

    def _enhance_query_with_context(
        self,
        query: str,
        context: Optional[UnityQueryContext]
    ) -> str:
        """Enhance search query with Unity context."""
        if not context:
            return query

        enhancements = [query]

        if context.active_scene:
            enhancements.append(f"scene:{context.active_scene}")

        if context.error_context:
            enhancements.append(f"error:{context.error_context}")

        if context.current_task:
            enhancements.append(f"task:{context.current_task}")

        return " ".join(enhancements)

    def _build_filter(
        self,
        project_id: Optional[str],
        filters: Optional[Dict[str, Any]]
    ) -> Optional[Filter]:
        """Build Qdrant filter from parameters."""
        conditions = []

        if project_id:
            conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=project_id))
            )

        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(
                        FieldCondition(key=key, match=MatchAny(any=value))
                    )
                else:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )

        if conditions:
            return Filter(must=conditions)
        return None

    async def _enrich_with_relationships(self, results: List[UnitySearchResult]):
        """Add relationship data to search results."""
        collection = self._get_collection_name(UnityCollectionType.RELATIONSHIPS)

        for result in results:
            entity_id = result.document.metadata.get("original_id")
            if not entity_id:
                continue

            try:
                # Find relationships where this entity is source or target
                rels = await self.client.scroll(
                    collection_name=collection,
                    scroll_filter=Filter(
                        should=[
                            FieldCondition(key="source_entity", match=MatchValue(value=entity_id)),
                            FieldCondition(key="target_entity", match=MatchValue(value=entity_id))
                        ]
                    ),
                    limit=10,
                    with_vectors=False
                )

                for point in rels[0]:
                    result.relationships.append(point.payload)

            except Exception:
                pass

    async def _multi_hop_expansion(
        self,
        results: List[UnitySearchResult],
        query_embedding: List[float],
        project_id: Optional[str]
    ) -> List[UnitySearchResult]:
        """Expand results through relationship graph."""
        expanded = list(results)
        seen_ids = {r.document.metadata.get("original_id") for r in results}

        # Get related entity IDs
        related_ids = set()
        for result in results:
            for rel in result.relationships:
                source = rel.get("source_entity")
                target = rel.get("target_entity")
                if source and source not in seen_ids:
                    related_ids.add(source)
                if target and target not in seen_ids:
                    related_ids.add(target)

        # Fetch related entities
        for collection_type in UnityCollectionType:
            if collection_type == UnityCollectionType.RELATIONSHIPS:
                continue

            collection = self._get_collection_name(collection_type)
            try:
                for rel_id in related_ids:
                    try:
                        points = await self.client.retrieve(
                            collection_name=collection,
                            ids=[rel_id],
                            with_vectors=False
                        )

                        for point in points:
                            payload = dict(point.payload or {})
                            text = payload.pop("text", "")
                            payload["id"] = payload.get("original_id", str(point.id))

                            expanded.append(UnitySearchResult(
                                document=Document(page_content=text, metadata=payload),
                                score=0.5,  # Lower score for related items
                                collection=collection_type.value,
                                context_chain=[r.document for r in results[:3]]
                            ))
                    except Exception:
                        continue
            except Exception:
                continue

        return expanded

    # ==================== CONVENIENCE METHODS ====================

    async def find_scripts_by_class(
        self,
        class_name: str,
        project_id: Optional[str] = None
    ) -> List[UnitySearchResult]:
        """Find scripts containing a specific class."""
        return await self.search_unity(
            query=f"class {class_name}",
            collection_types=[UnityCollectionType.SCRIPTS],
            project_id=project_id,
            filters={"class_names": class_name}
        )

    async def find_gameobjects_by_component(
        self,
        component_type: str,
        scene_name: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[UnitySearchResult]:
        """Find GameObjects with a specific component."""
        filters = {"components": component_type}
        if scene_name:
            filters["scene_name"] = scene_name

        return await self.search_unity(
            query=f"GameObject with {component_type}",
            collection_types=[UnityCollectionType.GAMEOBJECTS],
            project_id=project_id,
            filters=filters
        )

    async def find_similar_errors(
        self,
        error_message: str,
        project_id: Optional[str] = None,
        limit: int = 5
    ) -> List[UnitySearchResult]:
        """Find similar errors with potential solutions."""
        return await self.search_unity(
            query=error_message,
            collection_types=[UnityCollectionType.ERRORS, UnityCollectionType.SOLUTIONS],
            project_id=project_id,
            limit=limit,
            filters={"has_solution": True}
        )

    async def get_entity_dependencies(
        self,
        entity_id: str,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Get dependency graph for an entity."""
        collection = self._get_collection_name(UnityCollectionType.RELATIONSHIPS)
        dependencies = []
        visited = {entity_id}
        current_level = [entity_id]

        for _ in range(depth):
            next_level = []

            for eid in current_level:
                try:
                    rels, _ = await self.client.scroll(
                        collection_name=collection,
                        scroll_filter=Filter(must=[
                            FieldCondition(
                                key="source_entity",
                                match=MatchValue(value=eid)
                            ),
                            FieldCondition(
                                key="relationship_type",
                                match=MatchValue(value="depends_on")
                            )
                        ]),
                        limit=50,
                        with_vectors=False
                    )

                    for point in rels:
                        target = point.payload.get("target_entity")
                        if target and target not in visited:
                            dependencies.append(point.payload)
                            visited.add(target)
                            next_level.append(target)

                except Exception:
                    continue

            current_level = next_level
            if not current_level:
                break

        return dependencies

    # ==================== LANGCHAIN COMPATIBILITY ====================

    async def asearch(
        self,
        query: str,
        search_type: str = "similarity_score_threshold",
        k: int = 10,
        score_threshold: float | None = None,
        filter=None,
    ) -> List[Document]:
        """LangChain-compatible async search."""
        # Use unified search with general collection
        results = await self.search_unity(
            query=query,
            limit=k,
            score_threshold=score_threshold or self.score_threshold,
            filters=self._parse_langchain_filter(filter) if filter else None
        )

        return [r.document for r in results]

    async def aadd_documents(
        self,
        documents: list[Document],
        ids: Sequence[str]
    ) -> List[str]:
        """LangChain-compatible async document addition."""
        # Determine collection based on document metadata
        collection = await self._ensure_collection(UnityCollectionType.DOCUMENTATION)

        texts = [d.page_content for d in documents]
        embeddings = await self._embed_texts(texts)

        points = []
        for doc, vec, pid in zip(documents, embeddings, ids):
            payload = dict(doc.metadata or {})
            payload["text"] = doc.page_content
            payload["original_id"] = str(pid)

            point_id = self._to_uuid(pid)
            payload["id"] = point_id
            payload["timestamp"] = datetime.now().isoformat()

            vectors = {"dense": vec}
            if self.enable_sparse:
                sparse = self._generate_sparse_vector(doc.page_content)
                vectors["sparse"] = SparseVector(
                    indices=list(sparse.keys()),
                    values=list(sparse.values())
                )

            points.append(PointStruct(id=point_id, vector=vectors, payload=payload))

        # Batch upsert
        for i in range(0, len(points), self.batch_size):
            batch = points[i:i + self.batch_size]
            await self.client.upsert(collection_name=collection, points=batch)

        return list(ids)

    async def adelete(self, ids: Sequence[str]):
        """Delete documents by IDs from all collections."""
        uuid_ids = [self._to_uuid(i) for i in ids]
        points = qmodels.PointIdsList(points=uuid_ids)

        # Try to delete from all collections
        for ct in UnityCollectionType:
            collection = self._get_collection_name(ct)
            try:
                await self.client.delete(collection_name=collection, points_selector=points)
            except Exception:
                continue

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Get documents by IDs from all collections."""
        uuid_ids = [self._to_uuid(i) for i in ids]
        docs = []

        for ct in UnityCollectionType:
            collection = self._get_collection_name(ct)
            try:
                res = await self.client.retrieve(
                    collection_name=collection,
                    ids=uuid_ids,
                    with_vectors=False
                )

                for point in res:
                    payload = dict(point.payload or {})
                    text = payload.pop("text", "")
                    payload["id"] = payload.get("original_id", str(point.id))
                    docs.append(Document(page_content=text, metadata=payload))

            except Exception:
                continue

        return docs

    def _parse_langchain_filter(self, filter_input) -> Optional[Dict[str, Any]]:
        """Parse LangChain filter format to dict."""
        if isinstance(filter_input, dict):
            return filter_input
        if callable(filter_input):
            return None  # Can't convert callable
        if isinstance(filter_input, str):
            # Try to parse simple "key == 'value'" format
            try:
                result = {}
                parts = filter_input.split(" or ")
                for part in parts:
                    if "==" in part:
                        key, val = part.split("==", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        result[key] = val
                return result if result else None
            except Exception:
                return None
        return None

    # Sync compatibility
    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return []
        return loop.run_until_complete(self.aget_by_ids(ids))

    def get_all_docs(self) -> Dict[str, Document]:
        return {}  # Too expensive for multi-collection

    def save_local(self, *args, **kwargs):
        return None  # Qdrant persists automatically
