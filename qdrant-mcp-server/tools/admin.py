"""
Admin Tools for Qdrant MCP Server
Provides tools for optimization, snapshots, and cluster management
"""

from typing import Annotated, Union, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from datetime import datetime

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


# Tool 1: Optimize Collection
async def optimize_collection(
    collection: Annotated[
        str,
        Field(description="Name of the collection to optimize"),
    ],
    wait: Annotated[
        bool,
        Field(description="Wait for optimization to complete (can take a while for large collections)"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Optimization result"),
]:
    """
    Trigger collection optimization.
    This merges segments and rebuilds indexes for better performance.
    Use wait=False for large collections to avoid timeout.
    """
    try:
        client = await get_client()

        # Get pre-optimization stats
        info_before = await client.get_collection(collection)
        segments_before = info_before.segments_count

        # Trigger optimization
        await client.update_collection(
            collection_name=collection,
            optimizer_config=qmodels.OptimizersConfigDiff(
                indexing_threshold=0,  # Force immediate indexing
            ),
        )

        result = {
            "collection": collection,
            "operation": "optimize",
            "segments_before": segments_before,
            "optimization_triggered": True,
        }

        if wait:
            # Wait for optimization and get new stats
            import asyncio
            max_wait = 60  # Max 60 seconds
            waited = 0
            while waited < max_wait:
                await asyncio.sleep(2)
                waited += 2
                info_after = await client.get_collection(collection)
                if info_after.optimizer_status and info_after.optimizer_status.status == qmodels.OptimizersStatus.OK:
                    result["segments_after"] = info_after.segments_count
                    result["optimization_complete"] = True
                    break
            else:
                result["optimization_complete"] = False
                result["message"] = "Optimization still in progress"

        return ToolResponse(data=result)

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to optimize collection: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to optimize collection: {str(e)}")


# Tool 2: Create Snapshot
async def create_snapshot(
    collection: Annotated[
        str,
        Field(description="Name of the collection to snapshot"),
    ],
    wait: Annotated[
        bool,
        Field(description="Wait for snapshot to complete"),
    ] = True,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Snapshot creation result"),
]:
    """
    Create a snapshot (backup) of a collection.
    Snapshots can be used to restore the collection state.
    """
    try:
        client = await get_client()

        # Get collection info for metadata
        info = await client.get_collection(collection)

        # Create snapshot
        snapshot = await client.create_snapshot(
            collection_name=collection,
            wait=wait,
        )

        return ToolResponse(data={
            "collection": collection,
            "snapshot_name": snapshot.name if snapshot else "pending",
            "points_count": info.points_count,
            "created_at": datetime.utcnow().isoformat(),
            "status": "completed" if wait and snapshot else "in_progress",
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to create snapshot: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to create snapshot: {str(e)}")


# Tool 3: List Snapshots
async def list_snapshots(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="List of collection snapshots"),
]:
    """
    List all snapshots for a collection.
    Shows snapshot names, sizes, and creation times.
    """
    try:
        client = await get_client()

        snapshots = await client.list_snapshots(collection_name=collection)

        snapshot_list = []
        for snap in snapshots:
            snapshot_list.append({
                "name": snap.name,
                "size_bytes": snap.size if hasattr(snap, 'size') else None,
                "creation_time": snap.creation_time.isoformat() if hasattr(snap, 'creation_time') and snap.creation_time else None,
            })

        return ToolResponse(data={
            "collection": collection,
            "snapshots": snapshot_list,
            "count": len(snapshot_list),
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to list snapshots: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to list snapshots: {str(e)}")


# Tool 4: Get Cluster Info
async def get_cluster_info() -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Qdrant cluster/instance information"),
]:
    """
    Get information about the Qdrant cluster or instance.
    Shows version, enabled features, and cluster status.
    """
    try:
        client = await get_client()
        cfg = get_config()

        # Get telemetry data for version info
        # Note: This endpoint may not be available on all Qdrant versions
        import httpx

        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(
                    f"{cfg.qdrant.url}/",
                    timeout=10,
                )
                root_info = response.json() if response.status_code == 200 else {}
            except Exception:
                root_info = {}

        # Get collections for overview
        collections = await client.get_collections()

        total_points = 0
        total_vectors = 0
        collection_summaries = []

        for coll in collections.collections:
            try:
                info = await client.get_collection(coll.name)
                total_points += info.points_count or 0
                total_vectors += info.vectors_count or 0
                collection_summaries.append({
                    "name": coll.name,
                    "points": info.points_count,
                    "status": info.status.value if info.status else "unknown",
                })
            except Exception:
                collection_summaries.append({
                    "name": coll.name,
                    "points": 0,
                    "status": "error",
                })

        return ToolResponse(data={
            "url": cfg.qdrant.url,
            "version": root_info.get("version", "unknown"),
            "title": root_info.get("title", "Qdrant"),
            "collections_count": len(collections.collections),
            "total_points": total_points,
            "total_vectors": total_vectors,
            "collections": collection_summaries,
        })

    except Exception as e:
        return ToolError(error=f"Failed to get cluster info: {str(e)}")


# Tool 5: Health Check
async def health_check() -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Qdrant health status"),
]:
    """
    Check Qdrant health and connectivity.
    Returns detailed status including response time.
    """
    try:
        import time
        import httpx

        cfg = get_config()
        start_time = time.time()

        # Check HTTP connectivity
        async with httpx.AsyncClient() as http_client:
            try:
                response = await http_client.get(
                    f"{cfg.qdrant.url}/",
                    timeout=5,
                )
                http_ok = response.status_code == 200
                http_latency = time.time() - start_time
            except Exception as e:
                return ToolResponse(data={
                    "status": "unhealthy",
                    "http_ok": False,
                    "error": str(e),
                    "url": cfg.qdrant.url,
                })

        # Check API functionality
        client = await get_client()
        api_start = time.time()
        try:
            await client.get_collections()
            api_ok = True
            api_latency = time.time() - api_start
        except Exception as e:
            api_ok = False
            api_latency = time.time() - api_start

        return ToolResponse(data={
            "status": "healthy" if http_ok and api_ok else "degraded",
            "url": cfg.qdrant.url,
            "http_ok": http_ok,
            "http_latency_ms": round(http_latency * 1000, 2),
            "api_ok": api_ok,
            "api_latency_ms": round(api_latency * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        return ToolError(error=f"Health check failed: {str(e)}")
