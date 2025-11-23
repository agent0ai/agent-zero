# Agent Zero Memory & Knowledge System Architecture

## Overview
Agent Zero implements a sophisticated memory and knowledge system using FAISS vector database with intelligent consolidation, auto-recall, and hierarchical organization.

## Core Components

### 1. Memory System (`python/helpers/memory.py`)

**Main Class: `Memory`**
- Uses FAISS (Facebook AI Similarity Search) for vector storage
- Implements cosine similarity for semantic search
- Supports multiple memory areas with isolation
- Project-based memory subdirectories for multi-tenancy

**Memory Areas (Enum)**
```python
Memory.Area:
  - MAIN: General purpose memories
  - FRAGMENTS: Partial/temporary memories
  - SOLUTIONS: Stored solutions and patterns
  - INSTRUMENTS: Tool/instrument descriptions
```

**Key Methods**
- `Memory.get(agent)`: Get memory instance for agent
- `insert_text(text, metadata)`: Store new memory with metadata
- `search_similarity_threshold(query, limit, threshold, filter)`: Semantic search
- `delete_documents_by_ids(ids)`: Remove specific memories
- `get_document_by_id(id)`: Retrieve specific memory

### 2. Vector Database (`python/helpers/vector_db.py`)

**Class: `VectorDB`**
- Wrapper around FAISS for general vector operations
- Implements cached embeddings for efficiency
- Supports metadata-based filtering
- Cosine similarity normalization

**Class: `MyFaiss` (extends FAISS)**
- Custom FAISS implementation with async support
- Enhanced document retrieval by IDs
- Access to all stored documents

### 3. Memory Tools

**MemorySave (`python/tools/memory_save.py`)**
```python
execute(text="", area="", **kwargs)
  - Saves text to specified memory area
  - Returns memory ID for reference
  - Supports custom metadata via kwargs
```

**MemoryLoad (`python/tools/memory_load.py`)**
```python
execute(query="", threshold=0.7, limit=10, filter="")
  - Searches memories by semantic similarity
  - Configurable similarity threshold
  - Metadata filtering support
```

**MemoryDelete (`python/tools/memory_delete.py`)**
- Removes specific memories by ID or filter

**MemoryForget (`python/tools/memory_forget.py`)**
- Bulk memory cleanup operations

### 4. Memory Consolidation (`python/helpers/memory_consolidation.py`)

**Intelligent Consolidation Features**
- Automatic deduplication of similar memories
- LLM-powered consolidation decisions
- Actions: MERGE, REPLACE, KEEP_SEPARATE, UPDATE, SKIP
- Configurable similarity thresholds
- Keyword extraction for better search

**ConsolidationConfig**
```python
- similarity_threshold: 0.7 (default)
- max_similar_memories: 10
- replace_similarity_threshold: 0.9
- processing_timeout_seconds: 60
```

### 5. Knowledge Base System (`python/helpers/knowledge_import.py`)

**Supported File Types**
- Text files (.txt, .md, .json)
- PDFs (.pdf)
- CSV files (.csv)
- HTML files (.html)

**Knowledge Loading Process**
1. File change detection via checksums
2. Document parsing with appropriate loaders
3. Automatic chunking for large documents
4. Metadata enrichment with area tags
5. Incremental updates (only changed files)

**Knowledge Organization**
- Root knowledge → Main memory area
- Subdirectories → Corresponding memory areas
- Instruments folder → Special handling
- Project-specific knowledge isolation

## Memory Dashboard UI Features

### Settings Panel (Screenshot Analysis)
- **Memory Subdirectory**: Project-based isolation (default: "default")
- **Memory auto-recall enabled**: Automatic memory retrieval toggle
- **Memory auto-recall delayed**: Async delivery option
- **Auto-recall AI query preparation**: LLM-enhanced search queries
- **Auto-recall AI post-filtering**: LLM-based relevance filtering
- **Memory auto-recall interval**: Frequency control (1-10 messages)
- **Memory auto-recall history length**: Context window (default: 10000 chars)

### Dashboard Interface (Screenshot Analysis)
- **Memory Directory**: Project selection dropdown
- **Area Filter**: All Areas, Main, Fragments, Solutions, Instruments
- **Search**: Real-time memory content search
- **Limit**: Max results (default: 1000)
- **Threshold**: Similarity threshold slider (0.0-1.0, default: 0.60)
- **Statistics**: Total, Filtered, Knowledge, Conversation counts
- **Metadata/Preview**: Tabbed view for memory inspection

## Auto-Recall System

**How It Works**
1. Monitors conversation context
2. Triggers at configured intervals
3. Generates optimized search queries via utility LLM
4. Retrieves relevant memories semantically
5. Filters results with utility LLM
6. Injects memories into agent context

**Configuration Options**
- Enable/disable auto-recall
- Delayed vs immediate delivery
- AI-enhanced query generation
- AI-powered post-filtering
- Interval control (every N messages)
- History context window size

## Storage Structure

```
/memory/
  /{project_subdir}/
    /db/
      - index.faiss (vector index)
      - index.pkl (document store)
      - embedding.json (model metadata)
      - knowledge_import.json (import tracking)
    /embeddings/ (cached embeddings)

/knowledge/
  /{project_subdir}/
    /main/ (general knowledge)
    /fragments/ (partial info)
    /solutions/ (problem solutions)
    /instruments/ (tool docs)
```

## Embedding Models

- Configurable via agent settings
- Supports multiple providers (OpenAI, local, etc.)
- Cached embeddings for performance
- Model-specific namespacing

## Integration Points

### 1. Agent Integration
```python
# Get memory instance
db = await Memory.get(agent)

# Save memory
id = await db.insert_text("Important information", {"area": "main"})

# Search memories
docs = await db.search_similarity_threshold(
    query="relevant topic",
    limit=10,
    threshold=0.7
)
```

### 2. Tool Usage
Agents can use memory tools directly:
```
memory_save(text="Remember this", area="main")
memory_load(query="previous solution", threshold=0.8)
```

### 3. Knowledge Preloading
Automatic at agent initialization:
- Scans configured knowledge directories
- Loads new/changed files
- Updates vector index
- Maintains import tracking

### 4. Memory Consolidation
Triggered on new memory insertion:
- Finds similar existing memories
- Uses LLM to decide consolidation action
- Updates/merges as appropriate
- Maintains memory quality

## Performance Optimizations

1. **Cached Embeddings**: Reuse computed embeddings
2. **Incremental Updates**: Only process changed files
3. **Lazy Loading**: Initialize on first use
4. **Project Isolation**: Separate indices per project
5. **Batch Operations**: Bulk insert/delete support
6. **Async Processing**: Non-blocking operations

## Best Practices for Integration

1. **Memory Areas**: Use appropriate areas for organization
2. **Metadata**: Include rich metadata for filtering
3. **Threshold Tuning**: Adjust similarity thresholds per use case
4. **Consolidation**: Enable for deduplication
5. **Auto-Recall**: Configure based on conversation type
6. **Knowledge Structure**: Organize files by purpose
7. **Project Isolation**: Use subdirectories for multi-tenancy