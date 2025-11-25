"""
Collection Management Tools for Qdrant MCP Server
Provides tools for creating, managing, and inspecting collections
"""

from typing import Annotated, Union, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

import sys
sys.path.append('..')
from config import get_config


# Response Models
class ToolResponse(BaseModel):
    """Successful tool response"""
    status: str = Field(default="success", description="Response status")
    data: Dict[str, Any] | List[Any] | str = Field(description="Response data")


class ToolError(BaseModel):
    """Error tool response"""
    status: str = Field(default="error", description="Response status")
    error: str = Field(description="Error message")


# Qdrant client singleton
_client: Optional[AsyncQdrantClient] = None


async def get_client() -> AsyncQdrantClient:
    """Get or create Qdrant client"""
    global _client
    if _client is None:
        cfg = get_config()
        _client = AsyncQdrantClient(
            url=cfg.qdrant.url,
            api_key=cfg.qdrant.api_key,
            timeout=cfg.qdrant.timeout,
            prefer_grpc=cfg.qdrant.prefer_grpc,
        )
    return _client


# Tool 1: List Collections
async def list_collections() -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="List of all collections with basic info"),
]:
    """
    List all collections in the Qdrant database.
    Returns collection names, vector configurations, and point counts.
    """
    try:
        client = await get_client()
        response = await client.get_collections()

        collections = []
        for collection in response.collections:
            # Get detailed info for each collection
            try:
                info = await client.get_collection(collection.name)
                collections.append({
                    "name": collection.name,
                    "status": info.status.value if info.status else "unknown",
                    "points_count": info.points_count,
                    "vectors_count": info.vectors_count,
                    "indexed_vectors_count": info.indexed_vectors_count,
                    "segments_count": info.segments_count,
                })
            except Exception:
                collections.append({
                    "name": collection.name,
                    "status": "unknown",
                    "points_count": 0,
                })

        return ToolResponse(data={
            "collections": collections,
            "total_count": len(collections),
        })

    except Exception as e:
        return ToolError(error=f"Failed to list collections: {str(e)}")


