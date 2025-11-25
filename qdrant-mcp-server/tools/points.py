"""
Point Operations Tools for Qdrant MCP Server
Provides tools for managing points (documents) in collections
"""

from typing import Annotated, Union, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
import uuid

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


def _to_uuid(id_str: str) -> str:
    """Convert any string ID to a deterministic UUID"""
    try:
        uuid.UUID(str(id_str))
        return str(id_str)
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_str)))


# Tool 1: Count Points
async def count_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    exact: Annotated[
        bool,
        Field(description="If true, returns exact count (slower). If false, returns approximate count."),
    ] = False,
    filter: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Optional filter conditions (e.g., {'must': [{'key': 'field', 'match': {'value': 'x'}}]})"),
    ] = None,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Point count result"),
]:
    """
    Count points in a collection with optional filtering.
    Use exact=False for fast approximate counts on large collections.
    """
    try:
        client = await get_client()

        # Build filter if provided
        qdrant_filter = None
        if filter:
            try:
                qdrant_filter = qmodels.Filter(**filter)
            except Exception as e:
                return ToolError(error=f"Invalid filter format: {str(e)}")

        result = await client.count(
            collection_name=collection,
            count_filter=qdrant_filter,
            exact=exact,
        )

        return ToolResponse(data={
            "collection": collection,
            "count": result.count,
            "exact": exact,
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to count points: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to count points: {str(e)}")


# Tool 2: Get Points by ID
async def get_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    ids: Annotated[
        List[str],
        Field(description="List of point IDs to retrieve"),
    ],
    with_payload: Annotated[
        bool,
        Field(description="Include payload in response"),
    ] = True,
    with_vector: Annotated[
        bool,
        Field(description="Include vectors in response"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Retrieved points"),
]:
    """
    Retrieve specific points by their IDs.
    Returns payload and optionally vectors for each point.
    """
    try:
        client = await get_client()

        # Convert IDs to UUIDs
        uuid_ids = [_to_uuid(pid) for pid in ids]

        result = await client.retrieve(
            collection_name=collection,
            ids=uuid_ids,
            with_payload=with_payload,
            with_vectors=with_vector,
        )

        points = []
        for point in result:
            point_data = {
                "id": str(point.id),
            }
            if with_payload and point.payload:
                point_data["payload"] = dict(point.payload)
            if with_vector and point.vector:
                point_data["vector"] = point.vector if isinstance(point.vector, list) else dict(point.vector)
            points.append(point_data)

        return ToolResponse(data={
            "collection": collection,
            "points": points,
            "found_count": len(points),
            "requested_count": len(ids),
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to get points: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to get points: {str(e)}")


# Tool 3: Scroll Points
async def scroll_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    limit: Annotated[
        int,
        Field(description="Maximum number of points to return", ge=1, le=1000),
    ] = 100,
    offset: Annotated[
        Optional[str],
        Field(description="Scroll offset from previous call (use 'next_offset' from previous response)"),
    ] = None,
    filter: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Optional filter conditions"),
    ] = None,
    with_payload: Annotated[
        bool,
        Field(description="Include payload in response"),
    ] = True,
    with_vector: Annotated[
        bool,
        Field(description="Include vectors in response"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Scrolled points with pagination info"),
]:
    """
    Scroll through all points in a collection with pagination.
    Use 'next_offset' from response for subsequent calls.
    """
    try:
        client = await get_client()

        # Build filter if provided
        qdrant_filter = None
        if filter:
            try:
                qdrant_filter = qmodels.Filter(**filter)
            except Exception as e:
                return ToolError(error=f"Invalid filter format: {str(e)}")

        result, next_offset = await client.scroll(
            collection_name=collection,
            limit=limit,
            offset=offset,
            scroll_filter=qdrant_filter,
            with_payload=with_payload,
            with_vectors=with_vector,
        )

        points = []
        for point in result:
            point_data = {
                "id": str(point.id),
            }
            if with_payload and point.payload:
                point_data["payload"] = dict(point.payload)
            if with_vector and point.vector:
                point_data["vector"] = point.vector if isinstance(point.vector, list) else dict(point.vector)
            points.append(point_data)

        return ToolResponse(data={
            "collection": collection,
            "points": points,
            "count": len(points),
            "next_offset": str(next_offset) if next_offset else None,
            "has_more": next_offset is not None,
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to scroll points: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to scroll points: {str(e)}")


# Tool 4: Upsert Points
async def upsert_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    points: Annotated[
        List[Dict[str, Any]],
        Field(description="List of points to upsert. Each point: {'id': str, 'vector': list[float] or dict, 'payload': dict}"),
    ],
    wait: Annotated[
        bool,
        Field(description="Wait for operation to complete before returning"),
    ] = True,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Upsert operation result"),
]:
    """
    Insert or update points in a collection.
    If a point with the same ID exists, it will be overwritten.
    """
    try:
        client = await get_client()

        if not points:
            return ToolError(error="No points provided")

        # Convert points to Qdrant format
        qdrant_points = []
        for p in points:
            if "id" not in p or "vector" not in p:
                return ToolError(error="Each point must have 'id' and 'vector' fields")

            point_id = _to_uuid(p["id"])

            # Handle named vectors or single vector
            vector = p["vector"]
            if isinstance(vector, dict):
                # Named vectors
                pass
            elif isinstance(vector, list):
                # Single vector - use default name
                vector = {"text-dense": vector}

            payload = p.get("payload", {})
            payload["original_id"] = p["id"]

            qdrant_points.append(qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            ))

        # Upsert points
        await client.upsert(
            collection_name=collection,
            points=qdrant_points,
            wait=wait,
        )

        return ToolResponse(data={
            "collection": collection,
            "upserted_count": len(qdrant_points),
            "operation": "upsert",
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to upsert points: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to upsert points: {str(e)}")


# Tool 5: Delete Points
async def delete_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    ids: Annotated[
        Optional[List[str]],
        Field(description="List of point IDs to delete"),
    ] = None,
    filter: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Filter to select points for deletion"),
    ] = None,
    wait: Annotated[
        bool,
        Field(description="Wait for operation to complete before returning"),
    ] = True,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Delete operation result"),
]:
    """
    Delete points by IDs or filter.
    At least one of 'ids' or 'filter' must be provided.
    """
    try:
        client = await get_client()

        if ids is None and filter is None:
            return ToolError(error="Either 'ids' or 'filter' must be provided")

        points_selector = None

        if ids:
            # Delete by IDs
            uuid_ids = [_to_uuid(pid) for pid in ids]
            points_selector = qmodels.PointIdsList(points=uuid_ids)
        elif filter:
            # Delete by filter
            try:
                qdrant_filter = qmodels.Filter(**filter)
                points_selector = qmodels.FilterSelector(filter=qdrant_filter)
            except Exception as e:
                return ToolError(error=f"Invalid filter format: {str(e)}")

        await client.delete(
            collection_name=collection,
            points_selector=points_selector,
            wait=wait,
        )

        return ToolResponse(data={
            "collection": collection,
            "operation": "delete",
            "deleted_by": "ids" if ids else "filter",
            "ids_count": len(ids) if ids else None,
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to delete points: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to delete points: {str(e)}")
