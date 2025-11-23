# Agent Zero Memory & Knowledge Integration Guide

## Quick Start Integration

### 1. Basic Memory Operations

```python
from python.helpers.memory import Memory
from agent import Agent

# Initialize memory for an agent
async def setup_memory(agent: Agent):
    db = await Memory.get(agent)
    return db

# Save a memory
async def save_memory(agent: Agent, content: str, area: str = "main"):
    db = await Memory.get(agent)
    memory_id = await db.insert_text(
        text=content,
        metadata={
            "area": area,
            "timestamp": datetime.now().isoformat(),
            "source": "integration",
            # Add custom metadata
            "category": "user_data",
            "importance": "high"
        }
    )
    return memory_id

# Search memories
async def search_memories(agent: Agent, query: str):
    db = await Memory.get(agent)
    results = await db.search_similarity_threshold(
        query=query,
        limit=10,
        threshold=0.7,
        filter=""  # Optional metadata filter
    )
    return results
```

### 2. Creating Custom Memory Tools

```python
from python.helpers.tool import Tool, Response
from python.helpers.memory import Memory

class CustomMemoryTool(Tool):
    """Custom tool for specialized memory operations"""
    
    async def execute(self, action="save", content="", **kwargs):
        db = await Memory.get(self.agent)
        
        if action == "save":
            # Custom save logic
            memory_id = await db.insert_text(
                text=content,
                metadata={
                    "area": kwargs.get("area", "main"),
                    "tool": "custom",
                    "tags": kwargs.get("tags", []),
                }
            )
            return Response(
                message=f"Saved with ID: {memory_id}",
                break_loop=False
            )
        
        elif action == "search":
            # Custom search logic
            docs = await db.search_similarity_threshold(
                query=content,
                limit=kwargs.get("limit", 5),
                threshold=kwargs.get("threshold", 0.75)
            )
            formatted = Memory.format_docs_plain(docs)
            return Response(
                message="\n".join(formatted),
                break_loop=False
            )
```

### 3. Knowledge Base Integration

```python
from python.helpers.knowledge_import import load_knowledge

async def import_custom_knowledge(
    agent: Agent,
    knowledge_path: str,
    area: Memory.Area = Memory.Area.MAIN
):
    """Import custom knowledge files into memory"""
    
    db = await Memory.get(agent)
    log_item = agent.context.log.log(
        type="util",
        heading="Importing custom knowledge"
    )
    
    # Load knowledge with change detection
    index = {}
    index = load_knowledge(
        log_item=log_item,
        knowledge_dir=knowledge_path,
        index=index,
        metadata={"area": area.value, "source": "custom"},
        filename_pattern="**/*.md",  # Adjust pattern as needed
        recursive=True
    )
    
    # Process and insert documents
    for file_info in index.values():
        if file_info["state"] == "changed":
            for doc in file_info["documents"]:
                await db.insert_documents([doc])
    
    return index
```

### 4. Memory Consolidation Integration

```python
from python.helpers.memory_consolidation import (
    MemoryConsolidator,
    ConsolidationConfig
)

async def save_with_consolidation(
    agent: Agent,
    content: str,
    area: str = "main"
):
    """Save memory with automatic consolidation"""
    
    # Configure consolidation
    config = ConsolidationConfig(
        similarity_threshold=0.8,  # Higher for more aggressive merging
        max_similar_memories=5,
        replace_similarity_threshold=0.95
    )
    
    consolidator = MemoryConsolidator(agent, config)
    
    # Process with consolidation
    result = await consolidator.process_new_memory(
        new_memory=content,
        area=area,
        metadata={
            "timestamp": datetime.now().isoformat(),
            "consolidated": True
        }
    )
    
    return result
```

### 5. Auto-Recall Configuration

```python
def configure_auto_recall(agent: Agent):
    """Configure memory auto-recall settings"""
    
    settings = {
        # Enable auto-recall
        "memory_auto_recall": True,
        
        # Use delayed delivery for better performance
        "memory_auto_recall_delayed": False,
        
        # Enable AI-enhanced features
        "memory_auto_recall_query_prep": True,
        "memory_auto_recall_post_filter": True,
        
        # Trigger every 3 messages
        "memory_auto_recall_interval": 3,
        
        # Use 10KB of history for context
        "memory_auto_recall_history_length": 10000,
        
        # Quality thresholds
        "memory_threshold": 0.7,
        "memory_limit": 10
    }
    
    # Apply settings to agent configuration
    for key, value in settings.items():
        setattr(agent.config, key, value)
    
    return settings
```

### 6. Project-Based Memory Isolation

```python
async def setup_project_memory(
    agent: Agent,
    project_name: str
):
    """Initialize memory for a specific project"""
    
    # Set project subdirectory
    agent.config.memory_subdir = project_name
    
    # Initialize project-specific memory
    db = await Memory.get(agent)
    
    # Preload project knowledge if exists
    knowledge_path = f"knowledge/{project_name}"
    if os.path.exists(knowledge_path):
        await db.preload_knowledge(
            log_item=None,
            kn_dirs=[project_name],
            memory_subdir=project_name
        )
    
    return db
```

### 7. Advanced Search with Metadata Filtering