# Tool 2: Create Collection
async def create_collection(
    name: Annotated[
        str,
        Field(description="Name of the collection to create"),
    ],
    vector_size: Annotated[
        int,
        Field(description="Dimension of vectors (e.g., 384 for MiniLM, 1536 for OpenAI)", ge=1, le=65536),
    ] = 384,
    distance: Annotated[
        str,
        Field(description="Distance metric: 'cosine', 'euclid', or 'dot'"),
    ] = "cosine",
    on_disk: Annotated[
        bool,
        Field(description="Store vectors on disk (for large collections)"),
    ] = False,
    hnsw_m: Annotated[
        int,
        Field(description="HNSW index M parameter (higher = better recall, more memory)", ge=4, le=128),
    ] = 16,
    hnsw_ef_construct: Annotated[
        int,
        Field(description="HNSW index ef_construct (higher = better quality, slower build)", ge=4, le=512),
    ] = 100,
    enable_sparse: Annotated[
        bool,
        Field(description="Enable sparse vectors for hybrid search"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Collection creation result"),
]:
    """
    Create a new collection with specified vector configuration.
    Supports dense vectors with optional sparse vectors for hybrid search.
    """
    try:
        client = await get_client()

        # Check if collection exists
        collections = await client.get_collections()
        if name in [c.name for c in collections.collections]:
            return ToolError(error=f"Collection '{name}' already exists")

        # Map distance string to enum
        distance_map = {
            "cosine": qmodels.Distance.COSINE,
            "euclid": qmodels.Distance.EUCLID,
            "dot": qmodels.Distance.DOT,
        }
        distance_enum = distance_map.get(distance.lower(), qmodels.Distance.COSINE)

        # Vector configuration
        vectors_config = {
            "text-dense": qmodels.VectorParams(
                size=vector_size,
                distance=distance_enum,
                on_disk=on_disk,
            )
        }

        # Sparse vector configuration
        sparse_vectors_config = None
        if enable_sparse:
            sparse_vectors_config = {
                "text-sparse": qmodels.SparseVectorParams(
                    index=qmodels.SparseIndexParams(on_disk=on_disk)
                )
            }

        # HNSW configuration
        hnsw_config = qmodels.HnswConfigDiff(
            m=hnsw_m,
            ef_construct=hnsw_ef_construct,
        )

        # Create collection
        await client.create_collection(
            collection_name=name,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_vectors_config,
            hnsw_config=hnsw_config,
        )

        return ToolResponse(data={
            "message": f"Collection '{name}' created successfully",
            "config": {
                "name": name,
                "vector_size": vector_size,
                "distance": distance,
                "on_disk": on_disk,
                "hnsw_m": hnsw_m,
                "hnsw_ef_construct": hnsw_ef_construct,
                "sparse_enabled": enable_sparse,
            }
        })

    except Exception as e:
        return ToolError(error=f"Failed to create collection: {str(e)}")


# Tool 3: Delete Collection
async def delete_collection(
    name: Annotated[
        str,
        Field(description="Name of the collection to delete"),
    ],
    confirm: Annotated[
        bool,
        Field(description="Must be true to confirm deletion"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Collection deletion result"),
]:
    """
    Delete a collection and all its data.
    Requires explicit confirmation to prevent accidental data loss.
    """
    try:
        if not confirm:
            return ToolError(error="Deletion requires confirm=true to prevent accidental data loss")

        client = await get_client()

        # Check if collection exists
        collections = await client.get_collections()
        if name not in [c.name for c in collections.collections]:
            return ToolError(error=f"Collection '{name}' does not exist")

        # Get point count before deletion
        info = await client.get_collection(name)
        points_count = info.points_count

        # Delete collection
        await client.delete_collection(collection_name=name)

        return ToolResponse(data={
            "message": f"Collection '{name}' deleted successfully",
            "deleted_points": points_count,
        })

    except Exception as e:
        return ToolError(error=f"Failed to delete collection: {str(e)}")


# Tool 4: Get Collection Info
async def get_collection_info(
    name: Annotated[
        str,
        Field(description="Name of the collection to inspect"),
    ],
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Detailed collection information"),
]:
    """
    Get detailed information about a collection including:
    - Vector configuration
    - Index settings
    - Point counts
    - Storage statistics
    - Optimizer status
    """
    try:
        client = await get_client()

        info = await client.get_collection(name)

        # Extract vector configs
        vectors_config = {}
        if isinstance(info.config.params.vectors, dict):
            for vec_name, vec_params in info.config.params.vectors.items():
                vectors_config[vec_name] = {
                    "size": vec_params.size,
                    "distance": vec_params.distance.value if vec_params.distance else "unknown",
                    "on_disk": vec_params.on_disk,
                }
        else:
            vectors_config["default"] = {
                "size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.value if info.config.params.vectors.distance else "unknown",
            }

        # Extract HNSW config
        hnsw_config = {}
        if info.config.hnsw_config:
            hnsw_config = {
                "m": info.config.hnsw_config.m,
                "ef_construct": info.config.hnsw_config.ef_construct,
                "full_scan_threshold": info.config.hnsw_config.full_scan_threshold,
            }

        return ToolResponse(data={
            "name": name,
            "status": info.status.value if info.status else "unknown",
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "segments_count": info.segments_count,
            "vectors_config": vectors_config,
            "hnsw_config": hnsw_config,
            "optimizer_status": info.optimizer_status.status.value if info.optimizer_status and info.optimizer_status.status else "unknown",
            "payload_schema": {k: v.data_type.value if v.data_type else "unknown" for k, v in (info.payload_schema or {}).items()},
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{name}' not found")
        return ToolError(error=f"Failed to get collection info: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to get collection info: {str(e)}")


# Tool 5: Update Collection
async def update_collection(
    name: Annotated[
        str,
        Field(description="Name of the collection to update"),
    ],
    hnsw_m: Annotated[
        Optional[int],
        Field(description="New HNSW M parameter", ge=4, le=128),
    ] = None,
    hnsw_ef_construct: Annotated[
        Optional[int],
        Field(description="New HNSW ef_construct parameter", ge=4, le=512),
    ] = None,
    indexing_threshold: Annotated[
        Optional[int],
        Field(description="Number of vectors to trigger indexing", ge=0),
    ] = None,
    flush_interval_sec: Annotated[
        Optional[int],
        Field(description="Interval between disk flushes in seconds", ge=0),
    ] = None,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Collection update result"),
]:
    """
    Update collection configuration parameters.
    Changes HNSW index settings, optimizer thresholds, or flush intervals.
    """
    try:
        client = await get_client()

        # Build update params
        hnsw_config = None
        if hnsw_m is not None or hnsw_ef_construct is not None:
            hnsw_config = qmodels.HnswConfigDiff(
                m=hnsw_m,
                ef_construct=hnsw_ef_construct,
            )

        optimizers_config = None
        if indexing_threshold is not None or flush_interval_sec is not None:
            optimizers_config = qmodels.OptimizersConfigDiff(
                indexing_threshold=indexing_threshold,
                flush_interval_sec=flush_interval_sec,
            )

        if hnsw_config is None and optimizers_config is None:
            return ToolError(error="No update parameters provided")

        # Update collection
        await client.update_collection(
            collection_name=name,
            hnsw_config=hnsw_config,
            optimizers_config=optimizers_config,
        )

        return ToolResponse(data={
            "message": f"Collection '{name}' updated successfully",
            "updates": {
                "hnsw_m": hnsw_m,
                "hnsw_ef_construct": hnsw_ef_construct,
                "indexing_threshold": indexing_threshold,
                "flush_interval_sec": flush_interval_sec,
            }
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{name}' not found")
        return ToolError(error=f"Failed to update collection: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to update collection: {str(e)}")
