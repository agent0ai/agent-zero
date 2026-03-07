"""
SQLite-backed knowledge graph layer for relationship tracking,
activation/decay, and graph-based querying on top of FAISS memory.
"""

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class KnowledgeNode:
    id: str
    content: str
    memory_area: str  # "main", "fragments", "solutions", "instruments"
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    activation_score: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source_id: str
    target_id: str
    relation: str  # "depends_on", "contradicts", "refines", "supports", "derived_from"
    weight: float = 1.0
    created_at: datetime = field(default_factory=_utcnow)


VALID_RELATIONS = frozenset({"depends_on", "contradicts", "refines", "supports", "derived_from"})


class KnowledgeGraph:
    """SQLite-backed knowledge graph with activation/decay mechanics."""

    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_area TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    activation_score REAL NOT NULL DEFAULT 1.0,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id, relation),
                    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
                CREATE INDEX IF NOT EXISTS idx_nodes_area ON nodes(memory_area);
                CREATE INDEX IF NOT EXISTS idx_nodes_activation ON nodes(activation_score);
                """
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _dt_to_str(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    @staticmethod
    def _str_to_dt(s: str) -> datetime:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _row_to_node(self, row: sqlite3.Row) -> KnowledgeNode:
        return KnowledgeNode(
            id=row["id"],
            content=row["content"],
            memory_area=row["memory_area"],
            created_at=self._str_to_dt(row["created_at"]),
            last_accessed=self._str_to_dt(row["last_accessed"]),
            access_count=row["access_count"],
            activation_score=row["activation_score"],
            metadata=json.loads(row["metadata"]),
        )

    # ── Node operations ─────────────────────────────────────────────

    def add_node(self, node: KnowledgeNode) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO nodes
                   (id, content, memory_area, created_at, last_accessed,
                    access_count, activation_score, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node.id,
                    node.content,
                    node.memory_area,
                    self._dt_to_str(node.created_at),
                    self._dt_to_str(node.last_accessed),
                    node.access_count,
                    node.activation_score,
                    json.dumps(node.metadata),
                ),
            )
            self._conn.commit()

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_node(row)

    def delete_node(self, node_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def update_activation(self, node_id: str) -> None:
        now = self._dt_to_str(_utcnow())
        with self._lock:
            self._conn.execute(
                """UPDATE nodes
                   SET last_accessed = ?,
                       access_count = access_count + 1,
                       activation_score = MIN(activation_score + 0.1, 2.0)
                   WHERE id = ?""",
                (now, node_id),
            )
            self._conn.commit()

    # ── Edge operations ──────────────────────────────────────────────

    def add_edge(self, edge: KnowledgeEdge) -> None:
        if edge.relation not in VALID_RELATIONS:
            raise ValueError(f"Invalid relation '{edge.relation}'. Must be one of {VALID_RELATIONS}")
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO edges
                   (source_id, target_id, relation, weight, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    edge.source_id,
                    edge.target_id,
                    edge.relation,
                    edge.weight,
                    self._dt_to_str(edge.created_at),
                ),
            )
            self._conn.commit()

    def get_related(self, node_id: str, relation: Optional[str] = None) -> list[KnowledgeNode]:
        with self._lock:
            if relation is not None:
                rows = self._conn.execute(
                    """SELECT n.* FROM nodes n
                       JOIN edges e ON (e.target_id = n.id OR e.source_id = n.id)
                       WHERE (e.source_id = ? OR e.target_id = ?)
                         AND e.relation = ?
                         AND n.id != ?""",
                    (node_id, node_id, relation, node_id),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """SELECT n.* FROM nodes n
                       JOIN edges e ON (e.target_id = n.id OR e.source_id = n.id)
                       WHERE (e.source_id = ? OR e.target_id = ?)
                         AND n.id != ?""",
                    (node_id, node_id, node_id),
                ).fetchall()
        return [self._row_to_node(r) for r in rows]

    def get_edges_for_node(self, node_id: str) -> list[KnowledgeEdge]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM edges WHERE source_id = ? OR target_id = ?",
                (node_id, node_id),
            ).fetchall()
        return [
            KnowledgeEdge(
                source_id=r["source_id"],
                target_id=r["target_id"],
                relation=r["relation"],
                weight=r["weight"],
                created_at=self._str_to_dt(r["created_at"]),
            )
            for r in rows
        ]

    # ── Graph queries ────────────────────────────────────────────────

    def traverse(self, start_id: str, max_depth: int = 3) -> list[KnowledgeNode]:
        """BFS traversal from start_id up to max_depth hops."""
        visited: set[str] = set()
        result: list[KnowledgeNode] = []
        queue: list[tuple[str, int]] = [(start_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)

            node = self.get_node(current_id)
            if node is None:
                continue
            if current_id != start_id:
                result.append(node)

            if depth < max_depth:
                related = self.get_related(current_id)
                for rel_node in related:
                    if rel_node.id not in visited:
                        queue.append((rel_node.id, depth + 1))

        return result

    def find_contradictions(
        self,
        content: str,  # — reserved for future embedding-based matching
    ) -> list[tuple[KnowledgeNode, KnowledgeNode]]:
        """Return all pairs connected by a 'contradicts' edge."""
        with self._lock:
            rows = self._conn.execute(
                """SELECT e.source_id, e.target_id FROM edges e
                   WHERE e.relation = 'contradicts'"""
            ).fetchall()

        pairs: list[tuple[KnowledgeNode, KnowledgeNode]] = []
        for r in rows:
            src = self.get_node(r["source_id"])
            tgt = self.get_node(r["target_id"])
            if src is not None and tgt is not None:
                pairs.append((src, tgt))
        return pairs

    def get_context_subgraph(self, query: str, k: int = 10) -> list[KnowledgeNode]:
        """Return up to k nodes whose content matches query (simple LIKE),
        plus their immediate neighbours, ranked by activation_score."""
        like_pattern = f"%{query}%"
        with self._lock:
            rows = self._conn.execute(
                """SELECT * FROM nodes
                   WHERE content LIKE ?
                   ORDER BY activation_score DESC
                   LIMIT ?""",
                (like_pattern, k),
            ).fetchall()

        seed_nodes = [self._row_to_node(r) for r in rows]
        seen_ids: set[str] = {n.id for n in seed_nodes}
        expanded: list[KnowledgeNode] = list(seed_nodes)

        for node in seed_nodes:
            for neighbour in self.get_related(node.id):
                if neighbour.id not in seen_ids:
                    seen_ids.add(neighbour.id)
                    expanded.append(neighbour)

        # Sort by activation and trim to k
        expanded.sort(key=lambda n: n.activation_score, reverse=True)
        return expanded[:k]

    # ── Activation / decay ───────────────────────────────────────────

    def apply_decay(self, decay_rate: float = 0.95) -> int:
        """Multiply all activation scores by decay_rate. Returns count updated."""
        with self._lock:
            cur = self._conn.execute(
                "UPDATE nodes SET activation_score = activation_score * ?",
                (decay_rate,),
            )
            self._conn.commit()
            return cur.rowcount

    def boost_activation(self, node_id: str, amount: float = 0.1) -> None:
        with self._lock:
            self._conn.execute(
                """UPDATE nodes
                   SET activation_score = MIN(activation_score + ?, 2.0)
                   WHERE id = ?""",
                (amount, node_id),
            )
            self._conn.commit()

    # ── Bulk / utility ───────────────────────────────────────────────

    def node_count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM nodes").fetchone()
        return row["c"] if row else 0

    def edge_count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM edges").fetchone()
        return row["c"] if row else 0