```python
async def search_with_filters(
    agent: Agent,
    query: str,
    area: str = None,
    tags: list = None,
    date_from: str = None
):
    """Advanced memory search with metadata filtering"""
    
    db = await Memory.get(agent)
    
    # Build filter expression
    filters = []
    if area:
        filters.append(f'area == "{area}"')
    if tags:
        for tag in tags:
            filters.append(f'"{tag}" in tags')
    if date_from:
        filters.append(f'timestamp >= "{date_from}"')
    
    filter_expr = " and ".join(filters) if filters else ""
    
    # Search with filters
    results = await db.search_similarity_threshold(
        query=query,
        limit=20,
        threshold=0.6,
        filter=filter_expr
    )
    
    return results
```

### 8. Memory Dashboard API Integration

```python
from python.api import memory as memory_api

async def get_memory_stats(agent: Agent):
    """Get memory statistics for dashboard"""
    
    db = await Memory.get(agent)
    
    # Get all documents
    all_docs = db.db.get_all_docs()
    
    # Calculate statistics
    stats = {
        "total": len(all_docs),
        "by_area": {},
        "knowledge": 0,
        "conversation": 0
    }
    
    for doc in all_docs.values():
        area = doc.metadata.get("area", "unknown")
        stats["by_area"][area] = stats["by_area"].get(area, 0) + 1
        
        if doc.metadata.get("source") == "knowledge":
            stats["knowledge"] += 1
        elif doc.metadata.get("source") == "conversation":
            stats["conversation"] += 1
    
    return stats
```

## Integration Best Practices

### 1. Memory Organization
```python
# Use consistent metadata schema
MEMORY_METADATA_SCHEMA = {
    "area": str,           # Memory area (main, fragments, solutions)
    "timestamp": str,      # ISO format timestamp
    "source": str,         # Origin (user, agent, knowledge, api)
    "category": str,       # Content category
    "tags": list,          # Searchable tags
    "importance": str,     # Priority level (low, medium, high)
    "ttl": int,           # Time-to-live in seconds (optional)
}
```

### 2. Performance Optimization
```python
# Batch operations for efficiency
async def batch_insert_memories(agent: Agent, memories: list):
    db = await Memory.get(agent)
    
    documents = []
    for mem in memories:
        doc = Document(
            page_content=mem["content"],
            metadata=mem.get("metadata", {})
        )
        documents.append(doc)
    
    # Batch insert
    ids = await db.insert_documents(documents)
    return ids
```

### 3. Error Handling
```python
async def safe_memory_operation(agent: Agent, operation: str, **kwargs):
    try:
        db = await Memory.get(agent)
        
        if operation == "save":
            return await db.insert_text(**kwargs)
        elif operation == "search":
            return await db.search_similarity_threshold(**kwargs)
        elif operation == "delete":
            return await db.delete_documents_by_ids(**kwargs)
            
    except Exception as e:
        agent.context.log.log(
            type="error",
            heading=f"Memory operation failed: {operation}",
            content=str(e)
        )
        return None
```

### 4. Memory Lifecycle Management
```python
async def cleanup_old_memories(
    agent: Agent,
    days_old: int = 30,
    area: str = "fragments"
):
    """Clean up old memories based on TTL or age"""
    
    db = await Memory.get(agent)
    cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
    
    # Search for old memories
    filter_expr = f'area == "{area}" and timestamp < "{cutoff_date}"'
    old_docs = await db.search_by_metadata(filter=filter_expr)
    
    # Delete old memories
    if old_docs:
        ids = [doc.metadata.get("id") for doc in old_docs if doc.metadata.get("id")]
        await db.delete_documents_by_ids(ids)
        
    return len(old_docs)
```

## Testing Your Integration

```python
import asyncio

async def test_memory_integration(agent: Agent):
    """Test suite for memory integration"""
    
    # Test 1: Save and retrieve
    memory_id = await save_memory(
        agent, 
        "Test memory content",
        area="main"
    )
    assert memory_id is not None
    
    # Test 2: Search
    results = await search_memories(
        agent,
        "test content"
    )
    assert len(results) > 0
    
    # Test 3: Consolidation
    similar_content = "Test memory information"
    consolidated = await save_with_consolidation(
        agent,
        similar_content,
        area="main"
    )
    assert consolidated["success"]
    
    # Test 4: Metadata filtering
    filtered = await search_with_filters(
        agent,
        query="test",
        area="main"
    )
    assert all(d.metadata.get("area") == "main" for d in filtered)
    
    print("✅ All memory integration tests passed!")

# Run tests
# asyncio.run(test_memory_integration(agent))
```

## Common Integration Patterns

### 1. Chat History Persistence
Store conversation history for context continuity

### 2. Solution Caching
Save successful solutions for future reference

### 3. User Preference Learning
Track and recall user preferences

### 4. Knowledge Augmentation
Dynamically add domain knowledge

### 5. Cross-Session Context
Maintain context across multiple sessions

### 6. Collaborative Memory
Share memories between agent instances

## Troubleshooting

### Common Issues and Solutions

1. **Memory not persisting**: Check memory_subdir configuration
2. **Poor search results**: Adjust similarity threshold
3. **Duplicate memories**: Enable consolidation
4. **Slow performance**: Use cached embeddings
5. **Out of memory**: Implement cleanup routines
6. **Index corruption**: Rebuild from saved documents