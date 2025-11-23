# Qdrant MCP Server

Agent Zero exposes its Qdrant-backed memory/vector database operations via MCP (Model Context Protocol), enabling external MCP clients to perform semantic search, document insertion, deletion, and retrieval operations.

## Overview

The Qdrant MCP server provides 7 tools for interacting with Agent Zero's memory system:

1. **search_memories** - Semantic similarity search
2. **insert_memory** - Add documents with metadata
3. **delete_memories_by_query** - Remove documents via semantic matching
4. **delete_memories_by_ids** - Remove specific documents by ID
5. **get_memory_by_id** - Retrieve a single document
6. **list_memory_collections** - Show available collections
7. **get_collection_info** - Get collection statistics

## Prerequisites

### 1. Start Qdrant Container

```bash
cd docker/run
docker compose -f docker-compose.qdrant.yml up -d
```

This starts Qdrant on `http://localhost:6333` with persistent storage.

### 2. Configure Memory Backend

Edit `conf/memory.yaml`:

```yaml
backend: qdrant  # or 'hybrid' for Qdrant + FAISS fallback

qdrant:
  url: http://localhost:6333
  api_key: ""  # Optional - leave empty for local Qdrant
  collection: agent-zero
  prefer_hybrid: true
  score_threshold: 0.6
  limit: 20
  timeout: 10
```

### 3. Enable MCP Server

In Agent Zero Web UI:
1. Go to **Settings** → **External Services**
2. Enable **MCP Server**
3. Copy the **API Token** (you'll need this for client configuration)

### 4. Restart Agent Zero

The memory system will now use Qdrant for vector storage.

---

## Tool Reference

### 1. search_memories

Search memories using semantic similarity.

**Parameters:**
- `query` (string, required) - Search query text
- `memory_subdir` (string, optional) - Collection to search (default: "default")
- `limit` (integer, optional) - Max results (default: 10, range: 1-100)
- `threshold` (float, optional) - Similarity threshold 0-1 (default: 0.6)
- `filter` (string, optional) - Python expression for metadata filtering (e.g., `"area == 'solutions'"`)

**Returns:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "abc123",
      "content": "How to configure Qdrant...",
      "metadata": {
        "id": "abc123",
        "area": "solutions",
        "timestamp": "2025-01-22 10:30:00"
      }
    }
  ]
}
```

**Example:**
```python
result = await search_memories(
    query="How to setup Qdrant",
    limit=5,
    threshold=0.7,
    filter="area == 'solutions'"
)
```

---

### 2. insert_memory

Insert a new memory document.

**Parameters:**
- `text` (string, required) - Content to store
- `metadata` (object, optional) - Key-value metadata
  - Common keys: `area`, `source`, `tags`, `project`
- `memory_subdir` (string, optional) - Collection (default: "default")

**Returns:**
```json
{
  "status": "success",
  "data": {
    "id": "xyz789"
  }
}
```

**Example:**
```python
result = await insert_memory(
    text="Qdrant is configured on port 6333",
    metadata={
        "area": "solutions",
        "source": "user",
        "tags": ["qdrant", "configuration"]
    }
)
```

---

### 3. delete_memories_by_query

Delete memories matching a semantic query.

**⚠️ Destructive Operation**

**Parameters:**
- `query` (string, required) - Semantic query to find documents
- `threshold` (float, optional) - Similarity threshold (default: 0.6)
- `filter` (string, optional) - Metadata filter expression
- `memory_subdir` (string, optional) - Collection (default: "default")

**Returns:**
```json
{
  "status": "success",
  "data": {
    "count": 3,
    "deleted_ids": ["abc123", "def456", "ghi789"]
  }
}
```

**Example:**
```python
result = await delete_memories_by_query(
    query="outdated configuration instructions",
    threshold=0.8,
    filter="area == 'fragments'"
)
```

---

### 4. delete_memories_by_ids

Delete specific memories by their IDs.

**⚠️ Destructive Operation**

**Parameters:**
- `ids` (array of strings, required) - Document IDs to delete
- `memory_subdir` (string, optional) - Collection (default: "default")

**Returns:**
```json
{
  "status": "success",
  "data": {
    "count": 2
  }
}
```

**Example:**
```python
result = await delete_memories_by_ids(
    ids=["abc123", "def456"]
)
```

---

### 5. get_memory_by_id

Retrieve a document by its unique ID.

**Parameters:**
- `id` (string, required) - Document ID
- `memory_subdir` (string, optional) - Collection (default: "default")

**Returns:**
```json
{
  "status": "success",
  "data": {
    "id": "abc123",
    "content": "Document content here...",
    "metadata": {
      "id": "abc123",
      "area": "main",
      "timestamp": "2025-01-22 10:30:00"
    }
  }
}
```

**Error if not found:**
```json
{
  "status": "error",
  "error": "Document with ID 'abc123' not found"
}
```

---

### 6. list_memory_collections

List all available memory collections.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "data": {
    "collections": [
      "default",
      "projects/myproject",
      "projects/another-project"
    ]
  }
}
```

