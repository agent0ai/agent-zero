from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from python.helpers.memory import Memory, get_existing_memory_subdirs
from python.helpers.print_style import PrintStyle
from langchain_core.documents import Document

_PRINTER = PrintStyle(italic=True, font_color="blue", padding=False)


# Response models
class QdrantToolResponse(BaseModel):
    status: Literal["success"] = Field(
        description="The status of the response", default="success"
    )
    data: dict | list | str = Field(description="The response data")


class QdrantToolError(BaseModel):
    status: Literal["error"] = Field(
        description="The status of the response", default="error"
    )
    error: str = Field(description="The error message")


# Helper function to get memory instance
async def _get_memory_instance(memory_subdir: str = "default") -> Memory:
    """Get or initialize a Memory instance for the specified subdir."""
    try:
        return await Memory.get_by_subdir(
            memory_subdir=memory_subdir,
            log_item=None,
            preload_knowledge=False,
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize memory for subdir '{memory_subdir}': {str(e)}"
        )


# Tool 1: Search memories
async def search_memories(
    query: Annotated[
        str,
        Field(
            description="The semantic search query text to find relevant documents",
            title="query",
        ),
    ],
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to search (e.g., 'default', 'projects/myproject'). Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results to return. Default: 10",
            title="limit",
            ge=1,
            le=100,
        ),
    ] = 10,
    threshold: Annotated[
        float,
        Field(
            description="Similarity threshold (0-1). Only documents with score above this threshold are returned. Default: 0.6",
            title="threshold",
            ge=0.0,
            le=1.0,
        ),
    ] = 0.6,
    filter: Annotated[
        str | None,
        Field(
            description="Optional Python expression for metadata filtering (e.g., \"area == 'solutions'\", \"'tag' in tags\"). Default: None",
            title="filter",
        ),
    ] = None,
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Search results with documents, scores, and metadata"),
]:
    """
    Search memories using semantic similarity.
    Returns documents that match the query semantically, ordered by relevance score.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Searching memories: '{query}' in '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        docs = await memory.search_similarity_threshold(
            query=query,
            limit=limit,
            threshold=threshold,
            filter=filter or "",
        )
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                "id": doc.metadata.get("id", ""),
                "content": doc.page_content,
                "metadata": doc.metadata,
            })
        
        _PRINTER.print(f"[Qdrant MCP] Found {len(results)} documents")
        return QdrantToolResponse(data=results)
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Search failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 2: Insert memory
async def insert_memory(
    text: Annotated[
        str,
        Field(
            description="The text content to store in memory",
            title="text",
        ),
    ],
    metadata: Annotated[
        dict | None,
        Field(
            description="Optional metadata key-value pairs (e.g., {'area': 'solutions', 'source': 'user', 'tags': ['important']}). Default: {}",
            title="metadata",
        ),
    ] = None,
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to insert into. Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Document ID of the inserted memory"),
]:
    """
    Insert a new memory document with optional metadata.
    Returns the unique ID of the inserted document.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Inserting memory into '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        doc_id = await memory.insert_text(
            text=text,
            metadata=metadata or {},
        )
        
        _PRINTER.print(f"[Qdrant MCP] Inserted document with ID: {doc_id}")
        return QdrantToolResponse(data={"id": doc_id})
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Insert failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 3: Delete memories by query
async def delete_memories_by_query(
    query: Annotated[
        str,
        Field(
            description="Semantic query to find documents to delete",
            title="query",
        ),
    ],
    threshold: Annotated[
        float,
        Field(
            description="Similarity threshold (0-1). Documents with score above this threshold will be deleted. Default: 0.6",
            title="threshold",
            ge=0.0,
            le=1.0,
        ),
    ] = 0.6,
    filter: Annotated[
        str | None,
        Field(
            description="Optional Python expression for metadata filtering. Default: None",
            title="filter",
        ),
    ] = None,
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to delete from. Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Count of deleted documents and their IDs"),
]:
    """
    Delete memories that match a semantic query.
    This is a destructive operation - use with caution.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Deleting memories by query: '{query}' in '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        removed_docs = await memory.delete_documents_by_query(
            query=query,
            threshold=threshold,
            filter=filter or "",
        )
        
        removed_ids = [doc.metadata.get("id", "") for doc in removed_docs]
        
        _PRINTER.print(f"[Qdrant MCP] Deleted {len(removed_ids)} documents")
        return QdrantToolResponse(data={
            "count": len(removed_ids),
            "deleted_ids": removed_ids,
        })
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Delete by query failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 4: Delete memories by IDs
async def delete_memories_by_ids(
    ids: Annotated[
        list[str],
        Field(
            description="List of document IDs to delete",
            title="ids",
        ),
    ],
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to delete from. Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Count of deleted documents"),
]:
    """
    Delete specific memories by their IDs.
    This is a destructive operation - use with caution.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Deleting {len(ids)} documents by ID from '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        removed_docs = await memory.delete_documents_by_ids(ids=ids)
        
        _PRINTER.print(f"[Qdrant MCP] Deleted {len(removed_docs)} documents")
        return QdrantToolResponse(data={"count": len(removed_docs)})
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Delete by IDs failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 5: Get memory by ID
async def get_memory_by_id(
    id: Annotated[
        str,
        Field(
            description="Document ID to retrieve",
            title="id",
        ),
    ],
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to retrieve from. Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Document content and metadata"),
]:
    """
    Retrieve a specific memory document by its ID.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Getting document by ID: {id} from '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        doc = memory.get_document_by_id(id)
        
        if not doc:
            return QdrantToolError(error=f"Document with ID '{id}' not found")
        
        result = {
            "id": doc.metadata.get("id", ""),
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        
        _PRINTER.print(f"[Qdrant MCP] Retrieved document: {id}")
        return QdrantToolResponse(data=result)
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Get by ID failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 6: List memory collections
async def list_memory_collections() -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="List of available memory collections/subdirectories"),
]:
    """
    List all available memory collections (subdirectories).
    Includes default collection and project-specific collections.
    """
    try:
        _PRINTER.print("[Qdrant MCP] Listing memory collections")
        
        subdirs = get_existing_memory_subdirs()
        
        _PRINTER.print(f"[Qdrant MCP] Found {len(subdirs)} collections")
        return QdrantToolResponse(data={"collections": subdirs})
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] List collections failed: {e}")
        return QdrantToolError(error=str(e))


# Tool 7: Get collection info
async def get_collection_info(
    memory_subdir: Annotated[
        str,
        Field(
            description="Memory collection to get info about. Default: 'default'",
            title="memory_subdir",
        ),
    ] = "default",
) -> Annotated[
    Union[QdrantToolResponse, QdrantToolError],
    Field(description="Collection information including backend type and statistics"),
]:
    """
    Get information about a specific memory collection.
    Returns backend type (faiss/qdrant), document count estimate, and configuration.
    """
    try:
        _PRINTER.print(f"[Qdrant MCP] Getting info for collection: '{memory_subdir}'")
        
        memory = await _get_memory_instance(memory_subdir)
        
        # Get basic info
        info = {
            "memory_subdir": memory_subdir,
            "backend": memory.backend,
        }
        
        # Try to get document count (FAISS only, Qdrant doesn't expose this easily)
        try:
            if memory.backend == "faiss":
                all_docs = memory.db.get_all_docs()
                info["document_count"] = len(all_docs) if all_docs else 0
            else:
                info["document_count"] = "N/A (Qdrant backend)"
        except Exception:
            info["document_count"] = "N/A"
        
        _PRINTER.print(f"[Qdrant MCP] Collection info retrieved for '{memory_subdir}'")
        return QdrantToolResponse(data=info)
        
    except Exception as e:
        _PRINTER.print(f"[Qdrant MCP] Get collection info failed: {e}")
        return QdrantToolError(error=str(e))
