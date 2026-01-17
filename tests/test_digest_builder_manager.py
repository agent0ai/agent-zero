import os

from instruments.custom.digest_builder.digest_builder_manager import DigestBuilderManager
from instruments.custom.knowledge_ingest.knowledge_ingest_db import KnowledgeIngestDatabase


def test_digest_builder_creates_summary(tmp_path):
    db_path = os.path.join(tmp_path, "knowledge_ingest.db")
    db = KnowledgeIngestDatabase(db_path)
    source_id = db.add_source(
        name="Test Source",
        source_type="rss",
        uri="https://example.com/rss",
        tags=["tech"],
        cadence="daily",
    )

    db.add_item(
        source_id=source_id,
        title="AI platform update",
        url="https://example.com/ai",
        published_at="2024-01-01",
        content="New AI infrastructure release",
        content_hash="hash1",
        tags=["tech"],
        confidence=0.9,
    )

    manager = DigestBuilderManager(db_path)
    result = manager.build_digest(window_hours=24)

    assert result["status"] == "ok"
    assert "Digest" in result["summary"]
    digests = manager.list_digests(limit=1)
    assert len(digests["digests"]) == 1
