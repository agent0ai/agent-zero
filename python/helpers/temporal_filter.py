"""
Time-aware retrieval scoring that combines FAISS similarity with
recency, access frequency, and activation score.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from python.helpers.knowledge_graph import KnowledgeNode


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ScoringWeights:
    """Configurable weights for the composite score."""

    similarity_weight: float = 0.5
    recency_weight: float = 0.2
    frequency_weight: float = 0.1
    activation_weight: float = 0.2

    def __post_init__(self) -> None:
        total = self.similarity_weight + self.recency_weight + self.frequency_weight + self.activation_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")


def recency_score(
    node: KnowledgeNode,
    current_time: datetime | None = None,
    half_life_hours: float = 168.0,
) -> float:
    """Exponential decay based on hours since last access.

    half_life_hours controls how quickly recency fades (default 1 week).
    Returns a value in (0, 1].
    """
    now = current_time or _utcnow()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    last = node.last_accessed
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    elapsed_hours = max((now - last).total_seconds() / 3600.0, 0.0)
    # Exponential decay: 0.5^(elapsed / half_life)
    return 0.5 ** (elapsed_hours / half_life_hours)


def frequency_score(node: KnowledgeNode, max_count: int = 100) -> float:
    """Logarithmic scaling of access count, normalised to [0, 1]."""
    import math

    if node.access_count <= 0:
        return 0.0
    # log(1 + count) / log(1 + max_count)
    return min(math.log1p(node.access_count) / math.log1p(max_count), 1.0)


def activation_score(node: KnowledgeNode, max_activation: float = 2.0) -> float:
    """Normalise activation_score to [0, 1]."""
    return min(max(node.activation_score / max_activation, 0.0), 1.0)


def score(
    node: KnowledgeNode,
    similarity: float,
    current_time: datetime | None = None,
    weights: ScoringWeights | None = None,
    half_life_hours: float = 168.0,
    max_access_count: int = 100,
    max_activation: float = 2.0,
) -> float:
    """Compute a composite score combining similarity, recency, frequency,
    and activation.

    Args:
        node: The knowledge node being scored.
        similarity: FAISS cosine similarity in [0, 1].
        current_time: Reference time (defaults to now UTC).
        weights: Scoring weights (defaults to ScoringWeights()).
        half_life_hours: Half-life for recency decay.
        max_access_count: Cap for frequency normalisation.
        max_activation: Cap for activation normalisation.

    Returns:
        Composite score in [0, 1].
    """
    w = weights or ScoringWeights()
    now = current_time or _utcnow()

    r = recency_score(node, now, half_life_hours)
    f = frequency_score(node, max_access_count)
    a = activation_score(node, max_activation)
    s = max(min(similarity, 1.0), 0.0)

    return w.similarity_weight * s + w.recency_weight * r + w.frequency_weight * f + w.activation_weight * a


def rank_nodes(
    nodes_with_similarity: list[tuple[KnowledgeNode, float]],
    current_time: datetime | None = None,
    weights: ScoringWeights | None = None,
    **kwargs,
) -> list[tuple[KnowledgeNode, float]]:
    """Sort a list of (node, similarity) pairs by composite score descending.

    Returns list of (node, composite_score).
    """
    scored = [
        (node, score(node, sim, current_time=current_time, weights=weights, **kwargs))
        for node, sim in nodes_with_similarity
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
