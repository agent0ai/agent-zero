"""
Knowledge Graph Tool

This tool provides graph-based knowledge management capabilities using SurrealDB
for storing, querying, and traversing knowledge relationships.
"""

import json
from typing import Any, Dict, List, Optional

from python.helpers.tool import Tool, Response
from python.helpers.surrealdb_knowledge import (
    SurrealDBKnowledge,
    get_surrealdb_knowledge,
    KnowledgeNode,
)
from python.helpers.print_style import PrintStyle


class KnowledgeGraph(Tool):
    """
    Knowledge graph tool for managing graph-based knowledge storage.
    
    Methods:
        add_node: Add a knowledge node to the graph
        add_edge: Create a relationship between nodes
        search: Search for knowledge nodes
        get_related: Get nodes related to a given node
        get_subgraph: Get a subgraph around a node
        find_path: Find paths between two nodes
        update_node: Update an existing node
        delete_node: Delete a node
        import_documents: Import documents as knowledge nodes
        export_documents: Export knowledge as documents
    """
    
    async def execute(self, **kwargs) -> Response:
        """Execute the knowledge graph tool based on method."""
        method = self.method or kwargs.get("method", "search")
        
        # Get or create SurrealDB instance
        namespace = kwargs.get("namespace", "agent_zero")
        database = kwargs.get("database", "knowledge")
        
        try:
            self._db = await get_surrealdb_knowledge(namespace, database)
        except Exception as e:
            return Response(
                message=f"Failed to connect to SurrealDB: {str(e)}. Make sure SurrealDB is running.",
                break_loop=False
            )
        
        try:
            if method == "add_node":
                return await self._add_node(**kwargs)
            elif method == "add_edge":
                return await self._add_edge(**kwargs)
            elif method == "search":
                return await self._search(**kwargs)
            elif method == "get_related":
                return await self._get_related(**kwargs)
            elif method == "get_subgraph":
                return await self._get_subgraph(**kwargs)
            elif method == "find_path":
                return await self._find_path(**kwargs)
            elif method == "update_node":
                return await self._update_node(**kwargs)
            elif method == "delete_node":
                return await self._delete_node(**kwargs)
            elif method == "import_documents":
                return await self._import_documents(**kwargs)
            elif method == "export_documents":
                return await self._export_documents(**kwargs)
            elif method == "get_node":
                return await self._get_node(**kwargs)
            else:
                return Response(
                    message=f"Unknown method: {method}. Available methods: add_node, add_edge, search, get_related, get_subgraph, find_path, update_node, delete_node, import_documents, export_documents, get_node",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Knowledge graph error: {str(e)}",
                break_loop=False
            )
    
    async def _add_node(self, **kwargs) -> Response:
        """Add a knowledge node."""
        content = kwargs.get("content", "")
        node_type = kwargs.get("type", "fact")
        metadata = kwargs.get("metadata", {})
        embedding = kwargs.get("embedding", None)
        area = kwargs.get("area", "main")
        node_id = kwargs.get("id", None)
        
        if not content:
            return Response(message="No content provided for knowledge node", break_loop=False)
        
        result_id = await self._db.add_node(
            content=content,
            node_type=node_type,
            metadata=metadata,
            embedding=embedding,
            area=area,
            node_id=node_id
        )
        
        if result_id:
            return Response(
                message=f"Successfully created knowledge node with ID: {result_id}",
                break_loop=False
            )
        else:
            return Response(
                message="Failed to create knowledge node",
                break_loop=False
            )
    
    async def _add_edge(self, **kwargs) -> Response:
        """Add a relationship edge between nodes."""
        source_id = kwargs.get("source", "")
        target_id = kwargs.get("target", "")
        relation = kwargs.get("relation", "related_to")
        weight = kwargs.get("weight", 1.0)
        metadata = kwargs.get("metadata", {})
        
        if not source_id or not target_id:
            return Response(
                message="Both source and target node IDs are required",
                break_loop=False
            )
        
        result_id = await self._db.add_edge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
            metadata=metadata
        )
        
        if result_id:
            return Response(
                message=f"Successfully created edge '{relation}' from {source_id} to {target_id}",
                break_loop=False
            )
        else:
            return Response(
                message="Failed to create edge",
                break_loop=False
            )
    
    async def _search(self, **kwargs) -> Response:
        """Search for knowledge nodes."""
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 10)
        node_type = kwargs.get("type", None)
        area = kwargs.get("area", None)
        
        if not query:
            return Response(message="No search query provided", break_loop=False)
        
        results = await self._db.search_nodes(
            query=query,
            limit=limit,
            node_type=node_type,
            area=area
        )
        
        if results:
            # Format results for readability
            formatted_results = []
            for node in results:
                formatted_results.append({
                    "id": node.get("id", ""),
                    "content": node.get("content", "")[:200] + "..." if len(node.get("content", "")) > 200 else node.get("content", ""),
                    "type": node.get("type", ""),
                    "area": node.get("area", ""),
                    "score": node.get("score", 0),
                })
            
            return Response(
                message=f"Found {len(results)} matching nodes:\n{json.dumps(formatted_results, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"No knowledge nodes found matching '{query}'",
                break_loop=False
            )
    
    async def _get_node(self, **kwargs) -> Response:
        """Get a specific knowledge node by ID."""
        node_id = kwargs.get("id", "")
        
        if not node_id:
            return Response(message="No node ID provided", break_loop=False)
        
        node = await self._db.get_node(node_id)
        
        if node:
            return Response(
                message=f"Knowledge node:\n{json.dumps(node, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"Node not found: {node_id}",
                break_loop=False
            )
    
    async def _get_related(self, **kwargs) -> Response:
        """Get nodes related to a given node."""
        node_id = kwargs.get("id", "")
        relation = kwargs.get("relation", None)
        direction = kwargs.get("direction", "both")
        depth = kwargs.get("depth", 1)
        limit = kwargs.get("limit", 50)
        
        if not node_id:
            return Response(message="No node ID provided", break_loop=False)
        
        results = await self._db.get_related_nodes(
            node_id=node_id,
            relation=relation,
            direction=direction,
            depth=depth,
            limit=limit
        )
        
        if results:
            # Format results
            formatted_results = []
            for node in results:
                formatted_results.append({
                    "id": node.get("id", ""),
                    "content": node.get("content", "")[:100] + "..." if len(node.get("content", "")) > 100 else node.get("content", ""),
                    "type": node.get("type", ""),
                })
            
            relation_info = f" via '{relation}'" if relation else ""
            return Response(
                message=f"Found {len(results)} related nodes{relation_info}:\n{json.dumps(formatted_results, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"No related nodes found for {node_id}",
                break_loop=False
            )
    
    async def _get_subgraph(self, **kwargs) -> Response:
        """Get a subgraph around a node."""
        node_id = kwargs.get("id", "")
        depth = kwargs.get("depth", 2)
        limit = kwargs.get("limit", 100)
        
        if not node_id:
            return Response(message="No node ID provided", break_loop=False)
        
        result = await self._db.get_subgraph(
            center_id=node_id,
            depth=depth,
            limit=limit
        )
        
        nodes = result.get("nodes", [])
        edges = result.get("edges", [])
        
        return Response(
            message=f"Subgraph around {node_id}:\n  Nodes: {len(nodes)}\n  Edges: {len(edges)}\n\nNodes:\n{json.dumps(nodes[:20], indent=2, default=str)}",
            break_loop=False
        )
    
    async def _find_path(self, **kwargs) -> Response:
        """Find paths between two nodes."""
        source_id = kwargs.get("source", "")
        target_id = kwargs.get("target", "")
        max_depth = kwargs.get("max_depth", 5)
        
        if not source_id or not target_id:
            return Response(
                message="Both source and target node IDs are required",
                break_loop=False
            )
        
        paths = await self._db.find_path(
            source_id=source_id,
            target_id=target_id,
            max_depth=max_depth
        )
        
        if paths:
            return Response(
                message=f"Found {len(paths)} path(s) from {source_id} to {target_id}:\n{json.dumps(paths, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"No path found from {source_id} to {target_id}",
                break_loop=False
            )
    
    async def _update_node(self, **kwargs) -> Response:
        """Update an existing knowledge node."""
        node_id = kwargs.get("id", "")
        content = kwargs.get("content", None)
        metadata = kwargs.get("metadata", None)
        embedding = kwargs.get("embedding", None)
        
        if not node_id:
            return Response(message="No node ID provided", break_loop=False)
        
        if content is None and metadata is None and embedding is None:
            return Response(
                message="No update parameters provided (content, metadata, or embedding)",
                break_loop=False
            )
        
        success = await self._db.update_node(
            node_id=node_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        if success:
            return Response(
                message=f"Successfully updated node {node_id}",
                break_loop=False
            )
        else:
            return Response(
                message=f"Failed to update node {node_id}",
                break_loop=False
            )
    
    async def _delete_node(self, **kwargs) -> Response:
        """Delete a knowledge node."""
        node_id = kwargs.get("id", "")
        cascade_edges = kwargs.get("cascade_edges", True)
        
        if not node_id:
            return Response(message="No node ID provided", break_loop=False)
        
        success = await self._db.delete_node(node_id, cascade_edges)
        
        if success:
            return Response(
                message=f"Successfully deleted node {node_id}" + 
                        (" and its edges" if cascade_edges else ""),
                break_loop=False
            )
        else:
            return Response(
                message=f"Failed to delete node {node_id}",
                break_loop=False
            )
    
    async def _import_documents(self, **kwargs) -> Response:
        """Import documents as knowledge nodes."""
        documents = kwargs.get("documents", [])
        area = kwargs.get("area", "main")
        extract_relations = kwargs.get("extract_relations", False)
        
        if not documents:
            return Response(message="No documents provided", break_loop=False)
        
        nodes_created, edges_created = await self._db.import_from_documents(
            documents=documents,
            area=area,
            extract_relations=extract_relations
        )
        
        return Response(
            message=f"Import complete: {nodes_created} nodes created" +
                    (f", {edges_created} edges created" if edges_created > 0 else ""),
            break_loop=False
        )
    
    async def _export_documents(self, **kwargs) -> Response:
        """Export knowledge nodes as documents."""
        area = kwargs.get("area", None)
        node_type = kwargs.get("type", None)
        limit = kwargs.get("limit", 1000)
        
        documents = await self._db.export_to_documents(
            area=area,
            node_type=node_type,
            limit=limit
        )
        
        if documents:
            # Truncate content for display
            display_docs = []
            for doc in documents[:20]:
                content = doc.get("content", "")
                display_docs.append({
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "metadata": doc.get("metadata", {})
                })
            
            return Response(
                message=f"Exported {len(documents)} documents:\n{json.dumps(display_docs, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message="No documents to export",
                break_loop=False
            )
