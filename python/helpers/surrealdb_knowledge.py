"""
SurrealDB Knowledge Storage Helper

This module provides a graph-based knowledge storage system using SurrealDB,
designed to complement the existing FAISS-based vector storage for enhanced
relationship modeling and complex queries.

Features:
- Graph-based knowledge storage with nodes and edges
- Full-text search capabilities
- Schema-flexible document storage
- Relationship traversal queries
- Integration with existing Agent Zero memory patterns
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypedDict
from dataclasses import dataclass, field

from python.helpers.print_style import PrintStyle
from python.helpers import files


class KnowledgeNode(TypedDict, total=False):
    """Represents a knowledge node in SurrealDB."""
    id: str
    content: str
    type: str  # concept, entity, fact, procedure, etc.
    metadata: Dict[str, Any]
    embedding: Optional[List[float]]
    created_at: str
    updated_at: str
    area: str


class KnowledgeEdge(TypedDict, total=False):
    """Represents a relationship between knowledge nodes."""
    id: str
    source: str  # source node id
    target: str  # target node id
    relation: str  # type of relationship
    weight: float  # relationship strength
    metadata: Dict[str, Any]
    created_at: str


@dataclass
class SurrealDBConfig:
    """Configuration for SurrealDB connection."""
    url: str = "ws://localhost:8000/rpc"
    namespace: str = "agent_zero"
    database: str = "knowledge"
    username: str = "root"
    password: str = "root"
    
    @classmethod
    def from_env(cls) -> "SurrealDBConfig":
        """Create config from environment variables."""
        return cls(
            url=os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
            namespace=os.getenv("SURREALDB_NAMESPACE", "agent_zero"),
            database=os.getenv("SURREALDB_DATABASE", "knowledge"),
            username=os.getenv("SURREALDB_USERNAME", "root"),
            password=os.getenv("SURREALDB_PASSWORD", "root"),
        )


class SurrealDBKnowledge:
    """
    SurrealDB-based knowledge storage system for graph-based knowledge management.
    
    This class provides methods for storing, querying, and managing knowledge
    in a graph database structure, enabling complex relationship queries
    and semantic search capabilities.
    """
    
    # Singleton instances by namespace/database
    _instances: Dict[str, "SurrealDBKnowledge"] = {}
    
    def __init__(self, config: Optional[SurrealDBConfig] = None):
        """Initialize SurrealDB knowledge storage."""
        self.config = config or SurrealDBConfig.from_env()
        self._client = None
        self._connected = False
        self._initialized = False
        
    @classmethod
    def get_instance(
        cls,
        namespace: str = "agent_zero",
        database: str = "knowledge",
        config: Optional[SurrealDBConfig] = None
    ) -> "SurrealDBKnowledge":
        """Get or create a singleton instance for the specified namespace/database."""
        key = f"{namespace}/{database}"
        if key not in cls._instances:
            if config:
                cfg = config
            else:
                cfg = SurrealDBConfig.from_env()
                cfg.namespace = namespace
                cfg.database = database
            cls._instances[key] = cls(cfg)
        return cls._instances[key]
    
    async def connect(self) -> bool:
        """Establish connection to SurrealDB."""
        if self._connected:
            return True
            
        try:
            from surrealdb import Surreal
            
            self._client = Surreal(self.config.url)
            await self._client.connect()
            await self._client.signin({
                "user": self.config.username,
                "pass": self.config.password
            })
            await self._client.use(self.config.namespace, self.config.database)
            self._connected = True
            PrintStyle.standard(
                f"Connected to SurrealDB: {self.config.namespace}/{self.config.database}"
            )
            return True
        except ImportError:
            PrintStyle.warning(
                "SurrealDB package not installed. Install with: pip install surrealdb"
            )
            return False
        except Exception as e:
            PrintStyle.error(f"Failed to connect to SurrealDB: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close connection to SurrealDB."""
        if self._client and self._connected:
            try:
                await self._client.close()
            except Exception:
                pass
            finally:
                self._connected = False
                self._client = None
    
    async def initialize_schema(self) -> bool:
        """Initialize the knowledge graph schema."""
        if self._initialized:
            return True
            
        if not await self.connect():
            return False
            
        try:
            # Define schema for knowledge nodes
            await self._client.query("""
                DEFINE TABLE knowledge_node SCHEMAFULL;
                DEFINE FIELD content ON TABLE knowledge_node TYPE string;
                DEFINE FIELD type ON TABLE knowledge_node TYPE string;
                DEFINE FIELD metadata ON TABLE knowledge_node FLEXIBLE TYPE object;
                DEFINE FIELD embedding ON TABLE knowledge_node TYPE option<array<float>>;
                DEFINE FIELD created_at ON TABLE knowledge_node TYPE datetime DEFAULT time::now();
                DEFINE FIELD updated_at ON TABLE knowledge_node TYPE datetime DEFAULT time::now();
                DEFINE FIELD area ON TABLE knowledge_node TYPE string DEFAULT 'main';
                
                DEFINE INDEX idx_node_type ON TABLE knowledge_node COLUMNS type;
                DEFINE INDEX idx_node_area ON TABLE knowledge_node COLUMNS area;
            """)
            
            # Try to define full-text search (may not be available in all versions)
            try:
                await self._client.query("""
                    DEFINE ANALYZER custom_analyzer TOKENIZERS class FILTERS lowercase, ascii;
                    DEFINE INDEX idx_content_search ON TABLE knowledge_node 
                        COLUMNS content SEARCH ANALYZER custom_analyzer;
                """)
            except Exception:
                # Full-text search not available, fall back to basic functionality
                pass
            
            # Define schema for knowledge edges (relationships)
            await self._client.query("""
                DEFINE TABLE knowledge_edge SCHEMAFULL;
                DEFINE FIELD in ON TABLE knowledge_edge TYPE record<knowledge_node>;
                DEFINE FIELD out ON TABLE knowledge_edge TYPE record<knowledge_node>;
                DEFINE FIELD relation ON TABLE knowledge_edge TYPE string;
                DEFINE FIELD weight ON TABLE knowledge_edge TYPE float DEFAULT 1.0;
                DEFINE FIELD metadata ON TABLE knowledge_edge FLEXIBLE TYPE object;
                DEFINE FIELD created_at ON TABLE knowledge_edge TYPE datetime DEFAULT time::now();
                
                DEFINE INDEX idx_edge_relation ON TABLE knowledge_edge COLUMNS relation;
            """)
            
            self._initialized = True
            PrintStyle.standard("SurrealDB knowledge schema initialized")
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to initialize SurrealDB schema: {e}")
            return False
    
    async def add_node(
        self,
        content: str,
        node_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        area: str = "main",
        node_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add a knowledge node to the graph.
        
        Args:
            content: The text content of the knowledge node
            node_type: Type of knowledge (concept, entity, fact, procedure, etc.)
            metadata: Additional metadata for the node
            embedding: Vector embedding for semantic search
            area: Knowledge area (main, fragments, solutions, instruments)
            node_id: Optional custom ID for the node
            
        Returns:
            The ID of the created node, or None on failure
        """
        if not await self.connect():
            return None
            
        try:
            node_data = {
                "content": content,
                "type": node_type,
                "metadata": metadata or {},
                "area": area,
                "updated_at": datetime.now().isoformat(),
            }
            
            if embedding:
                node_data["embedding"] = embedding
                
            if node_id:
                result = await self._client.create(f"knowledge_node:{node_id}", node_data)
            else:
                result = await self._client.create("knowledge_node", node_data)
                
            if result and len(result) > 0:
                return str(result[0].get("id", ""))
            return None
        except Exception as e:
            PrintStyle.error(f"Failed to add knowledge node: {e}")
            return None
    
    async def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Add a relationship edge between two knowledge nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            relation: Type of relationship (e.g., "related_to", "is_a", "part_of")
            weight: Relationship strength (0.0 to 1.0)
            metadata: Additional metadata for the edge
            
        Returns:
            The ID of the created edge, or None on failure
        """
        if not await self.connect():
            return None
            
        try:
            # Ensure proper record format
            source_ref = source_id if ":" in source_id else f"knowledge_node:{source_id}"
            target_ref = target_id if ":" in target_id else f"knowledge_node:{target_id}"
            
            result = await self._client.query(
                f"""
                RELATE {source_ref}->knowledge_edge->{target_ref} 
                SET relation = $relation, weight = $weight, metadata = $metadata
                """,
                {
                    "relation": relation,
                    "weight": weight,
                    "metadata": metadata or {},
                }
            )
            
            if result and len(result) > 0 and len(result[0].get("result", [])) > 0:
                return str(result[0]["result"][0].get("id", ""))
            return None
        except Exception as e:
            PrintStyle.error(f"Failed to add knowledge edge: {e}")
            return None
    
    async def search_nodes(
        self,
        query: str,
        limit: int = 10,
        node_type: Optional[str] = None,
        area: Optional[str] = None,
    ) -> List[KnowledgeNode]:
        """
        Search for knowledge nodes using full-text search.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            node_type: Filter by node type
            area: Filter by knowledge area
            
        Returns:
            List of matching knowledge nodes
        """
        if not await self.connect():
            return []
            
        try:
            conditions = ["search::score(1) > 0"]
            params: Dict[str, Any] = {"query": query, "limit": limit}
            
            if node_type:
                conditions.append("type = $node_type")
                params["node_type"] = node_type
                
            if area:
                conditions.append("area = $area")
                params["area"] = area
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            # Try full-text search first, fall back to LIKE query
            try:
                result = await self._client.query(
                    f"""
                    SELECT *, search::score(1) as score 
                    FROM knowledge_node 
                    WHERE content @1@ $query AND {where_clause}
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    params
                )
            except Exception:
                # Fall back to LIKE-based search for compatibility
                result = await self._client.query(
                    f"""
                    SELECT *, 1.0 as score 
                    FROM knowledge_node 
                    WHERE string::lowercase(content) CONTAINS string::lowercase($query) AND {where_clause}
                    LIMIT $limit
                    """,
                    params
                )
            
            if result and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            PrintStyle.error(f"Failed to search knowledge nodes: {e}")
            return []
    
    async def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a knowledge node by ID."""
        if not await self.connect():
            return None
            
        try:
            ref = node_id if ":" in node_id else f"knowledge_node:{node_id}"
            result = await self._client.select(ref)
            return result if result else None
        except Exception as e:
            PrintStyle.error(f"Failed to get knowledge node: {e}")
            return None
    
    async def get_related_nodes(
        self,
        node_id: str,
        relation: Optional[str] = None,
        direction: str = "both",  # "in", "out", or "both"
        depth: int = 1,
        limit: int = 50,
    ) -> List[KnowledgeNode]:
        """
        Get nodes related to a given node through edges.
        
        Args:
            node_id: ID of the source node
            relation: Filter by specific relation type
            direction: Direction of relationships ("in", "out", or "both")
            depth: Depth of traversal (1 = direct connections only)
            limit: Maximum number of results
            
        Returns:
            List of related knowledge nodes
        """
        if not await self.connect():
            return []
            
        try:
            ref = node_id if ":" in node_id else f"knowledge_node:{node_id}"
            
            # Build traversal query based on direction
            if direction == "out":
                arrow = f"->{f'knowledge_edge' if not relation else f'knowledge_edge[relation=$relation]'}->"
            elif direction == "in":
                arrow = f"<-{f'knowledge_edge' if not relation else f'knowledge_edge[relation=$relation]'}<-"
            else:
                arrow = f"<->{f'knowledge_edge' if not relation else f'knowledge_edge[relation=$relation]'}<->"
            
            query = f"""
                SELECT * FROM {ref}{arrow}knowledge_node
                LIMIT $limit
            """
            
            params: Dict[str, Any] = {"limit": limit}
            if relation:
                params["relation"] = relation
                
            result = await self._client.query(query, params)
            
            if result and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            PrintStyle.error(f"Failed to get related nodes: {e}")
            return []
    
    async def update_node(
        self,
        node_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> bool:
        """Update an existing knowledge node."""
        if not await self.connect():
            return False
            
        try:
            ref = node_id if ":" in node_id else f"knowledge_node:{node_id}"
            
            updates = {"updated_at": datetime.now().isoformat()}
            if content is not None:
                updates["content"] = content
            if metadata is not None:
                updates["metadata"] = metadata
            if embedding is not None:
                updates["embedding"] = embedding
                
            await self._client.update(ref, updates)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to update knowledge node: {e}")
            return False
    
    async def delete_node(self, node_id: str, cascade_edges: bool = True) -> bool:
        """
        Delete a knowledge node and optionally its edges.
        
        Args:
            node_id: ID of the node to delete
            cascade_edges: If True, also delete all connected edges
            
        Returns:
            True if deletion was successful
        """
        if not await self.connect():
            return False
            
        try:
            ref = node_id if ":" in node_id else f"knowledge_node:{node_id}"
            
            if cascade_edges:
                # Delete all edges connected to this node
                await self._client.query(
                    f"DELETE knowledge_edge WHERE in = {ref} OR out = {ref}"
                )
            
            await self._client.delete(ref)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to delete knowledge node: {e}")
            return False
    
    async def delete_edge(self, edge_id: str) -> bool:
        """Delete a relationship edge."""
        if not await self.connect():
            return False
            
        try:
            await self._client.delete(edge_id)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to delete knowledge edge: {e}")
            return False
    
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find paths between two nodes in the knowledge graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            max_depth: Maximum path length to search
            
        Returns:
            List of paths, each containing nodes and edges
        """
        if not await self.connect():
            return []
            
        try:
            source_ref = source_id if ":" in source_id else f"knowledge_node:{source_id}"
            target_ref = target_id if ":" in target_id else f"knowledge_node:{target_id}"
            
            result = await self._client.query(
                f"""
                SELECT * FROM {source_ref}->knowledge_edge->knowledge_node
                WHERE id = {target_ref}
                LIMIT 100
                """
            )
            
            if result and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            PrintStyle.error(f"Failed to find path: {e}")
            return []
    
    async def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get a subgraph centered around a node.
        
        Args:
            center_id: ID of the center node
            depth: Depth of the subgraph
            limit: Maximum number of nodes
            
        Returns:
            Dictionary with nodes and edges
        """
        if not await self.connect():
            return {"nodes": [], "edges": []}
            
        try:
            ref = center_id if ":" in center_id else f"knowledge_node:{center_id}"
            
            # Get nodes
            nodes_result = await self._client.query(
                f"""
                SELECT * FROM {ref}<->knowledge_edge<->knowledge_node
                LIMIT $limit
                """,
                {"limit": limit}
            )
            
            nodes = nodes_result[0].get("result", []) if nodes_result else []
            
            # Include center node
            center_node = await self.get_node(center_id)
            if center_node:
                nodes.insert(0, center_node)
            
            # Get edges between these nodes
            node_ids = [n.get("id") for n in nodes if n.get("id")]
            edges = []
            
            if node_ids:
                edges_result = await self._client.query(
                    """
                    SELECT * FROM knowledge_edge 
                    WHERE in IN $node_ids AND out IN $node_ids
                    """,
                    {"node_ids": node_ids}
                )
                edges = edges_result[0].get("result", []) if edges_result else []
            
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            PrintStyle.error(f"Failed to get subgraph: {e}")
            return {"nodes": [], "edges": []}
    
    async def import_from_documents(
        self,
        documents: List[Dict[str, Any]],
        area: str = "main",
        extract_relations: bool = False,
    ) -> Tuple[int, int]:
        """
        Import knowledge from document-style data.
        
        Args:
            documents: List of documents with content and metadata
            area: Knowledge area for the imported nodes
            extract_relations: Whether to automatically extract relations
            
        Returns:
            Tuple of (nodes_created, edges_created)
        """
        nodes_created = 0
        edges_created = 0
        
        if not await self.connect():
            return nodes_created, edges_created
            
        for doc in documents:
            content = doc.get("content", doc.get("page_content", ""))
            metadata = doc.get("metadata", {})
            node_type = metadata.get("type", "document")
            
            node_id = await self.add_node(
                content=content,
                node_type=node_type,
                metadata=metadata,
                area=area,
            )
            
            if node_id:
                nodes_created += 1
                
        return nodes_created, edges_created
    
    async def export_to_documents(
        self,
        area: Optional[str] = None,
        node_type: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Export knowledge nodes as documents.
        
        Args:
            area: Filter by knowledge area
            node_type: Filter by node type
            limit: Maximum number of documents
            
        Returns:
            List of documents with content and metadata
        """
        if not await self.connect():
            return []
            
        try:
            conditions = []
            params: Dict[str, Any] = {"limit": limit}
            
            if area:
                conditions.append("area = $area")
                params["area"] = area
                
            if node_type:
                conditions.append("type = $node_type")
                params["node_type"] = node_type
            
            where_clause = " AND ".join(conditions) if conditions else "true"
            
            result = await self._client.query(
                f"""
                SELECT * FROM knowledge_node 
                WHERE {where_clause}
                LIMIT $limit
                """,
                params
            )
            
            documents = []
            if result and len(result) > 0:
                for node in result[0].get("result", []):
                    documents.append({
                        "content": node.get("content", ""),
                        "metadata": {
                            "id": node.get("id", ""),
                            "type": node.get("type", ""),
                            "area": node.get("area", ""),
                            **node.get("metadata", {}),
                        }
                    })
            
            return documents
        except Exception as e:
            PrintStyle.error(f"Failed to export documents: {e}")
            return []


# Helper function for agent integration
async def get_surrealdb_knowledge(
    namespace: str = "agent_zero",
    database: str = "knowledge",
) -> SurrealDBKnowledge:
    """
    Get a configured SurrealDB knowledge instance.
    
    Args:
        namespace: SurrealDB namespace
        database: SurrealDB database
        
    Returns:
        Configured SurrealDBKnowledge instance
    """
    instance = SurrealDBKnowledge.get_instance(namespace, database)
    await instance.initialize_schema()
    return instance
