"""
Search Tools for Qdrant MCP Server
Provides tools for vector similarity search and recommendations
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


# Tool 1: Search Vectors
async def search_vectors(
    collection: Annotated[
        str,
        Field(description="Name of the collection to search"),
    ],
    vector: Annotated[
        List[float],
        Field(description="Query vector for similarity search"),
    ],
    limit: Annotated[
        int,
        Field(description="Maximum number of results to return", ge=1, le=100),
    ] = 10,
    score_threshold: Annotated[
        Optional[float],
        Field(description="Minimum similarity score (0-1 for cosine). Only results above threshold are returned."),
    ] = None,
    filter: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Optional filter conditions"),
    ] = None,
    vector_name: Annotated[
        str,
        Field(description="Name of the vector to search against (for collections with multiple vectors)"),
    ] = "text-dense",
    with_payload: Annotated[
        bool,
        Field(description="Include payload in results"),
    ] = True,
    with_vector: Annotated[
        bool,
        Field(description="Include vectors in results"),
    ] = False,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Search results with scores"),
]:
    """
    Perform similarity search using a query vector.
    Returns points ordered by similarity score (highest first).
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

        # Use named vector
        query_vector = qmodels.NamedVector(
            name=vector_name,
            vector=vector,
        )

        results = await client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_payload=with_payload,
            with_vectors=with_vector,
        )

        search_results = []
        for point in results:
            result = {
                "id": str(point.id),
                "score": point.score,
            }
            if with_payload and point.payload:
                result["payload"] = dict(point.payload)
            if with_vector and point.vector:
                result["vector"] = point.vector if isinstance(point.vector, list) else dict(point.vector)
            search_results.append(result)

        return ToolResponse(data={
            "collection": collection,
            "results": search_results,
            "count": len(search_results),
            "vector_name": vector_name,
            "score_threshold": score_threshold,
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to search: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to search: {str(e)}")


# Tool 2: Batch Search
async def search_batch(
    collection: Annotated[
        str,
        Field(description="Name of the collection to search"),
    ],
    queries: Annotated[
        List[Dict[str, Any]],
        Field(description="List of search queries. Each query: {'vector': list[float], 'limit': int, 'filter': dict}"),
    ],
    vector_name: Annotated[
        str,
        Field(description="Name of the vector to search against"),
    ] = "text-dense",
    with_payload: Annotated[
        bool,
        Field(description="Include payload in results"),
    ] = True,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Batch search results"),
]:
    """
    Perform multiple similarity searches in a single request.
    More efficient than individual searches for multiple queries.
    """
    try:
        client = await get_client()

        if not queries:
            return ToolError(error="No queries provided")

        # Build search requests
        search_requests = []
        for q in queries:
            if "vector" not in q:
                return ToolError(error="Each query must have a 'vector' field")

            request = qmodels.SearchRequest(
                vector=qmodels.NamedVector(
                    name=vector_name,
                    vector=q["vector"],
                ),
                limit=q.get("limit", 10),
                score_threshold=q.get("score_threshold"),
                filter=qmodels.Filter(**q["filter"]) if q.get("filter") else None,
                with_payload=with_payload,
                with_vector=False,
            )
            search_requests.append(request)

        results = await client.search_batch(
            collection_name=collection,
            requests=search_requests,
        )

        batch_results = []
        for query_results in results:
            query_result = []
            for point in query_results:
                result = {
                    "id": str(point.id),
                    "score": point.score,
                }
                if with_payload and point.payload:
                    result["payload"] = dict(point.payload)
                query_result.append(result)
            batch_results.append(query_result)

        return ToolResponse(data={
            "collection": collection,
            "batch_results": batch_results,
            "query_count": len(queries),
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to batch search: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to batch search: {str(e)}")


# Tool 3: Recommend Points
async def recommend_points(
    collection: Annotated[
        str,
        Field(description="Name of the collection"),
    ],
    positive: Annotated[
        List[str],
        Field(description="List of point IDs to use as positive examples (find similar)"),
    ],
    negative: Annotated[
        Optional[List[str]],
        Field(description="List of point IDs to use as negative examples (avoid similar)"),
    ] = None,
    limit: Annotated[
        int,
        Field(description="Maximum number of recommendations", ge=1, le=100),
    ] = 10,
    score_threshold: Annotated[
        Optional[float],
        Field(description="Minimum similarity score for recommendations"),
    ] = None,
    filter: Annotated[
        Optional[Dict[str, Any]],
        Field(description="Optional filter conditions"),
    ] = None,
    vector_name: Annotated[
        str,
        Field(description="Name of the vector to use for recommendations"),
    ] = "text-dense",
    with_payload: Annotated[
        bool,
        Field(description="Include payload in results"),
    ] = True,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(description="Recommended points"),
]:
    """
    Find points similar to positive examples and dissimilar to negative examples.
    Useful for "more like this" functionality.
    """
    try:
        client = await get_client()

        if not positive:
            return ToolError(error="At least one positive example is required")

        # Build filter if provided
        qdrant_filter = None
        if filter:
            try:
                qdrant_filter = qmodels.Filter(**filter)
            except Exception as e:
                return ToolError(error=f"Invalid filter format: {str(e)}")

        results = await client.recommend(
            collection_name=collection,
            positive=positive,
            negative=negative or [],
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            using=vector_name,
            with_payload=with_payload,
            with_vectors=False,
        )

        recommendations = []
        for point in results:
            result = {
                "id": str(point.id),
                "score": point.score,
            }
            if with_payload and point.payload:
                result["payload"] = dict(point.payload)
            recommendations.append(result)

        return ToolResponse(data={
            "collection": collection,
            "recommendations": recommendations,
            "count": len(recommendations),
            "positive_examples": positive,
            "negative_examples": negative or [],
        })

    except UnexpectedResponse as e:
        if e.status_code == 404:
            return ToolError(error=f"Collection '{collection}' not found")
        return ToolError(error=f"Failed to get recommendations: {str(e)}")
    except Exception as e:
        return ToolError(error=f"Failed to get recommendations: {str(e)}")