**Example:**
```python
result = await list_memory_collections()
```

---

### 7. get_collection_info

Get statistics and information about a collection.

**Parameters:**
- `memory_subdir` (string, optional) - Collection (default: "default")

**Returns:**
```json
{
  "status": "success",
  "data": {
    "memory_subdir": "default",
    "backend": "qdrant",
    "document_count": "N/A (Qdrant backend)"
  }
}
```

**Note:** Document count is only available for FAISS backend. Qdrant doesn't expose this without pagination.

---

## Client Configuration

### Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agent-zero-memory": {
      "type": "sse",
      "url": "http://localhost:50001/mcp/t-YOUR_API_TOKEN/sse"
    }
  }
}
```

Replace:
- `50001` with your Agent Zero port
- `YOUR_API_TOKEN` with the token from Settings → External Services

### MCP CLI Tool

```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/cli

# Test connection
mcp-cli http://localhost:50001/mcp/t-YOUR_API_TOKEN/sse

# List available tools
mcp-cli tools http://localhost:50001/mcp/t-YOUR_API_TOKEN/sse

# Call a tool
mcp-cli call search_memories \
  --query "Qdrant configuration" \
  --limit 5 \
  http://localhost:50001/mcp/t-YOUR_API_TOKEN/sse
```

### Python Client (using `mcp` library)

```python
from mcp import Client

async def search_agent_zero_memory():
    async with Client("http://localhost:50001/mcp/t-YOUR_API_TOKEN/sse") as client:
        result = await client.call_tool(
            "search_memories",
            query="How to configure Qdrant",
            limit=5,
            threshold=0.7
        )
        print(result)
```

---

## Memory Areas

Agent Zero organizes memories into areas via metadata:

- **main** - General knowledge and facts
- **fragments** - Conversation fragments automatically saved
- **solutions** - Successful solutions from past interactions
- **instruments** - Tool and instrument descriptions

Filter by area:
```python
result = await search_memories(
    query="solution for bug",
    filter="area == 'solutions'"
)
```

---

## Project-Specific Collections

When using Projects, each project has an isolated memory collection:

- **Global:** `default`
- **Project:** `projects/myproject`

List all collections:
```python
result = await list_memory_collections()
# Returns: ["default", "projects/myproject", "projects/another"]
```

Search project-specific memory:
```python
result = await search_memories(
    query="project configuration",
    memory_subdir="projects/myproject"
)
```

---

## Security Considerations

### Token Authentication

All MCP endpoints require a valid API token:
- Token is auto-generated from username/password in Settings
- Token changes when credentials are updated
- Include in URL: `/mcp/t-{token}/sse`

### Collection Isolation

Projects use separate collections via `projects/{name}` subdirs to prevent cross-contamination.

### Metadata Filtering

Filter expressions use `simpleeval` (safe Python subset) to prevent code injection:
- Allowed: `area == 'solutions'`, `'important' in tags`, `timestamp > '2025-01-01'`
- Disallowed: `__import__('os').system('rm -rf /')` ❌

### Destructive Operations

Delete operations are marked with `destructiveHint: true` in MCP metadata. Clients should:
1. Prompt user for confirmation
2. Show what will be deleted (use `search_memories` first)
3. Log deletion operations for audit

---

## Troubleshooting

### Connection Refused

**Symptom:** `Connection refused to http://localhost:50001`

**Solutions:**
1. Verify Agent Zero is running: `docker ps` or check WebUI
2. Confirm port mapping: Settings → check `WEB_UI_PORT`
3. Test base URL: `curl http://localhost:50001`

