### knowledge_graph
graph-based knowledge storage using SurrealDB
store concepts entities facts with relationships
methods: add_node, add_edge, search, get_related, get_subgraph, find_path, update_node, delete_node, import_documents, export_documents, get_node
node types: concept, entity, fact, procedure, document, definition, example
relation types: is_a, part_of, related_to, causes, depends_on, precedes, similar_to, contradicts, supports, defines

1. add knowledge node
~~~json
{
    "thoughts": [
        "Need to store this concept in knowledge graph..."
    ],
    "headline": "Adding knowledge node",
    "tool_name": "knowledge_graph:add_node",
    "tool_args": {
        "content": "Machine learning is a subset of artificial intelligence...",
        "type": "concept",
        "metadata": {"domain": "AI", "source": "wikipedia"},
        "area": "main"
    }
}
~~~

2. create relationship between nodes
~~~json
{
    "thoughts": [
        "Need to connect these concepts..."
    ],
    "headline": "Creating relationship edge",
    "tool_name": "knowledge_graph:add_edge",
    "tool_args": {
        "source": "knowledge_node:abc123",
        "target": "knowledge_node:def456",
        "relation": "is_a",
        "weight": 1.0,
        "metadata": {"confidence": "high"}
    }
}
~~~

3. search knowledge
~~~json
{
    "thoughts": [
        "Let me search my knowledge graph..."
    ],
    "headline": "Searching knowledge graph",
    "tool_name": "knowledge_graph:search",
    "tool_args": {
        "query": "neural networks deep learning",
        "type": "concept",
        "area": "main",
        "limit": 10
    }
}
~~~

4. get related nodes
~~~json
{
    "thoughts": [
        "Need to find what's related to this concept..."
    ],
    "headline": "Getting related knowledge nodes",
    "tool_name": "knowledge_graph:get_related",
    "tool_args": {
        "id": "knowledge_node:abc123",
        "relation": "is_a",
        "direction": "out",
        "depth": 2,
        "limit": 20
    }
}
~~~

5. get subgraph
~~~json
{
    "thoughts": [
        "Need to understand the context around this node..."
    ],
    "headline": "Extracting knowledge subgraph",
    "tool_name": "knowledge_graph:get_subgraph",
    "tool_args": {
        "id": "knowledge_node:abc123",
        "depth": 2,
        "limit": 50
    }
}
~~~

6. find path between nodes
~~~json
{
    "thoughts": [
        "Need to find how these concepts are connected..."
    ],
    "headline": "Finding path between knowledge nodes",
    "tool_name": "knowledge_graph:find_path",
    "tool_args": {
        "source": "knowledge_node:abc123",
        "target": "knowledge_node:xyz789",
        "max_depth": 5
    }
}
~~~

7. import documents
~~~json
{
    "thoughts": [
        "Need to bulk import documents as knowledge..."
    ],
    "headline": "Importing documents to knowledge graph",
    "tool_name": "knowledge_graph:import_documents",
    "tool_args": {
        "documents": [
            {"content": "First document...", "metadata": {"source": "doc1"}},
            {"content": "Second document...", "metadata": {"source": "doc2"}}
        ],
        "area": "main",
        "extract_relations": false
    }
}
~~~

8. update node
~~~json
{
    "thoughts": [
        "Need to update this knowledge node..."
    ],
    "headline": "Updating knowledge node",
    "tool_name": "knowledge_graph:update_node",
    "tool_args": {
        "id": "knowledge_node:abc123",
        "content": "Updated content...",
        "metadata": {"updated": true}
    }
}
~~~

9. delete node
~~~json
{
    "thoughts": [
        "This knowledge is outdated, removing..."
    ],
    "headline": "Deleting knowledge node",
    "tool_name": "knowledge_graph:delete_node",
    "tool_args": {
        "id": "knowledge_node:abc123",
        "cascade_edges": true
    }
}
~~~
