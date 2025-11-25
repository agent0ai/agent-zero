"""
Qdrant MCP Server
FastMCP-based server providing Qdrant administration tools via MCP protocol
"""

import asyncio
import logging
import sys
from typing import Union
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

from config import get_config
from tools import (
    # Collections
    list_collections,
    create_collection,
    delete_collection,
    get_collection_info,
    update_collection,
    # Points
    count_points,
    get_points,
    scroll_points,
    upsert_points,
    delete_points,
    # Search
    search_vectors,
    search_batch,
    recommend_points,
    # Admin
    optimize_collection,
    create_snapshot,
    list_snapshots,
    get_cluster_info,
    health_check,
)


# Configure logging
cfg = get_config()
logging.basicConfig(
    level=getattr(logging, cfg.mcp.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("qdrant-mcp-server")


# Create MCP server
mcp = FastMCP(
    name="qdrant-admin",
    version="1.0.0",
)


# ============================================================================
# Collection Management Tools
# ============================================================================

@mcp.tool(
    name="qdrant_list_collections",
    description="List all collections in Qdrant with basic statistics (points count, status)"
)
async def tool_list_collections():
    """List all collections"""
    return await list_collections()


@mcp.tool(
    name="qdrant_create_collection",
    description="Create a new Qdrant collection with specified vector configuration and HNSW index settings"
)
async def tool_create_collection(
    name: str,
    vector_size: int = 384,
    distance: str = "cosine",
    on_disk: bool = False,
    hnsw_m: int = 16,
    hnsw_ef_construct: int = 100,
    enable_sparse: bool = False,
):
    """Create a new collection"""
    return await create_collection(
        name=name,
        vector_size=vector_size,
        distance=distance,
        on_disk=on_disk,
        hnsw_m=hnsw_m,
        hnsw_ef_construct=hnsw_ef_construct,
        enable_sparse=enable_sparse,
    )


@mcp.tool(
    name="qdrant_delete_collection",
    description="Delete a Qdrant collection. Requires confirm=true to prevent accidental deletion."
)
async def tool_delete_collection(name: str, confirm: bool = False):
    """Delete a collection"""
    return await delete_collection(name=name, confirm=confirm)


@mcp.tool(
    name="qdrant_get_collection_info",
    description="Get detailed information about a collection including vector config, HNSW settings, and payload schema"
)
async def tool_get_collection_info(name: str):
    """Get collection details"""
    return await get_collection_info(name=name)


@mcp.tool(
    name="qdrant_update_collection",
    description="Update collection configuration (HNSW parameters, optimizer settings)"
)
async def tool_update_collection(
    name: str,
    hnsw_m: int = None,
    hnsw_ef_construct: int = None,
    indexing_threshold: int = None,
    flush_interval_sec: int = None,
):
    """Update collection config"""
    return await update_collection(
        name=name,
        hnsw_m=hnsw_m,
        hnsw_ef_construct=hnsw_ef_construct,
        indexing_threshold=indexing_threshold,
        flush_interval_sec=flush_interval_sec,
    )


# ============================================================================
# Point Operations Tools
# ============================================================================

@mcp.tool(
    name="qdrant_count_points",
    description="Count points in a collection with optional filtering. Use exact=false for fast approximate counts."
)
async def tool_count_points(
    collection: str,
    exact: bool = False,
    filter: dict = None,
):
    """Count points"""
    return await count_points(collection=collection, exact=exact, filter=filter)


@mcp.tool(
    name="qdrant_get_points",
    description="Retrieve specific points by their IDs with payload and optionally vectors"
)
async def tool_get_points(
    collection: str,
    ids: list,
    with_payload: bool = True,
    with_vector: bool = False,
):
    """Get points by ID"""
    return await get_points(
        collection=collection,
        ids=ids,
        with_payload=with_payload,
        with_vector=with_vector,
    )


@mcp.tool(
    name="qdrant_scroll_points",
    description="Scroll through all points in a collection with pagination. Use next_offset for subsequent calls."
)
async def tool_scroll_points(
    collection: str,
    limit: int = 100,
    offset: str = None,
    filter: dict = None,
    with_payload: bool = True,
    with_vector: bool = False,
):
    """Scroll points"""
    return await scroll_points(
        collection=collection,
        limit=limit,
        offset=offset,
        filter=filter,
        with_payload=with_payload,
        with_vector=with_vector,
    )


@mcp.tool(
    name="qdrant_upsert_points",
    description="Insert or update points with vectors and payload. Points: [{'id': str, 'vector': list, 'payload': dict}]"
)
async def tool_upsert_points(
    collection: str,
    points: list,
    wait: bool = True,
):
    """Upsert points"""
    return await upsert_points(collection=collection, points=points, wait=wait)


@mcp.tool(
    name="qdrant_delete_points",
    description="Delete points by IDs or filter. At least one of ids or filter must be provided."
)
async def tool_delete_points(
    collection: str,
    ids: list = None,
    filter: dict = None,
    wait: bool = True,
):
    """Delete points"""
    return await delete_points(collection=collection, ids=ids, filter=filter, wait=wait)


# ============================================================================
# Search Tools
# ============================================================================

@mcp.tool(
    name="qdrant_search_vectors",
    description="Perform similarity search with a query vector. Returns points ordered by similarity score."
)
async def tool_search_vectors(
    collection: str,
    vector: list,
    limit: int = 10,
    score_threshold: float = None,
    filter: dict = None,
    vector_name: str = "text-dense",
    with_payload: bool = True,
    with_vector: bool = False,
):
    """Search vectors"""
    return await search_vectors(
        collection=collection,
        vector=vector,
        limit=limit,
        score_threshold=score_threshold,
        filter=filter,
        vector_name=vector_name,
        with_payload=with_payload,
        with_vector=with_vector,
    )


@mcp.tool(
    name="qdrant_search_batch",
    description="Perform multiple similarity searches in a single request. Queries: [{'vector': list, 'limit': int}]"
)
async def tool_search_batch(
    collection: str,
    queries: list,
    vector_name: str = "text-dense",
    with_payload: bool = True,
):
    """Batch search"""
    return await search_batch(
        collection=collection,
        queries=queries,
        vector_name=vector_name,
        with_payload=with_payload,
    )


@mcp.tool(
    name="qdrant_recommend_points",
    description="Find points similar to positive examples and dissimilar to negative examples ('more like this')"
)
async def tool_recommend_points(
    collection: str,
    positive: list,
    negative: list = None,
    limit: int = 10,
    score_threshold: float = None,
    filter: dict = None,
    vector_name: str = "text-dense",
    with_payload: bool = True,
):
    """Recommend points"""
    return await recommend_points(
        collection=collection,
        positive=positive,
        negative=negative,
        limit=limit,
        score_threshold=score_threshold,
        filter=filter,
        vector_name=vector_name,
        with_payload=with_payload,
    )


# ============================================================================
# Admin Tools
# ============================================================================

@mcp.tool(
    name="qdrant_optimize_collection",
    description="Trigger collection optimization (merge segments, rebuild indexes). Use wait=false for large collections."
)
async def tool_optimize_collection(collection: str, wait: bool = False):
    """Optimize collection"""
    return await optimize_collection(collection=collection, wait=wait)


@mcp.tool(
    name="qdrant_create_snapshot",
    description="Create a snapshot (backup) of a collection for disaster recovery"
)
async def tool_create_snapshot(collection: str, wait: bool = True):
    """Create snapshot"""
    return await create_snapshot(collection=collection, wait=wait)


@mcp.tool(
    name="qdrant_list_snapshots",
    description="List all snapshots for a collection with names, sizes, and creation times"
)
async def tool_list_snapshots(collection: str):
    """List snapshots"""
    return await list_snapshots(collection=collection)


@mcp.tool(
    name="qdrant_get_cluster_info",
    description="Get Qdrant cluster/instance information including version, features, and all collections overview"
)
async def tool_get_cluster_info():
    """Get cluster info"""
    return await get_cluster_info()


@mcp.tool(
    name="qdrant_health_check",
    description="Check Qdrant health and connectivity with response time measurements"
)
async def tool_health_check():
    """Health check"""
    return await health_check()


# ============================================================================
# HTTP Health Endpoint (for Docker healthcheck)
# ============================================================================

async def health_endpoint(request):
    """HTTP health check endpoint for Docker/k8s"""
    result = await health_check()
    if hasattr(result, 'status') and result.status == "success":
        data = result.data
        status_code = 200 if data.get("status") == "healthy" else 503
        return JSONResponse(data, status_code=status_code)
    return JSONResponse({"status": "unhealthy"}, status_code=503)


async def root_endpoint(request):
    """Root endpoint with server info"""
    return JSONResponse({
        "name": "qdrant-admin-mcp",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "mcp_sse": "/sse",
            "mcp_messages": "/messages/",
        },
    })


# Create Starlette app with MCP integration
@asynccontextmanager
async def lifespan(app):
    """Application lifespan context manager"""
    logger.info(f"Starting Qdrant MCP Server on {cfg.mcp.host}:{cfg.mcp.port}")
    logger.info(f"Qdrant URL: {cfg.qdrant.url}")
    yield
    logger.info("Shutting down Qdrant MCP Server")


# Build the application
routes = [
    Route("/", root_endpoint),
    Route("/health", health_endpoint),
]

# Create the Starlette app
app = Starlette(
    routes=routes,
    lifespan=lifespan,
)

# Mount MCP SSE endpoint
app.mount("/", mcp.sse_app())


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=cfg.mcp.host,
        port=cfg.mcp.port,
        log_level=cfg.mcp.log_level,
    )
