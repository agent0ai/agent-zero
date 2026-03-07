"""Tests for KnowledgeGraph CRUD, traversal, activation/decay."""

import pytest

from python.helpers.knowledge_graph import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
    _utcnow,
)


def _make_node(node_id: str, content: str = "test", area: str = "main") -> KnowledgeNode:
    now = _utcnow()
    return KnowledgeNode(
        id=node_id,
        content=content,
        memory_area=area,
        created_at=now,
        last_accessed=now,
    )


@pytest.mark.unit
class TestKnowledgeGraphNodes:
    def test_add_and_get_node(self):
        kg = KnowledgeGraph(":memory:")
        node = _make_node("n1", "hello world")
        kg.add_node(node)
        fetched = kg.get_node("n1")
        assert fetched is not None
        assert fetched.id == "n1"
        assert fetched.content == "hello world"
        kg.close()

    def test_get_nonexistent_node_returns_none(self):
        kg = KnowledgeGraph(":memory:")
        assert kg.get_node("missing") is None
        kg.close()

    def test_delete_node(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1"))
        assert kg.delete_node("n1") is True
        assert kg.get_node("n1") is None
        kg.close()

    def test_delete_nonexistent_returns_false(self):
        kg = KnowledgeGraph(":memory:")
        assert kg.delete_node("nope") is False
        kg.close()

    def test_node_count(self):
        kg = KnowledgeGraph(":memory:")
        assert kg.node_count() == 0
        kg.add_node(_make_node("a"))
        kg.add_node(_make_node("b"))
        assert kg.node_count() == 2
        kg.close()

    def test_update_activation(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1"))
        kg.update_activation("n1")
        node = kg.get_node("n1")
        assert node is not None
        assert node.access_count == 1
        assert node.activation_score == pytest.approx(1.1)
        kg.close()


@pytest.mark.unit
class TestKnowledgeGraphEdges:
    def test_add_and_get_edges(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("a"))
        kg.add_node(_make_node("b"))
        edge = KnowledgeEdge(source_id="a", target_id="b", relation="supports")
        kg.add_edge(edge)
        edges = kg.get_edges_for_node("a")
        assert len(edges) == 1
        assert edges[0].relation == "supports"
        kg.close()

    def test_invalid_relation_raises(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("a"))
        kg.add_node(_make_node("b"))
        with pytest.raises(ValueError, match="Invalid relation"):
            kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="invalid"))
        kg.close()

    def test_edge_count(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("a"))
        kg.add_node(_make_node("b"))
        assert kg.edge_count() == 0
        kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="supports"))
        assert kg.edge_count() == 1
        kg.close()

    def test_get_related(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("a"))
        kg.add_node(_make_node("b"))
        kg.add_node(_make_node("c"))
        kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="supports"))
        kg.add_edge(KnowledgeEdge(source_id="a", target_id="c", relation="contradicts"))
        related_all = kg.get_related("a")
        assert len(related_all) == 2
        related_supports = kg.get_related("a", relation="supports")
        assert len(related_supports) == 1
        assert related_supports[0].id == "b"
        kg.close()


@pytest.mark.unit
class TestKnowledgeGraphTraversalAndDecay:
    def test_traverse_bfs(self):
        kg = KnowledgeGraph(":memory:")
        for nid in ("a", "b", "c", "d"):
            kg.add_node(_make_node(nid))
        kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="supports"))
        kg.add_edge(KnowledgeEdge(source_id="b", target_id="c", relation="supports"))
        kg.add_edge(KnowledgeEdge(source_id="c", target_id="d", relation="supports"))

        result = kg.traverse("a", max_depth=2)
        ids = {n.id for n in result}
        assert "b" in ids
        assert "c" in ids
        # d is at depth 3, should not appear with max_depth=2
        assert "d" not in ids
        kg.close()

    def test_apply_decay(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1"))
        count = kg.apply_decay(0.5)
        assert count == 1
        node = kg.get_node("n1")
        assert node is not None
        assert node.activation_score == pytest.approx(0.5)
        kg.close()

    def test_boost_activation(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1"))
        kg.boost_activation("n1", 0.3)
        node = kg.get_node("n1")
        assert node is not None
        assert node.activation_score == pytest.approx(1.3)
        kg.close()

    def test_boost_activation_capped_at_2(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1"))
        kg.boost_activation("n1", 5.0)
        node = kg.get_node("n1")
        assert node is not None
        assert node.activation_score == pytest.approx(2.0)
        kg.close()

    def test_get_context_subgraph(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("n1", "python programming"))
        kg.add_node(_make_node("n2", "java programming"))
        kg.add_node(_make_node("n3", "cooking recipes"))
        result = kg.get_context_subgraph("python", k=5)
        assert len(result) >= 1
        assert any(n.id == "n1" for n in result)
        kg.close()

    def test_find_contradictions(self):
        kg = KnowledgeGraph(":memory:")
        kg.add_node(_make_node("a", "earth is flat"))
        kg.add_node(_make_node("b", "earth is round"))
        kg.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="contradicts"))
        pairs = kg.find_contradictions("")
        assert len(pairs) == 1
        assert pairs[0][0].id == "a"
        assert pairs[0][1].id == "b"
        kg.close()
