"""
Unified memory API wrapping FAISS-backed Memory and KnowledgeGraph.

Provides a single surface for save/recall/connect/get_context that
coordinates vector search with graph traversal and temporal scoring.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from python.helpers.knowledge_graph import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
)
from python.helpers.memory import Memory
from python.helpers.temporal_filter import ScoringWeights, rank_nodes, score


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryInterface:
    """Unified API over FAISS Memory + KnowledgeGraph."""

    def __init__(
        self,
        memory: Memory,
        graph: KnowledgeGraph | None = None,
        scoring_weights: ScoringWeights | None = None,
    ):
        self.memory = memory
        self.graph = graph or KnowledgeGraph()
        self.weights = scoring_weights or ScoringWeights()

    # ── save ─────────────────────────────────────────────────────────

    async def save(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        area: str = "main",
    ) -> str:
        """Save text to FAISS and create a corresponding KnowledgeNode.

        Returns the document id.
        """
        meta = dict(metadata or {})
        meta["area"] = area

        doc_id = await self.memory.insert_text(text, metadata=meta)

        now = _utcnow()
        node = KnowledgeNode(
            id=doc_id,
            content=text,
            memory_area=area,
            created_at=now,
            last_accessed=now,
            access_count=0,
            activation_score=1.0,
            metadata=meta,
        )
        self.graph.add_node(node)
        return doc_id

    # ── recall ───────────────────────────────────────────────────────

    async def recall(
        self,
        query: str,
        k: int = 5,
        area: str | None = None,
        threshold: float = 0.5,
    ) -> list[tuple[KnowledgeNode, float]]:
        """FAISS similarity search + graph expansion, scored temporally.

        Returns list of (KnowledgeNode, composite_score) sorted descending.
        """
        area_filter = f"area == '{area}'" if area else ""
        docs = await self.memory.search_similarity_threshold(
            query, limit=k * 2, threshold=threshold, filter=area_filter
        )

        # Build nodes with similarity scores
        nodes_with_sim: list[tuple[KnowledgeNode, float]] = []
        seen_ids: set[str] = set()

        for doc in docs:
            doc_id = doc.metadata.get("id", "")
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            node = self.graph.get_node(doc_id)
            if node is None:
                # Node exists in FAISS but not in graph — create a stub
                now = _utcnow()
                node = KnowledgeNode(
                    id=doc_id,
                    content=doc.page_content,
                    memory_area=doc.metadata.get("area", "main"),
                    created_at=now,
                    last_accessed=now,
                    metadata=doc.metadata,
                )
            else:
                # Boost activation on recall
                self.graph.update_activation(doc_id)

            # Use relevance_score if available from FAISS, default 0.7
            sim = doc.metadata.get("relevance_score", 0.7)
            nodes_with_sim.append((node, sim))

        # Graph expansion: add related nodes from the graph
        for node, _sim in list(nodes_with_sim):
            related = self.graph.get_related(node.id)
            for rel in related:
                if rel.id not in seen_ids:
                    seen_ids.add(rel.id)
                    # Related nodes get a lower base similarity
                    nodes_with_sim.append((rel, 0.4))

        # Temporal ranking
        ranked = rank_nodes(nodes_with_sim, weights=self.weights)
        return ranked[:k]

    # ── connect ──────────────────────────────────────────────────────

    def connect(
        self,
        node_id_1: str,
        node_id_2: str,
        relation: str,
        weight: float = 1.0,
    ) -> None:
        """Create a directed edge between two nodes."""
        edge = KnowledgeEdge(
            source_id=node_id_1,
            target_id=node_id_2,
            relation=relation,
            weight=weight,
            created_at=_utcnow(),
        )
        self.graph.add_edge(edge)

    # ── get_context ──────────────────────────────────────────────────

    async def get_context(
        self,
        query: str,
        k: int = 10,
        area: str | None = None,
        threshold: float = 0.3,
    ) -> list[tuple[KnowledgeNode, float]]:
        """Combined FAISS similarity + graph context subgraph retrieval.

        Merges vector-search results with graph-based context subgraph,
        applies temporal scoring, and returns the top k results.
        """
        # Vector search results
        recalled = await self.recall(query, k=k, area=area, threshold=threshold)
        seen_ids = {node.id for node, _ in recalled}

        # Graph-based subgraph
        graph_nodes = self.graph.get_context_subgraph(query, k=k)
        combined = list(recalled)

        for gn in graph_nodes:
            if gn.id not in seen_ids:
                seen_ids.add(gn.id)
                composite = score(gn, similarity=0.3, weights=self.weights)
                combined.append((gn, composite))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:k]

    # ── utility ──────────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.graph.get_node(node_id)

    def apply_decay(self, decay_rate: float = 0.95) -> int:
        return self.graph.apply_decay(decay_rate)