### Invalid Token

**Symptom:** `403 Forbidden` or `MCP forbidden`

**Solutions:**
1. Copy fresh token from Settings → External Services
2. Ensure token hasn't changed (happens when auth credentials update)
3. Check token in URL exactly matches settings

### Qdrant Not Running

**Symptom:** `Failed to initialize memory: Connection refused`

**Solutions:**
```bash
# Check Qdrant status
docker ps | grep qdrant

# Start Qdrant
cd docker/run
docker compose -f docker-compose.qdrant.yml up -d

# Verify Qdrant is accessible
curl http://localhost:6333/health
```

### Empty Search Results

**Symptom:** `search_memories` returns `[]`

**Possible Causes:**
1. **Threshold too high** - Lower threshold to 0.4-0.5
2. **Wrong collection** - Verify `memory_subdir` exists via `list_memory_collections`
3. **No documents** - Insert test documents first
4. **Filter too restrictive** - Remove filter or adjust expression

**Debug:**
```python
# 1. List collections
collections = await list_memory_collections()

# 2. Check collection info
info = await get_collection_info(memory_subdir="default")

# 3. Lower threshold
results = await search_memories(
    query="test",
    threshold=0.1,  # Very permissive
    limit=100
)
```

### Backend Mismatch

**Symptom:** `backend: faiss` when expecting Qdrant

**Solutions:**
1. Edit `conf/memory.yaml` and set `backend: qdrant`
2. Restart Agent Zero completely
3. Verify with `get_collection_info()` - should return `"backend": "qdrant"`

---

## Performance Tips

### Batch Operations

Instead of multiple single inserts:
```python
# ❌ Slow
for doc in documents:
    await insert_memory(doc.text, doc.metadata)
```

Use batch approach:
```python
# ✅ Faster - insert all at once if possible
# (Note: Current API doesn't support batch insert directly)
# Workaround: Use asyncio.gather for parallel inserts
import asyncio
await asyncio.gather(*[
    insert_memory(doc.text, doc.metadata)
    for doc in documents
])
```

### Search Optimization

1. **Use filters** to reduce search space:
   ```python
   # Faster - searches only 'solutions' area
   await search_memories(
       query="bug fix",
       filter="area == 'solutions'"
   )
   ```

2. **Limit results** appropriately:
   ```python
   # Don't fetch more than needed
   await search_memories(query="...", limit=5)  # Not 100
   ```

3. **Adjust threshold** based on use case:
   - **High precision:** `threshold=0.8` (fewer, more relevant results)
   - **High recall:** `threshold=0.4` (more results, some noise)

---

## Example Use Cases

### 1. Search Agent's Knowledge

```python
# Find what Agent Zero knows about Qdrant
result = await search_memories(
    query="Qdrant configuration and setup",
    limit=10,
    threshold=0.7
)

for doc in result["data"]:
    print(f"[{doc['metadata']['area']}] {doc['content'][:100]}...")
```

### 2. Add Custom Knowledge

```python
# Teach Agent Zero something new
await insert_memory(
    text="Production Qdrant cluster is at qdrant.prod.example.com:6333",
    metadata={
        "area": "main",
        "source": "admin",
        "tags": ["qdrant", "production", "infrastructure"]
    }
)
```

### 3. Clean Up Old Memories

```python
# Find and remove outdated instructions
result = await delete_memories_by_query(
    query="old python 2 instructions",
    threshold=0.75,
    filter="area == 'fragments'"
)
print(f"Removed {result['data']['count']} outdated memories")
```

### 4. Extract Project Knowledge

```python
# Get all collections
collections = await list_memory_collections()

# Search each project
for collection in collections["data"]["collections"]:
    if collection.startswith("projects/"):
        results = await search_memories(
            query="API endpoints",
            memory_subdir=collection,
            limit=5
        )
        print(f"\n{collection}:")
        for doc in results["data"]:
            print(f"  - {doc['content'][:80]}...")
```

---

## Further Reading

- [Agent Zero Architecture](architecture.md) - Memory system overview
- [Qdrant Setup](qdrant.md) - Detailed Qdrant configuration
- [MCP Setup](mcp_setup.md) - MCP client configuration
- [Connectivity](connectivity.md) - External API endpoints and A2A protocol
