import os

from instruments.custom.knowledge_ingest.knowledge_ingest_db import KnowledgeIngestDatabase


def test_knowledge_ingest_db_roundtrip(tmp_path):
    db_path = os.path.join(tmp_path, "knowledge_ingest.db")
    db = KnowledgeIngestDatabase(db_path)

    source_id = db.add_source(
        name="Test RSS",
        source_type="rss",
        uri="https://example.com/rss.xml",
        tags=["architecture"],
        cadence="daily",
    )

    assert source_id
    sources = db.list_sources()
    assert len(sources) == 1
    assert sources[0]["name"] == "Test RSS"

    inserted = db.add_item(
        source_id=source_id,
        title="Title",
        url="https://example.com/item",
        published_at="2024-01-01",
        content="Content",
        content_hash="abcd1234",
        tags=["architecture"],
        confidence=0.8,
    )

    assert inserted is True
    items = db.list_items(since_hours=24)
    assert len(items) == 1
    assert items[0]["title"] == "Title"

    digest_id = db.add_digest(
        window_start="2024-01-01T00:00:00",
        window_end="2024-01-01T01:00:00",
        summary="Summary",
        channels=["telegram"],
    )

    assert digest_id
    digests = db.list_digests(limit=5)
    assert len(digests) == 1
    assert digests[0]["summary"] == "Summary"
